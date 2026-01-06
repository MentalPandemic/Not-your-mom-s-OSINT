"""Configuration utilities for OSINT tools."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


def get_config_dir() -> Path:
    """Get the configuration directory path.
    
    Returns:
        Path to configuration directory
    """
    if os.name == 'nt':  # Windows
        config_dir = Path(os.environ.get('APPDATA', '')) / 'osint'
    else:  # Linux/macOS
        config_dir = Path.home() / '.config' / 'osint'
    
    return config_dir


def get_config_file() -> Path:
    """Get the main configuration file path.
    
    Returns:
        Path to configuration file
    """
    return get_config_dir() / 'config.json'


def ensure_config_dir():
    """Ensure the configuration directory exists."""
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)


def load_config() -> Dict[str, Any]:
    """Load configuration from file.
    
    Returns:
        Configuration dictionary
    """
    config_file = get_config_file()
    
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load config file {config_file}: {e}")
            return get_default_config()
    else:
        return get_default_config()


def save_config(config: Dict[str, Any]):
    """Save configuration to file.
    
    Args:
        config: Configuration dictionary to save
    """
    ensure_config_dir()
    config_file = get_config_file()
    
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    except IOError as e:
        print(f"Warning: Could not save config file {config_file}: {e}")


def get_default_config() -> Dict[str, Any]:
    """Get default configuration.
    
    Returns:
        Default configuration dictionary
    """
    return {
        "sources": {
            "sherlock": {
                "enabled": True,
                "timeout": 30,
                "max_concurrent": 10
            }
        },
        "output": {
            "default_format": "json",
            "timestamp_format": "iso",
            "include_metadata": True
        },
        "requests": {
            "timeout": 30,
            "retries": 3,
            "user_agent": "Not-your-moms-OSINT/0.1.0"
        },
        "correlation": {
            "enabled": True,
            "similarity_threshold": 0.8,
            "max_correlations": 100
        }
    }


def get_source_config(config: Dict[str, Any], source_name: str) -> Dict[str, Any]:
    """Get configuration for a specific source.
    
    Args:
        config: Main configuration dictionary
        source_name: Name of the source
        
    Returns:
        Source configuration dictionary
    """
    sources = config.get('sources', {})
    return sources.get(source_name, {})


def is_source_enabled(config: Dict[str, Any], source_name: str) -> bool:
    """Check if a source is enabled.
    
    Args:
        config: Main configuration dictionary
        source_name: Name of the source
        
    Returns:
        True if source is enabled, False otherwise
    """
    source_config = get_source_config(config, source_name)
    return source_config.get('enabled', True)


def update_source_config(config: Dict[str, Any], source_name: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update configuration for a specific source.
    
    Args:
        config: Main configuration dictionary
        source_name: Name of the source
        updates: Dictionary of updates to apply
        
    Returns:
        Updated configuration dictionary
    """
    if 'sources' not in config:
        config['sources'] = {}
    
    if source_name not in config['sources']:
        config['sources'][source_name] = {}
    
    config['sources'][source_name].update(updates)
    return config


def get_output_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Get output configuration.
    
    Args:
        config: Main configuration dictionary
        
    Returns:
        Output configuration dictionary
    """
    return config.get('output', {})


def get_request_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Get request configuration.
    
    Args:
        config: Main configuration dictionary
        
    Returns:
        Request configuration dictionary
    """
    return config.get('requests', {})


def get_user_agent(config: Dict[str, Any]) -> str:
    """Get user agent string from configuration.
    
    Args:
        config: Main configuration dictionary
        
    Returns:
        User agent string
    """
    request_config = get_request_config(config)
    return request_config.get('user_agent', 'Not-your-moms-OSINT/0.1.0')


def get_timeout(config: Dict[str, Any]) -> int:
    """Get request timeout from configuration.
    
    Args:
        config: Main configuration dictionary
        
    Returns:
        Timeout in seconds
    """
    request_config = get_request_config(config)
    return request_config.get('timeout', 30)


def initialize_config():
    """Initialize configuration with defaults if it doesn't exist."""
    config_file = get_config_file()
    
    if not config_file.exists():
        print("Initializing default configuration...")
        config = get_default_config()
        save_config(config)
        print(f"Configuration saved to: {config_file}")
    else:
        print(f"Configuration already exists at: {config_file}")


# Cache for loaded configuration
_config_cache = None


def get_cached_config() -> Dict[str, Any]:
    """Get cached configuration (loads once).
    
    Returns:
        Configuration dictionary
    """
    global _config_cache
    
    if _config_cache is None:
        _config_cache = load_config()
    
    return _config_cache


def clear_config_cache():
    """Clear the configuration cache."""
    global _config_cache
    _config_cache = None