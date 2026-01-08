from __future__ import annotations

import sys

from osint.cli.app import cli
from osint.cli.setup_wizard import run_setup_wizard
from osint.utils.config_manager import ConfigManager


def _should_run_setup_bootstrap(argv: list[str]) -> bool:
    if any(arg in {"-h", "--help"} for arg in argv):
        return False
    if "--skip-setup" in argv:
        return False

    subcommand = next((arg for arg in argv[1:] if not arg.startswith("-")), None)
    if subcommand in {"setup", "config"}:
        return False

    return True


def main() -> None:
    if _should_run_setup_bootstrap(sys.argv):
        cm = ConfigManager.default()
        if not cm.load().get("setup_complete"):
            run_setup_wizard(cm)

    cli(prog_name="osint")


if __name__ == "__main__":
    main()
