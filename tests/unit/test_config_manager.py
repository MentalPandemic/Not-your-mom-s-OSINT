"""
Unit tests for ConfigManager functionality.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from osint.utils.config_manager import ConfigManager


class TestConfigManager:
    """Test cases for ConfigManager class."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_config_path = Path(self.temp_dir) / "test_config.json"
    
    def teardown_method(self):
        """Cleanup after each test method."""
        shutil.rmtree(self.temp_dir)
    
    def test_init_default_path(self):
        """Test initialization with default path."""
        with patch('osint.utils.config_manager.Path.home') as mock_home:
            mock_home.return_value = Path('/mock/home')
            config_manager = ConfigManager()
            expected_path = Path('/mock/home/.osint_config.json')
            assert config_manager.config_path == expected_path
    
    def test_init_custom_path(self):
        """Test initialization with custom path."""
        custom_path = "/custom/path/config.json"
        config_manager = ConfigManager(custom_path)
        assert config_manager.config_path == Path(custom_path)
    
    def test_get_config_path(self):
        """Test getting configuration path."""
        config_manager = ConfigManager(str(self.temp_config_path))
        assert config_manager.get_config_path() == self.temp_config_path
    
    def test_create_default_config(self):
        """Test creating default configuration."""
        config_manager = ConfigManager()
        default_config = config_manager.create_default_config()
        
        assert isinstance(default_config, dict)
        assert default_config['output_format'] == 'json'
        assert default_config['verbose_logging'] == False
        assert default_config['results_path'] == './results'
        assert default_config['sherlock_enabled'] == False
        assert 'api_keys' in default_config
        assert default_config['auto_updates'] == False
        assert default_config['notification_email'] == ''
        assert default_config['advanced_features'] == False
        assert default_config['setup_complete'] == False
    
    def test_load_config_nonexistent_file(self):
        """Test loading config when file doesn't exist."""
        config_manager = ConfigManager(str(self.temp_config_path))
        config = config_manager.load_config()
        
        assert isinstance(config, dict)
        assert config['output_format'] == 'json'  # Default value
    
    def test_load_config_existing_file(self):
        """Test loading config from existing file."""
        test_config = {
            "output_format": "csv",
            "verbose_logging": True,
            "setup_complete": True
        }
        
        with open(self.temp_config_path, 'w') as f:
            json.dump(test_config, f)
        
        config_manager = ConfigManager(str(self.temp_config_path))
        config = config_manager.load_config()
        
        assert config['output_format'] == 'csv'
        assert config['verbose_logging'] == True
        assert config['setup_complete'] == True
        # Should have default values for missing keys
        assert config['results_path'] == './results'
    
    def test_load_config_invalid_json(self):
        """Test loading config with invalid JSON."""
        with open(self.temp_config_path, 'w') as f:
            f.write("invalid json content")
        
        config_manager = ConfigManager(str(self.temp_config_path))
        config = config_manager.load_config()
        
        # Should return default config on error
        assert config['output_format'] == 'json'
        assert config['verbose_logging'] == False
    
    def test_save_config(self):
        """Test saving configuration to file."""
        config_manager = ConfigManager(str(self.temp_config_path))
        test_config = {
            "output_format": "both",
            "verbose_logging": True,
            "results_path": "/tmp/test",
            "setup_complete": True
        }
        
        result = config_manager.save_config(test_config)
        assert result == True
        assert self.temp_config_path.exists()
        
        with open(self.temp_config_path, 'r') as f:
            saved_config = json.load(f)
        
        assert saved_config['output_format'] == 'both'
        assert saved_config['verbose_logging'] == True
    
    def test_save_config_create_directory(self):
        """Test saving config creates directory if needed."""
        nested_path = Path(self.temp_dir) / "nested" / "dir" / "config.json"
        config_manager = ConfigManager(str(nested_path))
        
        test_config = {"output_format": "json"}
        result = config_manager.save_config(test_config)
        
        assert result == True
        assert nested_path.exists()
    
    def test_is_setup_complete_true(self):
        """Test setup completion detection when complete."""
        config = {"setup_complete": True}
        with open(self.temp_config_path, 'w') as f:
            json.dump(config, f)
        
        config_manager = ConfigManager(str(self.temp_config_path))
        assert config_manager.is_setup_complete() == True
    
    def test_is_setup_complete_false(self):
        """Test setup completion detection when not complete."""
        config = {"setup_complete": False}
        with open(self.temp_config_path, 'w') as f:
            json.dump(config, f)
        
        config_manager = ConfigManager(str(self.temp_config_path))
        assert config_manager.is_setup_complete() == False
    
    def test_mark_setup_complete(self):
        """Test marking setup as complete."""
        config_manager = ConfigManager(str(self.temp_config_path))
        
        # Start with incomplete setup
        initial_config = {"setup_complete": False}
        config_manager.save_config(initial_config)
        
        # Mark as complete
        result = config_manager.mark_setup_complete()
        assert result == True
        
        # Verify it's marked complete
        config = config_manager.load_config()
        assert config['setup_complete'] == True
    
    def test_validate_config_valid(self):
        """Test validation of valid configuration."""
        config_manager = ConfigManager()
        valid_config = {
            "output_format": "json",
            "verbose_logging": True,
            "results_path": "/tmp/valid",
            "notification_email": "test@example.com",
            "api_keys": {
                "twitter": "key123",
                "facebook": "",
                "linkedin": "",
                "instagram": ""
            }
        }
        
        is_valid, errors = config_manager.validate_config(valid_config)
        assert is_valid == True
        assert len(errors) == 0
    
    def test_validate_config_invalid_output_format(self):
        """Test validation with invalid output format."""
        config_manager = ConfigManager()
        invalid_config = {
            "output_format": "invalid_format",
            "verbose_logging": True,
            "results_path": "/tmp/valid"
        }
        
        is_valid, errors = config_manager.validate_config(invalid_config)
        assert is_valid == False
        assert any("Invalid output format" in error for error in errors)
    
    def test_validate_config_invalid_email(self):
        """Test validation with invalid email format."""
        config_manager = ConfigManager()
        invalid_config = {
            "output_format": "json",
            "notification_email": "invalid-email"
        }
        
        is_valid, errors = config_manager.validate_config(invalid_config)
        assert is_valid == False
        assert any("Invalid email format" in error for error in errors)
    
    def test_validate_config_invalid_api_keys(self):
        """Test validation with invalid API keys structure."""
        config_manager = ConfigManager()
        invalid_config = {
            "output_format": "json",
            "api_keys": "invalid"  # Should be dict
        }
        
        is_valid, errors = config_manager.validate_config(invalid_config)
        assert is_valid == False
        assert any("API keys must be a dictionary" in error for error in errors)
    
    def test_validate_config_invalid_api_key_type(self):
        """Test validation with invalid API key type."""
        config_manager = ConfigManager()
        invalid_config = {
            "output_format": "json",
            "api_keys": {
                "twitter": 123  # Should be string
            }
        }
        
        is_valid, errors = config_manager.validate_config(invalid_config)
        assert is_valid == False
        assert any("must be a string" in error for error in errors)