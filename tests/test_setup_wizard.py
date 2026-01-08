from pathlib import Path

import pytest
from click.testing import CliRunner

from osint.cli.main import cli


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_setup_wizard_complete(runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "osint_config.json"
    monkeypatch.setenv("OSINT_CONFIG_PATH", str(config_path))

    result = runner.invoke(
        cli,
        ["setup"],
        input="1\nn\n./results\nn\nn\nn\n\nn\n",
    )

    assert result.exit_code == 0
    assert "Setup Complete!" in result.output
    assert config_path.exists()


def test_config_show(runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "osint_config.json"
    monkeypatch.setenv("OSINT_CONFIG_PATH", str(config_path))

    runner.invoke(cli, ["setup"], input="1\nn\n./results\nn\nn\nn\n\nn\n")

    result = runner.invoke(cli, ["config", "--show"])
    assert result.exit_code == 0
    assert '"output_format"' in result.output


def test_config_reset(runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "osint_config.json"
    monkeypatch.setenv("OSINT_CONFIG_PATH", str(config_path))

    runner.invoke(cli, ["setup"], input="1\nn\n./results\nn\nn\nn\n\nn\n")

    result = runner.invoke(cli, ["config", "--reset"])
    assert result.exit_code == 0
    assert "Configuration file removed" in result.output


def test_skip_setup_flag(runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "osint_config.json"
    monkeypatch.setenv("OSINT_CONFIG_PATH", str(config_path))

    result = runner.invoke(cli, ["--skip-setup"])
    assert result.exit_code == 0
    assert "Setup Wizard" not in result.output


def test_first_run_auto_setup(runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "osint_config.json"
    monkeypatch.setenv("OSINT_CONFIG_PATH", str(config_path))

    result = runner.invoke(cli, input="1\nn\n./results\nn\nn\nn\n\nn\n")

    assert result.exit_code == 0
    assert "Setup Wizard" in result.output


def test_wizard_with_api_keys(runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "osint_config.json"
    monkeypatch.setenv("OSINT_CONFIG_PATH", str(config_path))

    result = runner.invoke(
        cli,
        ["setup"],
        input="1\nn\n./results\nn\ny\ntwitter_key\n\n\n\nn\n\nn\n",
    )

    assert result.exit_code == 0
    assert "Setup Complete!" in result.output


def test_wizard_with_email(runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "osint_config.json"
    monkeypatch.setenv("OSINT_CONFIG_PATH", str(config_path))

    result = runner.invoke(
        cli,
        ["setup"],
        input="1\nn\n./results\nn\nn\nn\nuser@example.com\nn\n",
    )

    assert result.exit_code == 0
    assert "user@example.com" in result.output


def test_wizard_with_invalid_email_then_skip(runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "osint_config.json"
    monkeypatch.setenv("OSINT_CONFIG_PATH", str(config_path))

    result = runner.invoke(
        cli,
        ["setup"],
        input="1\nn\n./results\nn\nn\nn\ninvalid\n\nn\n",
    )

    assert result.exit_code == 0
    assert "Invalid email address format" in result.output


def test_output_format_choices(runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "osint_config.json"
    monkeypatch.setenv("OSINT_CONFIG_PATH", str(config_path))

    result = runner.invoke(cli, ["setup"], input="2\nn\n./results\nn\nn\nn\n\nn\n")
    assert result.exit_code == 0
    assert "Setup Complete!" in result.output

    result = runner.invoke(cli, ["setup"], input="3\nn\n./results\nn\nn\nn\n\nn\n")
    assert result.exit_code == 0
