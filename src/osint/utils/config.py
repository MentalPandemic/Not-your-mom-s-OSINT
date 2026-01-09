"""Configuration path helpers for Not-your-mom's-OSINT."""

from __future__ import annotations

import os
from pathlib import Path


def get_local_config_path(cwd: Path | None = None) -> Path:
    base = cwd or Path.cwd()
    return base / "osint_config.json"


def get_home_config_path() -> Path:
    return Path.home() / ".osint_config.json"


def get_config_path() -> Path:
    """Get the effective configuration path.

    Priority:
      1) OSINT_CONFIG_PATH env var (if set)
      2) ./osint_config.json (if present)
      3) ~/.osint_config.json
    """

    env_path = os.environ.get("OSINT_CONFIG_PATH")
    if env_path:
        return Path(env_path).expanduser()

    local_config = get_local_config_path()
    if local_config.exists():
        return local_config

    return get_home_config_path()


def resolve_results_dir(results_path: str, cwd: Path | None = None) -> Path:
    """Resolve a results directory path.

    - Expands '~'
    - Resolves relative paths against cwd (defaults to Path.cwd())
    """

    base = cwd or Path.cwd()
    path = Path(results_path or "./results").expanduser()
    if not path.is_absolute():
        path = base / path
    return path
