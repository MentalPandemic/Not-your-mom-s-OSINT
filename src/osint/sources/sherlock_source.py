from __future__ import annotations

import json
import random
import re
import time
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from osint.core.datasource import DataSource, ProgressCallback
from osint.core.models import QueryResult, QueryStatus


class SherlockUnavailableError(RuntimeError):
    pass


def _slug(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def _format_template(template: str, username: str) -> str:
    try:
        return template.format(username=username)
    except Exception:
        try:
            return template.format(username)
        except Exception:
            return template.replace("{}", username)


def _load_sherlock_site_data() -> dict[str, Any]:
    try:
        import importlib.resources

        try:
            import sherlock  # noqa: F401
        except ModuleNotFoundError:
            import sherlock_project  # noqa: F401

        candidates: list[tuple[str, str]] = [
            ("sherlock_project.resources", "data.json"),
            ("sherlock_project.resources", "sites.json"),
            ("sherlock_project", "sites.json"),
            ("sherlock_project", "resources/data.json"),
            ("sherlock_project", "resources/sites.json"),
            ("sherlock.resources", "data.json"),
            ("sherlock.resources", "sites.json"),
            ("sherlock", "sites.json"),
            ("sherlock", "resources/data.json"),
            ("sherlock", "resources/sites.json"),
        ]

        for pkg, resource in candidates:
            try:
                payload = importlib.resources.files(pkg).joinpath(resource).read_text(encoding="utf-8")
                data = json.loads(payload)
                if isinstance(data, dict) and data:
                    # Filter out non-dict entries like $schema
                    return {k: v for k, v in data.items() if isinstance(v, dict)}
            except Exception:
                continue

        raise SherlockUnavailableError(
            "Sherlock is installed, but the sites database could not be located."
        )
    except ModuleNotFoundError as e:
        raise SherlockUnavailableError(
            "Sherlock is not installed. Install the 'sherlock-project' dependency to enable "
            "username enumeration."
        ) from e


@dataclass(slots=True)
class _TaskContext:
    username: str
    site_name: str
    site: Mapping[str, Any]
    url: str
    attempt: int
    started: float


class _ThreadPoolSession:
    def __init__(self, max_workers: int) -> None:
        import requests

        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._session = requests.Session()

    def request(self, method: str, url: str, **kwargs: Any) -> Future[Any]:
        return self._executor.submit(self._session.request, method, url, **kwargs)

    def close(self) -> None:
        self._session.close()
        self._executor.shutdown(wait=True)


class SherlockSource(DataSource):
    name = "sherlock"

    def __init__(
        self,
        config: Mapping[str, Any] | None = None,
        *,
        site_data: Mapping[str, Any] | None = None,
        session_factory: Callable[[int], Any] | None = None,
        sleeper: Callable[[float], None] | None = None,
    ) -> None:
        cfg = dict(config or {})
        sherlock_cfg = cfg.get("sherlock") or {}

        self._site_data = dict(site_data) if site_data is not None else None
        self._timeout_default = float(sherlock_cfg.get("timeout", 10))
        self._threads_default = int(sherlock_cfg.get("threads", 10))
        self._retries_default = int(sherlock_cfg.get("retries", 3))
        self._no_nsfw_default = bool(sherlock_cfg.get("no_nsfw", False))

        self._session_factory = session_factory
        self._sleeper = sleeper or time.sleep

    def _ensure_site_data(self) -> dict[str, Any]:
        if self._site_data is None:
            self._site_data = _load_sherlock_site_data()
        return dict(self._site_data)

    def available_sites(self) -> list[str]:
        return sorted(self._ensure_site_data().keys())

    def available_categories(self) -> list[str]:
        categories: set[str] = set()
        for site in self._ensure_site_data().values():
            if not isinstance(site, dict):
                continue
            tags = site.get("tags") or []
            if isinstance(tags, str):
                tags = [tags]
            if isinstance(tags, list):
                categories.update({_slug(str(t)) for t in tags if str(t).strip()})

        return sorted(c for c in categories if c)

    def resolve_site_names(
        self,
        *,
        sites: Sequence[str] | None = None,
        category: str | None = None,
        no_nsfw: bool | None = None,
    ) -> list[str]:
        data = self._ensure_site_data()

        requested = {s.strip().lower() for s in (sites or []) if s.strip()}
        cat = _slug(category) if category else None
        cat_aliases: set[str] | None = None
        if cat:
            aliases: dict[str, set[str]] = {
                "social-media": {"social-media", "social", "social-network"},
                "forums": {"forums", "forum"},
                "blogs": {"blogs", "blog"},
            }
            cat_aliases = aliases.get(cat, {cat})

        out: list[str] = []
        for name, site in data.items():
            if not isinstance(site, dict):
                continue

            if requested and name.lower() not in requested:
                continue

            if no_nsfw is True and bool(site.get("isNSFW")):
                continue

            if cat_aliases:
                tags = site.get("tags") or []
                if isinstance(tags, str):
                    tags = [tags]
                tag_slugs = {_slug(str(t)) for t in tags}
                if not (tag_slugs & cat_aliases):
                    continue

            out.append(name)

        return sorted(out)

    def search(
        self,
        usernames: Sequence[str],
        *,
        sites: Sequence[str] | None = None,
        category: str | None = None,
        timeout: float | None = None,
        threads: int | None = None,
        no_nsfw: bool | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> list[QueryResult]:
        normalized_usernames = [u.strip() for u in usernames if str(u).strip()]
        if not normalized_usernames:
            return []

        timeout = float(timeout) if timeout is not None else self._timeout_default
        threads = int(threads) if threads is not None else self._threads_default
        threads = max(1, min(threads, 100))
        retries = max(0, self._retries_default)
        no_nsfw = self._no_nsfw_default if no_nsfw is None else bool(no_nsfw)

        data = self._ensure_site_data()

        selected_sites = self.resolve_site_names(sites=sites, category=category, no_nsfw=no_nsfw)
        total = len(selected_sites) * len(normalized_usernames)
        if total == 0:
            return []

        session = self._create_session(threads)

        in_flight: dict[Future[Any], _TaskContext] = {}
        results: list[QueryResult] = []
        completed = 0

        def submit(site_name: str, username: str, attempt: int) -> None:
            site = data[site_name]
            if not isinstance(site, dict):
                site = {}

            url_template = str(site.get("url") or "")
            url = _format_template(url_template, username)

            method = str(site.get("method") or "GET").upper()
            allow_redirects = bool(site.get("allow_redirects", True))
            headers = site.get("headers") or None

            kwargs: dict[str, Any] = {
                "timeout": timeout,
                "allow_redirects": allow_redirects,
            }
            if isinstance(headers, dict):
                kwargs["headers"] = {str(k): str(v) for k, v in headers.items()}

            post_body = site.get("post_body")
            if method != "GET" and post_body is not None:
                if isinstance(post_body, dict):
                    kwargs["data"] = post_body
                else:
                    kwargs["data"] = str(post_body)

            ctx = _TaskContext(
                username=username,
                site_name=site_name,
                site=site,
                url=url,
                attempt=attempt,
                started=time.monotonic(),
            )
            in_flight[session.request(method, url, **kwargs)] = ctx

        for site_name in selected_sites:
            for username in normalized_usernames:
                submit(site_name, username, attempt=1)

        try:
            while in_flight:
                done, _ = wait(in_flight.keys(), return_when=FIRST_COMPLETED)

                for future in done:
                    ctx = in_flight.pop(future)
                    ended = time.monotonic()
                    response_time = max(0.0, ended - ctx.started)

                    try:
                        resp = future.result()
                    except Exception as e:
                        if ctx.attempt <= retries:
                            self._backoff(ctx.attempt)
                            submit(ctx.site_name, ctx.username, attempt=ctx.attempt + 1)
                            continue

                        results.append(
                            QueryResult(
                                username=ctx.username,
                                platform_name=ctx.site_name,
                                profile_url=ctx.url,
                                status=QueryStatus.ERROR,
                                response_time=response_time,
                                metadata={"error": str(e), "attempt": ctx.attempt},
                            )
                        )
                        completed += 1
                        if progress_callback:
                            progress_callback(completed, total)
                        continue

                    status, meta = self._interpret_response(ctx, resp)

                    if status == QueryStatus.ERROR and meta.get("retriable") and ctx.attempt <= retries:
                        self._backoff(ctx.attempt)
                        submit(ctx.site_name, ctx.username, attempt=ctx.attempt + 1)
                        continue

                    results.append(
                        QueryResult(
                            username=ctx.username,
                            platform_name=ctx.site_name,
                            profile_url=ctx.url,
                            status=status,
                            response_time=self._extract_response_time(resp, response_time),
                            metadata=meta,
                        )
                    )
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, total)

        finally:
            close = getattr(session, "close", None)
            if callable(close):
                close()

        return results

    def _create_session(self, threads: int) -> Any:
        if self._session_factory is not None:
            return self._session_factory(threads)

        try:
            from requests_futures.sessions import FuturesSession

            return FuturesSession(max_workers=threads)
        except Exception:
            return _ThreadPoolSession(max_workers=threads)

    def _backoff(self, attempt: int) -> None:
        base = 0.35
        delay = base * (2 ** max(0, attempt - 1))
        delay = min(delay, 8.0)
        delay = delay + random.random() * 0.2
        self._sleeper(delay)

    def _extract_response_time(self, resp: Any, fallback: float) -> float:
        elapsed = getattr(resp, "elapsed", None)
        if elapsed is None:
            return fallback

        total_seconds = getattr(elapsed, "total_seconds", None)
        if callable(total_seconds):
            try:
                return float(total_seconds())
            except Exception:
                return fallback

        try:
            return float(elapsed)
        except Exception:
            return fallback

    def _interpret_response(self, ctx: _TaskContext, resp: Any) -> tuple[QueryStatus, dict[str, Any]]:
        status_code = int(getattr(resp, "status_code", 0) or 0)
        text = str(getattr(resp, "text", "") or "")
        final_url = str(getattr(resp, "url", "") or "")

        site = ctx.site
        error_type = str(site.get("errorType") or "")

        meta: dict[str, Any] = {
            "http_status": status_code,
            "error_type": error_type,
            "final_url": final_url,
            "is_nsfw": bool(site.get("isNSFW")),
        }

        tags = site.get("tags") or []
        if isinstance(tags, str):
            tags = [tags]
        if isinstance(tags, list):
            meta["tags"] = [str(t) for t in tags]

        if status_code in {429, 500, 502, 503, 520, 521, 522}:
            meta["retriable"] = True
            meta["error"] = "rate_limited" if status_code == 429 else "upstream_error"
            return (QueryStatus.ERROR, meta)

        if status_code == 403 and "cloudflare" in str(getattr(resp, "headers", {}) or {}).get("Server", "").lower():
            meta["error"] = "waf_detected"
            return (QueryStatus.ERROR, meta)

        if error_type == "status_code":
            codes = site.get("errorCode")
            if isinstance(codes, list):
                error_codes = {int(c) for c in codes}
            elif codes is None:
                error_codes = {404}
            else:
                error_codes = {int(codes)}

            if status_code in error_codes:
                return (QueryStatus.NOT_FOUND, meta)
            if status_code >= 400:
                meta["error"] = "http_error"
                return (QueryStatus.ERROR, meta)
            return (QueryStatus.FOUND, meta)

        if error_type == "message":
            error_msgs = [site.get("errorMsg"), site.get("errorMsg2")]
            error_msgs = [str(m) for m in error_msgs if m]
            if any(m in text for m in error_msgs):
                return (QueryStatus.NOT_FOUND, meta)

            if status_code == 404:
                return (QueryStatus.NOT_FOUND, meta)
            if status_code >= 400:
                meta["error"] = "http_error"
                return (QueryStatus.ERROR, meta)
            return (QueryStatus.FOUND, meta)

        if error_type == "response_url":
            if ctx.username.lower() not in final_url.lower():
                return (QueryStatus.NOT_FOUND, meta)

            if status_code >= 400:
                meta["error"] = "http_error"
                return (QueryStatus.ERROR, meta)
            return (QueryStatus.FOUND, meta)

        if status_code == 404:
            return (QueryStatus.NOT_FOUND, meta)

        if status_code >= 400:
            meta["error"] = "http_error"
            return (QueryStatus.ERROR, meta)

        if status_code in {200, 301, 302, 303, 307, 308}:
            return (QueryStatus.FOUND, meta)

        meta["error"] = "unexpected_http_status"
        return (QueryStatus.ERROR, meta)
