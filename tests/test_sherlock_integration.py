from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner

from osint.cli.main import cli
from osint.core.aggregator import AggregationResult, AggregationStats
from osint.core.models import QueryResult, QueryStatus
from osint.utils.config_manager import update_config


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def _fake_results() -> list[QueryResult]:
    return [
        QueryResult(
            username="john",
            platform_name="GitHub",
            profile_url="https://github.com/john",
            status=QueryStatus.FOUND,
            response_time=0.1,
            metadata={},
        ),
        QueryResult(
            username="john",
            platform_name="ExampleForum",
            profile_url="https://forum.example/u/john",
            status=QueryStatus.NOT_FOUND,
            response_time=0.2,
            metadata={},
        ),
    ]


def test_cli_search_exports_json(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "osint_config.json"
    monkeypatch.setenv("OSINT_CONFIG_PATH", str(config_path))

    update_config(
        {
            "setup_complete": True,
            "sherlock_enabled": True,
            "results_path": str(tmp_path / "results"),
        }
    )

    captured: dict[str, Any] = {}

    def fake_search(self: Any, usernames: list[str], **kwargs: Any) -> AggregationResult:
        captured.update(kwargs)
        results = _fake_results()
        stats = AggregationStats(total=len(results), found=1, not_found=1, error=0)
        return AggregationResult(results=results, stats=stats)

    monkeypatch.setattr("osint.cli.commands.Aggregator.search_usernames", fake_search)

    out_path = tmp_path / "out.json"
    result = runner.invoke(
        cli,
        ["search", "--username", "john", "--export", "json", "--output", str(out_path)],
    )

    assert result.exit_code == 0
    assert out_path.exists()
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["source"] == "sherlock"
    assert len(payload["results"]) == 2
    assert captured.get("sites") is None


def test_cli_search_exports_both_and_browser(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "osint_config.json"
    monkeypatch.setenv("OSINT_CONFIG_PATH", str(config_path))

    update_config(
        {
            "setup_complete": True,
            "sherlock_enabled": True,
            "results_path": str(tmp_path / "results"),
        }
    )

    def fake_search(self: Any, usernames: list[str], **kwargs: Any) -> AggregationResult:
        results = _fake_results()
        stats = AggregationStats(total=len(results), found=1, not_found=1, error=0)
        return AggregationResult(results=results, stats=stats)

    monkeypatch.setattr("osint.cli.commands.Aggregator.search_usernames", fake_search)

    opened: list[str] = []
    monkeypatch.setattr("osint.cli.commands.webbrowser.open", lambda url: opened.append(url))

    base_path = tmp_path / "out"
    result = runner.invoke(
        cli,
        [
            "search",
            "--username",
            "john",
            "--export",
            "both",
            "--output",
            str(base_path),
            "--browser",
        ],
    )

    assert result.exit_code == 0
    assert base_path.with_suffix(".json").exists()
    assert base_path.with_suffix(".csv").exists()
    assert opened == ["https://github.com/john"]
