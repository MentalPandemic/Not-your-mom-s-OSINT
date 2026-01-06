"""Main entry point for the osint CLI."""

import sys

import click

from osint.cli.commands import cli


def main() -> int:
    """Main entry point for the CLI."""
    try:
        cli(standalone_mode=False)
        return 0
    except click.exceptions.Exit as e:
        return e.exit_code
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
