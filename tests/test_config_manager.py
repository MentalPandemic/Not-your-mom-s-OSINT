from __future__ import annotations

import json
from pathlib import Path

import click
import pytest

from osint.utils.config_manager import ConfigManager, validate_email, validate_results_path


def test_validate_email_accepts_empty() -> None:
    assert validate_email("") == ""


@pytest.mark.parametrize(
    "value",
    [
        "user@example.com",
        "user.name+tag@example.co.uk",
    ],
)
def test_validate_email_accepts_valid(value: str) -> None:
    assert validate_email(value) == value


@pytest.mark.parametrize("value", ["not-an-email", "user@", "@example.com", "user@example"])
def test_validate_email_rejects_invalid(value: str) -> None:
    with pytest.raises(click.BadParameter):
        validate_email(value)


def test_validate_results_path_creates_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    out = validate_results_path("./results")
    assert Path(out).exists()
    assert Path(out).is_dir()


def test_config_manager_creates_defaults_when_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "osint_config.json"
    monkeypatch.setenv("OSINT_CONFIG_PATH", str(config_path))

    cm = ConfigManager.default()
    cfg = cm.load()
    assert cfg["setup_complete"] is False

    cm.save({**cfg, "setup_complete": True})

    loaded = json.loads(config_path.read_text(encoding="utf-8"))
    assert loaded["setup_complete"] is True
