from __future__ import annotations

import json
from typing import Any

import click

from osint.cli.setup_wizard import run_setup_wizard
from osint.utils.config_manager import ConfigManager


def _mask_api_keys(config: dict[str, Any]) -> dict[str, Any]:
    masked = json.loads(json.dumps(config))
    api_keys = masked.get("api_keys") or {}
    for k, v in list(api_keys.items()):
        api_keys[k] = "***" if v else ""
    masked["api_keys"] = api_keys
    return masked


@click.group(invoke_without_command=True)
@click.option(
    "--skip-setup",
    is_flag=True,
    default=False,
    help="Run without launching the interactive setup wizard.",
)
@click.pass_context
def cli(ctx: click.Context, skip_setup: bool) -> None:
    if ctx.resilient_parsing:
        return

    config_manager = ConfigManager.default()
    config = config_manager.load()

    ctx.obj = {
        "config_manager": config_manager,
        "config": config,
        "skip_setup": skip_setup,
    }

    if (
        not skip_setup
        and not config.get("setup_complete")
        and ctx.invoked_subcommand not in {"setup", "config"}
    ):
        run_setup_wizard(config_manager)
        ctx.obj["config"] = config_manager.load()

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command("setup")
@click.pass_context
def setup_cmd(ctx: click.Context) -> None:
    """Run the interactive setup wizard."""
    cm: ConfigManager = ctx.obj["config_manager"]
    run_setup_wizard(cm)


@cli.command("config")
@click.option("--show", is_flag=True, help="Show the current configuration.")
@click.option("--reset", is_flag=True, help="Reset configuration to defaults.")
@click.pass_context
def config_cmd(ctx: click.Context, show: bool, reset: bool) -> None:
    """View or update configuration."""
    cm: ConfigManager = ctx.obj["config_manager"]

    if reset:
        click.echo(f"Resetting configuration at: {cm.path}")
        if click.confirm("Continue?", default=False):
            cm.reset()
            click.echo("Configuration reset.")
        return

    if show:
        cfg = cm.load()
        click.echo(json.dumps(_mask_api_keys(cfg), indent=2, sort_keys=True))
        return

    run_setup_wizard(cm)
