from __future__ import annotations

import json

import click

from osint.cli.setup_wizard import run_setup_wizard
from osint.utils.config_manager import is_setup_complete, read_config, reset_config


@click.group(invoke_without_command=True)
@click.option(
    "--skip-setup",
    is_flag=True,
    default=False,
    help="Run without launching the interactive setup wizard.",
)
@click.pass_context
def cli(ctx: click.Context, skip_setup: bool) -> None:
    """Not-your-mom's-OSINT command line interface."""

    if not skip_setup and not is_setup_complete():
        if ctx.invoked_subcommand is None:
            run_setup_wizard()

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command("setup")
def setup_cmd() -> None:
    """Run the interactive setup wizard."""

    run_setup_wizard()


@cli.command("config")
@click.option("--show", is_flag=True, help="Display the current configuration.")
@click.option("--reset", is_flag=True, help="Delete the configuration file.")
def config_cmd(show: bool, reset: bool) -> None:
    """View, reset, or re-run configuration."""

    if reset:
        path = reset_config()
        click.echo(f"Configuration file removed (if present): {path}")
        return

    if show:
        config = read_config()
        click.echo(json.dumps(config, indent=2, sort_keys=True))
        return

    run_setup_wizard()
