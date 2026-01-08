import json
from pathlib import Path

import pytest

from osint.utils.config_manager import default_config, read_config, update_config, validate_email


def test_default_config_when_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "osint_config.json"
    monkeypatch.setenv("OSINT_CONFIG_PATH", str(config_path))

    cfg = read_config()
    assert cfg["setup_complete"] is False
    assert cfg["output_format"] == "json"


def test_write_and_read_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "osint_config.json"
    monkeypatch.setenv("OSINT_CONFIG_PATH", str(config_path))

    updated = update_config({"output_format": "csv", "setup_complete": True})
    assert updated["output_format"] == "csv"
    assert updated["setup_complete"] is True

    data = json.loads(config_path.read_text(encoding="utf-8"))
    assert data["output_format"] == "csv"

    loaded = read_config()
    assert loaded["output_format"] == "csv"


def test_results_path_created(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "osint_config.json"
    results_dir = tmp_path / "results"

    monkeypatch.setenv("OSINT_CONFIG_PATH", str(config_path))

    cfg = update_config({"results_path": str(results_dir), "setup_complete": True})
    assert Path(cfg["results_path"]).exists()


@pytest.mark.parametrize(
    "email,ok",
    [
        ("", True),
        ("a@b.com", True),
        ("invalid", False),
        ("a@b", False),
    ],
)
def test_email_validation(email: str, ok: bool) -> None:
    if ok:
        assert validate_email(email) == email
    else:
        with pytest.raises(ValueError):
            validate_email(email)


def test_default_config_shape() -> None:
    cfg = default_config()
    assert set(cfg["api_keys"].keys()) == {"twitter", "facebook", "linkedin", "instagram"}
