from __future__ import annotations

import csv
import json
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import click

from osint.core.aggregator import Aggregator
from osint.core.datasource import normalize_list
from osint.core.models import QueryResult, QueryStatus
from osint.utils.config import resolve_results_dir
from osint.utils.config_manager import read_config


def _utc_ts() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_csv(path: Path, results: list[QueryResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "username",
                "platform_name",
                "profile_url",
                "status",
                "response_time",
                "metadata",
            ],
        )
        writer.writeheader()
        for r in results:
            writer.writerow(
                {
                    "username": r.username,
                    "platform_name": r.platform_name,
                    "profile_url": r.profile_url or "",
                    "status": r.status.value,
                    "response_time": r.response_time if r.response_time is not None else "",
                    "metadata": json.dumps(r.metadata, sort_keys=True),
                }
            )


def _resolve_output_paths(
    *,
    export: str,
    output: Path | None,
    results_dir: Path,
) -> dict[str, Path]:
    ts = _utc_ts()

    if output is None:
        base = results_dir / f"sherlock_search_{ts}"
    else:
        base = output

    paths: dict[str, Path] = {}

    if export in {"json", "both"}:
        json_path = base
        if json_path.suffix.lower() != ".json":
            json_path = json_path.with_suffix(".json")
        paths["json"] = json_path

    if export in {"csv", "both"}:
        csv_path = base
        if csv_path.suffix.lower() != ".csv":
            csv_path = csv_path.with_suffix(".csv")
        paths["csv"] = csv_path

    return paths


def _human_summary(results: list[QueryResult]) -> str:
    found = [r for r in results if r.status == QueryStatus.FOUND]
    errors = [r for r in results if r.status == QueryStatus.ERROR]

    lines: list[str] = []
    lines.append(f"Total results: {len(results)}")
    lines.append(f"Found: {len(found)}")
    lines.append(f"Errors: {len(errors)}")

    if found:
        lines.append("")
        lines.append("Found profiles:")
        for r in found:
            lines.append(f"  - {r.username} @ {r.platform_name}: {r.profile_url}")

    if errors:
        lines.append("")
        lines.append("Errors:")
        for r in errors[:10]:
            err = r.metadata.get("error") if isinstance(r.metadata, dict) else None
            lines.append(f"  - {r.username} @ {r.platform_name}: {err or 'error'}")

        if len(errors) > 10:
            lines.append(f"  ... and {len(errors) - 10} more")

    return "\n".join(lines)


@click.command("search")
@click.option(
    "--username",
    "-u",
    multiple=True,
    required=True,
    help="Username(s) to search. Can be repeated or comma-separated.",
)
@click.option(
    "--source",
    type=click.Choice(["all", "sherlock"], case_sensitive=False),
    default="all",
    show_default=True,
    help="Source to use.",
)
@click.option("--category", type=str, default=None, help="Filter by site category/tag.")
@click.option("--sites", type=str, default=None, help="Comma-separated list of specific sites.")
@click.option("--timeout", type=float, default=None, help="Request timeout in seconds.")
@click.option(
    "--threads",
    type=int,
    default=None,
    help="Number of concurrent threads (max: 100).",
)
@click.option(
    "--export",
    type=click.Choice(["json", "csv", "both"], case_sensitive=False),
    default=None,
    help="Export format.",
)
@click.option(
    "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Output file path (extension optional).",
)
@click.option("--browser", is_flag=True, default=False, help="Open found profiles in browser.")
@click.option("--no-nsfw", is_flag=True, default=False, help="Exclude NSFW sites from search.")
def search(
    username: tuple[str, ...],
    source: str,
    category: str | None,
    sites: str | None,
    timeout: float | None,
    threads: int | None,
    export: str | None,
    output: Path | None,
    browser: bool,
    no_nsfw: bool,
) -> None:
    config = read_config()

    usernames = normalize_list(username)
    if not usernames:
        raise click.ClickException("At least one --username is required")

    sites_list = normalize_list(sites)

    export = (export or str(config.get("output_format") or "json")).lower()
    if export not in {"json", "csv", "both"}:
        export = "json"

    results_dir = resolve_results_dir(str(config.get("results_path") or "./results"))

    if source.lower() == "all" and not bool(config.get("sherlock_enabled")):
        click.echo(
            "Warning: Sherlock is not enabled in your config. Running Sherlock anyway. "
            "Run 'osint setup' to enable it permanently.",
            err=True,
        )

    agg = Aggregator(config)

    progress_total = None
    progress_bar = None

    def progress_callback(done: int, total: int) -> None:
        nonlocal progress_total, progress_bar

        if progress_bar is None:
            progress_total = total
            progress_bar = click.progressbar(length=total, label="Searching")
            progress_bar.__enter__()

        if progress_total and total != progress_total:
            progress_total = total

        if progress_bar is not None:
            progress_bar.update(1)

    try:
        try:
            result = agg.search_usernames(
                usernames,
                sources=[source],
                category=category,
                sites=sites_list or None,
                timeout=timeout,
                threads=threads,
                no_nsfw=no_nsfw,
                progress_callback=progress_callback,
            )
        finally:
            if progress_bar is not None:
                progress_bar.__exit__(None, None, None)
    except Exception as e:
        try:
            from osint.sources.sherlock_source import SherlockUnavailableError

            if isinstance(e, SherlockUnavailableError):
                raise click.ClickException(str(e)) from e
        except Exception:
            pass

        if isinstance(e, ValueError):
            raise click.ClickException(str(e)) from e

        raise

    results = result.results

    click.echo(_human_summary(results))

    output_paths = _resolve_output_paths(export=export, output=output, results_dir=results_dir)

    payload = {
        "source": "sherlock",
        "usernames": usernames,
        "category": category,
        "sites": sites_list or None,
        "no_nsfw": no_nsfw,
        "results": [r.to_dict() for r in results],
        "stats": {
            "total": result.stats.total,
            "found": result.stats.found,
            "not_found": result.stats.not_found,
            "error": result.stats.error,
        },
    }

    if "json" in output_paths:
        _write_json(output_paths["json"], payload)
        click.echo(f"Saved JSON results to: {output_paths['json']}")

    if "csv" in output_paths:
        _write_csv(output_paths["csv"], results)
        click.echo(f"Saved CSV results to: {output_paths['csv']}")

    if browser:
        for r in results:
            if r.status == QueryStatus.FOUND and r.profile_url:
                webbrowser.open(r.profile_url)
