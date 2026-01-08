from __future__ import annotations

import os
from pathlib import Path
from typing import Any

LOCAL_CONFIG_FILENAME = "osint_config.json"
USER_CONFIG_FILENAME = ".osint_config.json"


def default_config() -> dict[str, Any]:
    return {
        "output_format": "json",
        "verbose_logging": False,
        "results_path": "./results",
        "sherlock_enabled": False,
        "api_keys": {
            "twitter": "",
            "facebook": "",
            "linkedin": "",
            "instagram": "",
        },
        "auto_updates": True,
        "notification_email": "",
        "advanced_features": False,
        "setup_complete": False,
    }


def get_local_config_path(cwd: Path | None = None) -> Path:
    return (cwd or Path.cwd()) / LOCAL_CONFIG_FILENAME


def get_user_config_path(home: Path | None = None) -> Path:
    return (home or Path.home()) / USER_CONFIG_FILENAME


def resolve_config_path() -> Path:
    env_path = os.getenv("OSINT_CONFIG_PATH")
    if env_path:
        return Path(env_path).expanduser()

    local_path = get_local_config_path()
    if local_path.exists():
        return local_path

    return get_user_config_path()
