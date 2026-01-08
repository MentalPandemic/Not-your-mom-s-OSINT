from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from osint.cli.app import cli


def test_first_run_triggers_setup_wizard_and_saves_config(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "osint_config.json"
    monkeypatch.setenv("OSINT_CONFIG_PATH", str(config_path))

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        user_input = "\n".join(
            [
                "3",  # output format
                "y",  # verbose
                "./out",  # results path
                "y",  # sherlock
                "y",  # configure api keys
                "tw_key",  # twitter
                "",  # facebook
                "li_key",  # linkedin
                "",  # instagram
                "n",  # auto updates
                "test@example.com",  # email
                "y",  # advanced
                "",
            ]
        )

        result = runner.invoke(cli, [], input=user_input)
        assert result.exit_code == 0, result.output
        assert "Welcome to Not-your-mom's-OSINT" in result.output

        assert config_path.exists()
        cfg = json.loads(config_path.read_text(encoding="utf-8"))
        assert cfg["setup_complete"] is True
        assert cfg["output_format"] == "both"
        assert cfg["verbose_logging"] is True
        assert cfg["sherlock_enabled"] is True
        assert cfg["auto_updates"] is False
        assert cfg["notification_email"] == "test@example.com"
        assert cfg["api_keys"]["twitter"] == "tw_key"
        assert cfg["api_keys"]["facebook"] == ""
        assert cfg["api_keys"]["linkedin"] == "li_key"
        assert cfg["api_keys"]["instagram"] == ""

        assert Path(cfg["results_path"]).exists()


def test_config_show_masks_api_keys(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "osint_config.json"
    monkeypatch.setenv("OSINT_CONFIG_PATH", str(config_path))

    config_path.write_text(
        json.dumps(
            {
                "output_format": "json",
                "verbose_logging": False,
                "results_path": "./results",
                "sherlock_enabled": True,
                "api_keys": {
                    "twitter": "secret",
                    "facebook": "",
                    "linkedin": "x",
                    "instagram": "",
                },
                "auto_updates": True,
                "notification_email": "",
                "advanced_features": False,
                "setup_complete": True,
            }
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["config", "--show"])
    assert result.exit_code == 0
    shown = json.loads(result.output)
    assert shown["api_keys"]["twitter"] == "***"
    assert shown["api_keys"]["linkedin"] == "***"
    assert shown["api_keys"]["facebook"] == ""


def test_rerunning_setup_updates_existing_config(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "osint_config.json"
    monkeypatch.setenv("OSINT_CONFIG_PATH", str(config_path))

    config_path.write_text(
        json.dumps(
            {
                "output_format": "json",
                "verbose_logging": True,
                "results_path": "./results",
                "sherlock_enabled": True,
                "api_keys": {"twitter": "", "facebook": "", "linkedin": "", "instagram": ""},
                "auto_updates": True,
                "notification_email": "old@example.com",
                "advanced_features": True,
                "setup_complete": True,
            }
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        user_input = "\n".join(
            [
                "2",  # output format
                "n",  # verbose
                "",  # results path default
                "n",  # sherlock
                "n",  # configure api keys
                "y",  # auto updates
                "",  # email skip
                "n",  # advanced
                "",
            ]
        )
        result = runner.invoke(cli, ["setup"], input=user_input)
        assert result.exit_code == 0, result.output

    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    assert cfg["output_format"] == "csv"
    assert cfg["verbose_logging"] is False
    assert cfg["notification_email"] == ""
    assert cfg["setup_complete"] is True


def test_skip_setup_does_not_launch_wizard(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "osint_config.json"
    monkeypatch.setenv("OSINT_CONFIG_PATH", str(config_path))

    runner = CliRunner()
    result = runner.invoke(cli, ["--skip-setup"], input="")
    assert result.exit_code == 0
    assert "Welcome to Not-your-mom's-OSINT" not in result.output
    assert "Usage:" in result.output


def test_invalid_inputs_are_rejected_and_reprompted(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "osint_config.json"
    monkeypatch.setenv("OSINT_CONFIG_PATH", str(config_path))

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        Path("badpath").write_text("not a directory", encoding="utf-8")

        user_input = "\n".join(
            [
                "1",  # output format
                "n",  # verbose
                "badpath",  # results path (invalid; it's a file)
                "./gooddir",  # results path (valid)
                "n",  # sherlock
                "n",  # configure api keys
                "y",  # auto updates
                "not-an-email",  # invalid email
                "user@example.com",  # valid email
                "n",  # advanced
                "",
            ]
        )

        result = runner.invoke(cli, ["setup"], input=user_input)
        assert result.exit_code == 0, result.output
        assert "Error: Unable to create results path" in result.output
        assert "Error: Invalid email format." in result.output
        cfg = json.loads(config_path.read_text(encoding="utf-8"))
        assert cfg["notification_email"] == "user@example.com"
        assert Path(cfg["results_path"]).exists()
