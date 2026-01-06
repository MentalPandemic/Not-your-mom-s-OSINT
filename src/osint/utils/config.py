"""Configuration utilities for the OSINT platform."""

import json
import os
from pathlib import Path
from typing import Any, Optional


class Config:
    """Configuration management class for OSINT settings.

    This class handles loading, saving, and accessing configuration
    settings from a JSON file.
    """

    DEFAULT_CONFIG_PATH = Path.home() / ".config" / "osint" / "config.json"
    DEFAULT_CONFIG = {
        "timeout": 30,
        "max_retries": 3,
        "user_agent": "Mozilla/5.0 (compatible; Not-your-moms-OSINT/0.1.0)",
        "output_format": "json",
        "log_level": "INFO",
        "sources": {
            "sherlock": {"enabled": True},
        },
    }

    def __init__(self, config_path: Optional[Path] = None) -> None:
        """Initialize the Config class.

        Args:
            config_path: Path to the configuration file. If not provided,
                        uses the default path.
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config: dict[str, Any] = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from file or create default.

        Returns:
            Dictionary containing configuration settings
        """
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    user_config = json.load(f)
                    config = self.DEFAULT_CONFIG.copy()
                    config.update(user_config)
                    return config
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config: {e}. Using defaults.")
                return self.DEFAULT_CONFIG.copy()
        else:
            return self.DEFAULT_CONFIG.copy()

    def save(self) -> None:
        """Save current configuration to file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=2)
        except IOError as e:
            print(f"Error saving config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key (supports nested keys with dots)
            default: Default value if key not found

        Returns:
            Configuration value or default

        Example:
            >>> config.get("timeout")
            30
            >>> config.get("sources.sherlock.enabled")
            True
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key (supports nested keys with dots)
            value: Value to set

        Example:
            >>> config.set("timeout", 60)
            >>> config.set("sources.sherlock.enabled", False)
        """
        keys = key.split(".")
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def reset(self) -> None:
        """Reset configuration to default values."""
        self.config = self.DEFAULT_CONFIG.copy()

    def reset_to_file(self) -> None:
        """Reset configuration to default and save to file."""
        self.reset()
        self.save()


def get_config() -> Config:
    """Get the global configuration instance.

    Returns:
        Config instance
    """
    return Config()


def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get an environment variable.

    Args:
        key: Environment variable name
        default: Default value if not found

    Returns:
        Environment variable value or default
    """
    return os.getenv(key, default)
