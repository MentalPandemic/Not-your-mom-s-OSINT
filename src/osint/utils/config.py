"""Configuration utilities for Not-your-mom's-OSINT."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


def get_config_dir() -> Path:
    """Get the configuration directory path."""
    config_dir = Path.home() / ".config" / "osint"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_cache_dir() -> Path:
    """Get the cache directory path."""
    cache_dir = Path.home() / ".cache" / "osint"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def load_config(config_name: str = "osint.json") -> Dict[str, Any]:
    """
    Load configuration from file.
    
    Args:
        config_name: Name of the configuration file
        
    Returns:
        Configuration dictionary
    """
    config_path = get_config_dir() / config_name
    
    if not config_path.exists():
        return {}
    
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_config(config: Dict[str, Any], config_name: str = "osint.json") -> None:
    """
    Save configuration to file.
    
    Args:
        config: Configuration dictionary to save
        config_name: Name of the configuration file
    """
    config_path = get_config_dir() / config_name
    
    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
    except IOError as e:
        raise RuntimeError(f"Failed to save configuration: {e}")


def get_default_timeout() -> int:
    """Get the default timeout for OSINT operations."""
    return int(os.environ.get("OSINT_DEFAULT_TIMEOUT", "30"))


def get_max_workers() -> int:
    """Get the maximum number of worker threads."""
    return int(os.environ.get("OSINT_MAX_WORKERS", "5"))


def load_source_config(source_name: str) -> Dict[str, Any]:
    """
    Load configuration for a specific source.
    
    Args:
        source_name: Name of the source
        
    Returns:
        Source-specific configuration dictionary
    """
    config = load_config()
    return config.get("sources", {}).get(source_name, {})
