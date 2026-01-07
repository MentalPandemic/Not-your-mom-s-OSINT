"""
Unit tests for CLI functionality.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from osint.cli import cli


class TestCLI:
    """Test cases for main CLI functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.runner = CliRunner()
    
    def teardown_method(self):
        """Cleanup after test method."""
        shutil.rmtree(self.temp_dir)
    
    def test_version_option(self):
        """Test version option."""
        result = self.runner.invoke(cli, ['--version'])
        
        assert result.exit_code == 0
        assert "Not-your-mom's-OSINT" in result.output
        assert "v1.0.0" in result.output
    
    def test_config_command_show_no_config(self):
        """Test config command with show option when no config exists."""
        result = self.runner.invoke(cli, ['config', '--show'])
        
        assert result.exit_code == 0
        assert "Current Configuration" in result.output
        assert "Not configured" in result.output
    
    def test_config_command_show_with_config(self):
        """Test config command with show option when config exists."""
        config_path = Path(self.temp_dir) / "config.json"
        test_config = {
            "output_format": "csv",
            "verbose_logging": True,
            "results_path": "/tmp/results",
            "sherlock_enabled": True,
            "api_keys": {
                "twitter": "test_key",
                "facebook": "",
                "linkedin": "",
                "instagram": ""
            },
            "auto_updates": True,
            "notification_email": "user@example.com",
            "advanced_features": False,
            "setup_complete": True
        }
        
        config_path.write_text(json.dumps(test_config))
        
        with patch('osint.utils.config_manager.ConfigManager') as mock_manager:
            mock_instance = MagicMock()
            mock_instance.load_config.return_value = test_config
            mock_instance.get_config_path.return_value = config_path
            mock_manager.return_value = mock_instance
            
            result = self.runner.invoke(cli, ['config', '--show'])
            
            assert result.exit_code == 0
            assert "Current Configuration" in result.output
            assert "csv" in result.output
            assert "Enabled" in result.output
            assert "user@example.com" in result.output
    
    def test_config_command_path(self):
        """Test config command with path option."""
        with patch('osint.utils.config_manager.ConfigManager') as mock_manager:
            mock_instance = MagicMock()
            expected_path = "/path/to/config.json"
            mock_instance.get_config_path.return_value = Path(expected_path)
            mock_manager.return_value = mock_instance
            
            result = self.runner.invoke(cli, ['config', '--path'])
            
            assert result.exit_code == 0
            assert expected_path in result.output
    
    def test_config_command_reset(self):
        """Test config command with reset option."""
        config_path = Path(self.temp_dir) / "config.json"
        config_path.write_text('{"output_format": "json"}')
        
        with patch('osint.utils.config_manager.ConfigManager') as mock_manager:
            mock_instance = MagicMock()
            mock_instance.create_default_config.return_value = {"setup_complete": False}
            mock_instance.save_config.return_value = True
            mock_manager.return_value = mock_instance
            
            with patch('click.confirm') as mock_confirm:
                mock_confirm.return_value = True
                
                result = self.runner.invoke(cli, ['config', '--reset'])
                
                assert result.exit_code == 0
                assert "reset to defaults" in result.output
                mock_instance.save_config.assert_called_once()
    
    def test_config_command_reset_cancelled(self):
        """Test config command with reset option when cancelled by user."""
        with patch('click.confirm') as mock_confirm:
            mock_confirm.return_value = False
            
            result = self.runner.invoke(cli, ['config', '--reset'])
            
            assert result.exit_code == 0
            assert "Reset cancelled" in result.output
    
    def test_config_command_no_options(self):
        """Test config command without options shows help."""
        result = self.runner.invoke(cli, ['config'])
        
        assert result.exit_code == 0
        assert "Configuration commands" in result.output
        assert "osint config --show" in result.output
    
    def test_first_run_setup_wizard_triggered(self):
        """Test that setup wizard is triggered on first run."""
        with patch('osint.utils.config_manager.ConfigManager') as mock_manager:
            mock_instance = MagicMock()
            mock_instance.is_setup_complete.return_value = False
            mock_manager.return_value = mock_instance
            
            with patch('click.confirm') as mock_confirm:
                mock_confirm.return_value = False  # Skip setup
                
                result = self.runner.invoke(cli, [])
                
                assert result.exit_code == 0
                mock_instance.is_setup_complete.assert_called_once()
    
    def test_skip_setup_option(self):
        """Test skip setup option."""
        result = self.runner.invoke(cli, ['--skip-setup'])
        
        assert result.exit_code == 0
        assert "Setup wizard skipped" in result.output
    
    def test_setup_command_integration(self):
        """Test that setup command is properly integrated."""
        result = self.runner.invoke(cli, ['setup', '--help'])
        
        assert result.exit_code == 0
        assert "Run the interactive setup wizard" in result.output