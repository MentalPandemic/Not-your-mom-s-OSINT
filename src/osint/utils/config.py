"""
Configuration utilities for Not-your-mom's-OSINT platform.
"""

import os
from pathlib import Path
from typing import Optional


def get_config_dir() -> Path:
    """Get the directory for storing configuration files."""
    return Path.home() / ".osint"


def get_default_config_path() -> Path:
    """Get the default configuration file path."""
    return get_config_dir() / "config.json"


def ensure_config_dir() -> bool:
    """Ensure the configuration directory exists.
    
    Returns:
        True if directory exists or was created successfully.
    """
    try:
        get_config_dir().mkdir(parents=True, exist_ok=True)
        return True
    except OSError:
        return False


def is_first_run() -> bool:
    """Check if this is the first time running the application."""
    return not get_default_config_path().exists()


def get_user_data_dir() -> Path:
    """Get the directory for user data and results."""
    return Path.home() / ".osint" / "data"


def get_results_dir() -> str:
    """Get the default results directory."""
    return str(get_user_data_dir() / "results")


def expand_path(path: str) -> str:
    """Expand user path shortcuts like ~ and environment variables."""
    return os.path.expanduser(os.path.expandvars(path))