from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import click

from osint.utils.config import default_config, resolve_config_path

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def validate_email(email: str) -> str:
    email = email.strip()
    if not email:
        return ""
    if not _EMAIL_RE.match(email):
        raise click.BadParameter("Invalid email format.")
    return email


def validate_results_path(path_str: str) -> str:
    path_str = (path_str or "").strip() or "./results"

    expanded_path = Path(path_str).expanduser()

    try:
        expanded_path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise click.BadParameter(f"Unable to create results path: {exc}") from exc

    return path_str


def _safe_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")

    os.replace(tmp_path, path)

    try:
        os.chmod(path, 0o600)
    except OSError:
        # Best-effort on platforms/filesystems that don't support chmod.
        pass


@dataclass
class ConfigManager:
    path: Path

    @classmethod
    def default(cls) -> "ConfigManager":
        return cls(path=resolve_config_path())

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return default_config()

        try:
            with self.path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as exc:
            raise click.ClickException(
                f"Config file is not valid JSON: {self.path}"
            ) from exc

        merged = default_config()
        merged.update(data or {})
        merged.setdefault("api_keys", {})
        merged["api_keys"] = {
            **default_config()["api_keys"],
            **(merged.get("api_keys") or {}),
        }
        return merged

    def save(self, config: dict[str, Any]) -> None:
        _safe_write_json(self.path, config)

    def reset(self) -> dict[str, Any]:
        cfg = default_config()
        self.save(cfg)
        return cfg
