from __future__ import annotations

from concurrent.futures import Future
from dataclasses import dataclass
from typing import Any

import pytest

from osint.core.models import QueryStatus
from osint.sources.sherlock_source import SherlockSource


@dataclass
class _Elapsed:
    seconds: float

    def total_seconds(self) -> float:
        return self.seconds


@dataclass
class _Response:
    status_code: int
    text: str
    url: str
    elapsed: _Elapsed
    headers: dict[str, str] | None = None


class _FakeSession:
    def __init__(self, responses_by_url: dict[str, list[Any]]) -> None:
        self.responses_by_url = {k: list(v) for k, v in responses_by_url.items()}
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> Future[Any]:
        self.calls.append((method, url, kwargs))
        fut: Future[Any] = Future()

        queue = self.responses_by_url.get(url)
        if not queue:
            fut.set_exception(RuntimeError(f"No stubbed response for {url}"))
            return fut

        item = queue.pop(0)
        if isinstance(item, Exception):
            fut.set_exception(item)
        else:
            fut.set_result(item)
        return fut

    def close(self) -> None:
        return


@pytest.fixture
def site_data() -> dict[str, Any]:
    return {
        "GitHub": {
            "url": "https://github.com/{username}",
            "errorType": "status_code",
            "errorCode": 404,
            "tags": ["social-media"],
        },
        "ExampleForum": {
            "url": "https://forum.example/u/{username}",
            "errorType": "message",
            "errorMsg": "User not found",
            "tags": ["forums"],
            "isNSFW": True,
        },
    }


def test_sherlock_source_instantiation(site_data: dict[str, Any]) -> None:
    src = SherlockSource(site_data=site_data)
    assert "GitHub" in src.available_sites()
    assert "social-media" in src.available_categories()


def test_single_username_search(site_data: dict[str, Any]) -> None:
    responses = {
        "https://github.com/john": [_Response(200, "", "https://github.com/john", _Elapsed(0.1))],
        "https://forum.example/u/john": [
            _Response(200, "User not found", "https://forum.example/u/john", _Elapsed(0.2))
        ],
    }

    fake_session = _FakeSession(responses)

    src = SherlockSource(site_data=site_data, session_factory=lambda _: fake_session)
    results = src.search(["john"], no_nsfw=False)

    by_platform = {r.platform_name: r for r in results}
    assert by_platform["GitHub"].status == QueryStatus.FOUND
    assert by_platform["ExampleForum"].status == QueryStatus.NOT_FOUND


def test_multiple_username_search(site_data: dict[str, Any]) -> None:
    responses = {
        "https://github.com/john": [_Response(200, "", "https://github.com/john", _Elapsed(0.1))],
        "https://forum.example/u/john": [
            _Response(200, "User not found", "https://forum.example/u/john", _Elapsed(0.2))
        ],
        "https://github.com/jane": [_Response(404, "", "https://github.com/jane", _Elapsed(0.1))],
        "https://forum.example/u/jane": [
            _Response(200, "", "https://forum.example/u/jane", _Elapsed(0.2))
        ],
    }

    fake_session = _FakeSession(responses)

    src = SherlockSource(site_data=site_data, session_factory=lambda _: fake_session)
    results = src.search(["john", "jane"], no_nsfw=False)
    assert len(results) == 4


def test_site_filtering(site_data: dict[str, Any]) -> None:
    responses = {
        "https://github.com/john": [_Response(200, "", "https://github.com/john", _Elapsed(0.1))],
    }

    fake_session = _FakeSession(responses)

    src = SherlockSource(site_data=site_data, session_factory=lambda _: fake_session)
    results = src.search(["john"], sites=["GitHub"], no_nsfw=False)
    assert len(results) == 1
    assert results[0].platform_name == "GitHub"


def test_category_and_nsfw_filtering(site_data: dict[str, Any]) -> None:
    responses = {
        "https://github.com/john": [_Response(200, "", "https://github.com/john", _Elapsed(0.1))],
    }

    fake_session = _FakeSession(responses)

    src = SherlockSource(site_data=site_data, session_factory=lambda _: fake_session)
    results = src.search(["john"], category="social-media", no_nsfw=True)
    assert len(results) == 1
    assert results[0].platform_name == "GitHub"


def test_retry_on_exception(site_data: dict[str, Any]) -> None:
    responses = {
        "https://github.com/john": [
            TimeoutError("timed out"),
            _Response(200, "", "https://github.com/john", _Elapsed(0.1)),
        ]
    }

    fake_session = _FakeSession(responses)

    src = SherlockSource(
        {"sherlock": {"retries": 1}},
        site_data=site_data,
        session_factory=lambda _: fake_session,
        sleeper=lambda _: None,
    )
    results = src.search(["john"], sites=["GitHub"], no_nsfw=False)
    assert len(results) == 1
    assert results[0].status == QueryStatus.FOUND
    assert len(fake_session.calls) == 2
