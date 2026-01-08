from __future__ import annotations

from pathlib import Path
from typing import Any

import click

from osint.utils.config_manager import ConfigManager, validate_email, validate_results_path

_OUTPUT_FORMAT_MENU = """What is your preferred output format?
(1) JSON
(2) CSV
(3) Both"""


def _prompt_output_format() -> str:
    click.echo(_OUTPUT_FORMAT_MENU)
    choice = click.prompt(
        "Enter choice [1/2/3]",
        type=click.Choice(["1", "2", "3"], case_sensitive=False),
        default="1",
        show_default=False,
    )
    return {"1": "json", "2": "csv", "3": "both"}[choice]


def _prompt_api_keys() -> dict[str, str]:
    api_keys: dict[str, str] = {}

    def prompt_key(label: str) -> str:
        return click.prompt(
            f"Enter {label} API key (Press Enter to skip)",
            default="",
            show_default=False,
            hide_input=True,
        ).strip()

    api_keys["twitter"] = prompt_key("Twitter/X")
    api_keys["facebook"] = prompt_key("Facebook")
    api_keys["linkedin"] = prompt_key("LinkedIn")
    api_keys["instagram"] = prompt_key("Instagram")

    return api_keys


def run_setup_wizard(config_manager: ConfigManager) -> dict[str, Any]:
    click.echo("Welcome to Not-your-mom's-OSINT!")
    click.echo(
        "This setup wizard will guide you through initial configuration for the OSINT platform."
    )
    click.echo()

    config = config_manager.load()

    config["output_format"] = _prompt_output_format()
    click.echo()

    config["verbose_logging"] = click.confirm(
        "Would you like to enable verbose logging?", default=False
    )

    click.echo("Please enter the path where results should be saved:")
    click.echo("(Default: ./results)")

    while True:
        try:
            raw_results_path = click.prompt(
                "Enter path",
                default=config.get("results_path") or "./results",
                show_default=True,
            )
            config["results_path"] = validate_results_path(raw_results_path)
            break
        except click.BadParameter as exc:
            click.echo(f"Error: {exc.message}")

    config["sherlock_enabled"] = click.confirm(
        "Do you want to integrate Sherlock for username enumeration?", default=False
    )

    if click.confirm("Would you like to configure social media API keys now?", default=False):
        entered = _prompt_api_keys()
        config.setdefault("api_keys", {})
        for k, v in entered.items():
            if v is not None:
                config["api_keys"][k] = v

    config["auto_updates"] = click.confirm(
        "Would you like to enable automatic updates for OSINT sources?", default=True
    )

    click.echo("Please enter your email address for notifications (optional):")
    click.echo("(Press Enter to skip)")

    while True:
        try:
            raw_email = click.prompt("Enter email", default="", show_default=False)
            config["notification_email"] = validate_email(raw_email)
            break
        except click.BadParameter as exc:
            click.echo(f"Error: {exc.message}")

    config["advanced_features"] = click.confirm(
        "Enable advanced correlation engine features?", default=False
    )

    config["setup_complete"] = True
    config_manager.save(config)

    click.echo()
    click.echo("Setup complete. Configuration saved.")
    click.echo(f"Config file: {config_manager.path}")
    click.echo()

    _print_summary(config)

    click.echo()
    click.echo("Next steps:")
    click.echo("  - Run `osint config --show` to review your configuration")
    click.echo("  - Re-run this wizard anytime with `osint setup`")

    return config


def _mask_secret(value: str) -> str:
    if not value:
        return ""
    return "***"


def _print_summary(config: dict[str, Any]) -> None:
    click.echo("Saved configuration summary:")
    click.echo(f"  output_format: {config.get('output_format')}")
    click.echo(f"  verbose_logging: {config.get('verbose_logging')}")
    click.echo(f"  results_path: {config.get('results_path')}")
    click.echo(f"  sherlock_enabled: {config.get('sherlock_enabled')}")
    click.echo(f"  auto_updates: {config.get('auto_updates')}")
    click.echo(f"  notification_email: {config.get('notification_email') or ''}")
    click.echo(f"  advanced_features: {config.get('advanced_features')}")

    api_keys = config.get("api_keys") or {}
    click.echo("  api_keys:")
    click.echo(f"    twitter: {_mask_secret(str(api_keys.get('twitter', '')))}")
    click.echo(f"    facebook: {_mask_secret(str(api_keys.get('facebook', '')))}")
    click.echo(f"    linkedin: {_mask_secret(str(api_keys.get('linkedin', '')))}")
    click.echo(f"    instagram: {_mask_secret(str(api_keys.get('instagram', '')))}")


def ensure_results_path_on_disk(config: dict[str, Any]) -> None:
    path = Path(str(config.get("results_path") or "./results")).expanduser()
    path.mkdir(parents=True, exist_ok=True)
