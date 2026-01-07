"""
Configuration manager for Not-your-mom's-OSINT platform.
Handles reading and writing configuration files.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """Manages configuration file operations for the OSINT platform."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the configuration manager.
        
        Args:
            config_path: Path to configuration file. If None, uses default locations.
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Default to user home directory or current directory
            home_config = Path.home() / ".osint_config.json"
            current_dir_config = Path.cwd() / "osint_config.json"
            
            if home_config.exists():
                self.config_path = home_config
            else:
                self.config_path = current_dir_config
    
    def get_config_path(self) -> Path:
        """Get the current configuration file path."""
        return self.config_path
    
    def create_default_config(self) -> Dict[str, Any]:
        """Create default configuration dictionary."""
        return {
            "output_format": "json",
            "verbose_logging": False,
            "results_path": "./results",
            "sherlock_enabled": False,
            "api_keys": {
                "twitter": "",
                "facebook": "",
                "linkedin": "",
                "instagram": ""
            },
            "auto_updates": False,
            "notification_email": "",
            "advanced_features": False,
            "setup_complete": False
        }
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file.
        
        Returns:
            Dictionary containing configuration, or default config if file doesn't exist.
        """
        if not self.config_path.exists():
            return self.create_default_config()
        
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            # Merge with defaults to ensure all keys exist
            default_config = self.create_default_config()
            default_config.update(config)
            return default_config
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load config file: {e}")
            return self.create_default_config()
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to file.
        
        Args:
            config: Dictionary containing configuration to save.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Create directory if it doesn't exist
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            return True
            
        except (IOError, OSError) as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def is_setup_complete(self) -> bool:
        """Check if initial setup has been completed."""
        config = self.load_config()
        return config.get("setup_complete", False)
    
    def mark_setup_complete(self) -> bool:
        """Mark setup as complete in configuration."""
        config = self.load_config()
        config["setup_complete"] = True
        return self.save_config(config)
    
    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate configuration values.
        
        Args:
            config: Configuration dictionary to validate.
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate output format
        if config.get("output_format") not in ["json", "csv", "both"]:
            errors.append("Invalid output format. Must be 'json', 'csv', or 'both'")
        
        # Validate results path
        results_path = config.get("results_path", "")
        if results_path and not self._is_valid_path(results_path):
            errors.append("Invalid results path")
        
        # Validate email
        email = config.get("notification_email", "")
        if email and not self._is_valid_email(email):
            errors.append("Invalid email format")
        
        # Validate API keys are strings
        api_keys = config.get("api_keys", {})
        if not isinstance(api_keys, dict):
            errors.append("API keys must be a dictionary")
        else:
            for platform, key in api_keys.items():
                if not isinstance(key, str):
                    errors.append(f"API key for {platform} must be a string")
        
        return len(errors) == 0, errors
    
    def _is_valid_email(self, email: str) -> bool:
        """Simple email validation."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _is_valid_path(self, path: str) -> bool:
        """Validate that a path is reasonable."""
        try:
            # Test if we can create the directory
            Path(path).mkdir(parents=True, exist_ok=True)
            return True
        except (OSError, ValueError):
            return False