"""Configuration read/write utilities.

Configuration is stored as JSON at either:
- ./osint_config.json (preferred if present)
- ~/.osint_config.json

An explicit path can be provided via OSINT_CONFIG_PATH.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from osint.utils.config import get_config_path


EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def default_config() -> dict[str, Any]:
    return {
        "output_format": "json",
        "verbose_logging": False,
        "results_path": "./results",
        "sherlock_enabled": False,
        "sherlock": {
            "timeout": 10,
            "threads": 10,
            "retries": 3,
            "no_nsfw": False,
        },
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


def resolve_config_path(explicit_path: str | Path | None = None) -> Path:
    if explicit_path is not None:
        return Path(explicit_path).expanduser()

    env_path = os.environ.get("OSINT_CONFIG_PATH")
    if env_path:
        return Path(env_path).expanduser()

    return get_config_path()


def ensure_results_path(path_str: str) -> str:
    raw = (path_str or "").strip() or "./results"
    path = Path(raw).expanduser()

    if path.exists() and not path.is_dir():
        raise ValueError(f"Results path is not a directory: {path}")

    path.mkdir(parents=True, exist_ok=True)

    if raw.startswith("~"):
        return str(path)
    return raw


def validate_email(email: str) -> str:
    email = email.strip()
    if not email:
        return ""
    if not EMAIL_REGEX.match(email):
        raise ValueError("Invalid email address format")
    return email


def read_config(path: str | Path | None = None) -> dict[str, Any]:
    config_path = resolve_config_path(path)
    if not config_path.exists():
        return default_config()

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default_config()

    merged = default_config()
    merged.update({k: v for k, v in data.items() if k != "api_keys"})

    api_keys = merged.get("api_keys", {})
    api_keys.update((data.get("api_keys") or {}))
    merged["api_keys"] = api_keys

    return merged


def _write_atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile("w", delete=False, dir=str(path.parent), encoding="utf-8") as tf:
        json.dump(payload, tf, indent=2, sort_keys=True)
        tf.write("\n")
        temp_name = tf.name

    os.replace(temp_name, path)

    try:
        os.chmod(path, 0o600)
    except PermissionError:
        pass


def write_config(config: dict[str, Any], path: str | Path | None = None) -> Path:
    config_path = resolve_config_path(path)
    _write_atomic_json(config_path, config)
    return config_path


def update_config(updates: dict[str, Any], path: str | Path | None = None) -> dict[str, Any]:
    current = read_config(path)

    if "api_keys" in updates and isinstance(updates["api_keys"], dict):
        api_keys = current.get("api_keys", {})
        api_keys.update(updates["api_keys"])
        updates = {**updates, "api_keys": api_keys}

    if "sherlock" in updates and isinstance(updates["sherlock"], dict):
        sherlock_cfg = current.get("sherlock", {})
        if isinstance(sherlock_cfg, dict):
            sherlock_cfg.update(updates["sherlock"])
            updates = {**updates, "sherlock": sherlock_cfg}

    current.update(updates)

    if "results_path" in current:
        current["results_path"] = ensure_results_path(str(current["results_path"]))

    if "notification_email" in current:
        current["notification_email"] = validate_email(str(current["notification_email"]))

    write_config(current, path)
    return current


def is_setup_complete(path: str | Path | None = None) -> bool:
    return bool(read_config(path).get("setup_complete"))


def reset_config(path: str | Path | None = None) -> Path:
    config_path = resolve_config_path(path)
    if config_path.exists():
        config_path.unlink()
    return config_path
