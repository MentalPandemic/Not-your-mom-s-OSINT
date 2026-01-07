"""
Unit tests for setup wizard functionality.
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

from osint.cli.setup_wizard import SetupWizard, run_setup_wizard, setup
from osint.utils.config_manager import ConfigManager


class TestSetupWizard:
    """Test cases for SetupWizard class."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_config_path = Path(self.temp_dir) / "test_config.json"
        self.wizard = SetupWizard()
        self.wizard.config_manager = ConfigManager(str(self.temp_config_path))
    
    def teardown_method(self):
        """Cleanup after test method."""
        shutil.rmtree(self.temp_dir)
    
    def test_wizard_initialization(self):
        """Test wizard initialization."""
        assert self.wizard.config_manager is not None
        assert self.wizard.current_config is not None
        assert 'output_format' in self.wizard.current_config
    
    @patch('click.echo')
    @patch('click.prompt')
    def test_setup_output_format_json(self, mock_prompt, mock_echo):
        """Test setting output format to JSON."""
        mock_prompt.return_value = "1"
        
        self.wizard._setup_output_format()
        
        assert self.wizard.current_config['output_format'] == 'json'
        mock_prompt.assert_called_once()
    
    @patch('click.echo')
    @patch('click.confirm')
    def test_setup_verbose_logging_true(self, mock_confirm, mock_echo):
        """Test enabling verbose logging."""
        mock_confirm.return_value = True
        
        self.wizard._setup_verbose_logging()
        
        assert self.wizard.current_config['verbose_logging'] == True
    
    @patch('click.echo')
    @patch('click.prompt')
    def test_setup_results_path(self, mock_prompt, mock_echo):
        """Test setting results path."""
        mock_prompt.return_value = "/test/path"
        
        with patch('osint.cli.setup_wizard.Path') as mock_path:
            mock_path.return_value.mkdir.return_value = None
            
            self.wizard._setup_results_path()
            
            assert self.wizard.current_config['results_path'] == "/test/path"
    
    @patch('click.echo')
    @patch('click.confirm')
    def test_setup_sherlock_integration(self, mock_confirm, mock_echo):
        """Test enabling Sherlock integration."""
        mock_confirm.return_value = True
        
        self.wizard._setup_sherlock_integration()
        
        assert self.wizard.current_config['sherlock_enabled'] == True
    
    @patch('click.echo')
    @patch('click.confirm')
    def test_setup_social_media_apis_no(self, mock_confirm, mock_echo):
        """Test declining social media API setup."""
        mock_confirm.return_value = False
        
        self.wizard._setup_social_media_apis()
        
        # API keys should remain empty
        assert all(key == "" for key in self.wizard.current_config['api_keys'].values())
    
    @patch('click.echo')
    @patch('click.confirm')
    def test_setup_social_media_apis_yes(self, mock_confirm, mock_echo):
        """Test configuring social media APIs."""
        mock_confirm.return_value = True
        
        # Mock API key prompts
        with patch('click.prompt') as mock_prompt:
            mock_prompt.side_effect = [
                "twitter_key_123",
                "facebook_key_456", 
                "linkedin_key_789",
                "instagram_key_012"
            ]
            
            self.wizard._setup_social_media_apis()
            
            assert self.wizard.current_config['api_keys']['twitter'] == "twitter_key_123"
            assert self.wizard.current_config['api_keys']['facebook'] == "facebook_key_456"
            assert self.wizard.current_config['api_keys']['linkedin'] == "linkedin_key_789"
            assert self.wizard.current_config['api_keys']['instagram'] == "instagram_key_012"
    
    @patch('click.echo')
    @patch('click.confirm')
    def test_setup_auto_updates(self, mock_confirm, mock_echo):
        """Test enabling automatic updates."""
        mock_confirm.return_value = True
        
        self.wizard._setup_auto_updates()
        
        assert self.wizard.current_config['auto_updates'] == True
    
    @patch('click.echo')
    @patch('click.prompt')
    def test_setup_notifications_empty(self, mock_prompt, mock_echo):
        """Test setting notifications with empty email."""
        mock_prompt.return_value = ""
        
        self.wizard._setup_notifications()
        
        assert self.wizard.current_config['notification_email'] == ""
    
    @patch('click.echo')
    @patch('click.prompt')
    def test_setup_notifications_valid_email(self, mock_prompt, mock_echo):
        """Test setting notifications with valid email."""
        mock_prompt.side_effect = ["test@example.com"]
        
        self.wizard._setup_notifications()
        
        assert self.wizard.current_config['notification_email'] == "test@example.com"
    
    @patch('click.echo')
    @patch('click.prompt')
    def test_setup_notifications_invalid_then_valid(self, mock_prompt, mock_echo):
        """Test email validation with invalid then valid email."""
        mock_prompt.side_effect = ["invalid-email", "valid@example.com"]
        
        self.wizard._setup_notifications()
        
        assert self.wizard.current_config['notification_email'] == "valid@example.com"
    
    @patch('click.echo')
    @patch('click.confirm')
    def test_setup_advanced_features(self, mock_confirm, mock_echo):
        """Test enabling advanced features."""
        mock_confirm.return_value = True
        
        self.wizard._setup_advanced_features()
        
        assert self.wizard.current_config['advanced_features'] == True
    
    def test_is_valid_email(self):
        """Test email validation."""
        valid_emails = [
            "test@example.com",
            "user.name+tag@domain.co.uk",
            "user@subdomain.domain.com"
        ]
        
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "",
            "user@@domain.com"
        ]
        
        for email in valid_emails:
            assert self.wizard._is_valid_email(email) == True, f"Email {email} should be valid"
        
        for email in invalid_emails:
            assert self.wizard._is_valid_email(email) == False, f"Email {email} should be invalid"
    
    def test_validate_and_save_success(self):
        """Test successful validation and saving."""
        # Valid configuration
        self.wizard.current_config = {
            "output_format": "json",
            "verbose_logging": True,
            "results_path": str(self.temp_dir),
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
        
        result = self.wizard._validate_and_save()
        
        assert result == True
        assert self.temp_config_path.exists()
        
        with open(self.temp_config_path, 'r') as f:
            saved_config = json.load(f)
        
        assert saved_config['output_format'] == 'json'
        assert saved_config['setup_complete'] == True  # Should be marked complete
    
    def test_validate_and_save_invalid_config(self):
        """Test validation and save with invalid configuration."""
        # Invalid configuration
        self.wizard.current_config = {
            "output_format": "invalid_format",  # Invalid
            "verbose_logging": True,
            "results_path": "/nonexistent/path",
            "notification_email": "invalid-email"
        }
        
        result = self.wizard._validate_and_save()
        
        assert result == False
        # File should not exist or should not be marked complete
        if self.temp_config_path.exists():
            with open(self.temp_config_path, 'r') as f:
                saved_config = json.load(f)
            assert saved_config.get('setup_complete', False) == False


class TestSetupCommands:
    """Test cases for CLI setup commands."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.runner = CliRunner()
    
    def teardown_method(self):
        """Cleanup after test method."""
        shutil.rmtree(self.temp_dir)
    
    @patch('osint.cli.setup_wizard.run_setup_wizard')
    def test_setup_command_force(self, mock_run_wizard):
        """Test setup command with force flag."""
        mock_run_wizard.return_value = True
        
        result = self.runner.invoke(setup, ['--force'])
        
        assert result.exit_code == 0
        mock_run_wizard.assert_called_once()
    
    @patch('osint.cli.setup_wizard.run_setup_wizard')
    def test_setup_command_force_fails(self, mock_run_wizard):
        """Test setup command with force flag when wizard fails."""
        mock_run_wizard.return_value = False
        
        result = self.runner.invoke(setup, ['--force'])
        
        assert result.exit_code == 1
        mock_run_wizard.assert_called_once()
    
    def test_setup_command_already_configured(self):
        """Test setup command when already configured."""
        config_path = Path(self.temp_dir) / "config.json"
        config_path.write_text(json.dumps({"setup_complete": True}))
        
        with patch('osint.utils.config_manager.ConfigManager') as mock_manager:
            mock_instance = MagicMock()
            mock_instance.is_setup_complete.return_value = True
            mock_instance.config_path = config_path
            mock_manager.return_value = mock_instance
            
            with patch('click.confirm') as mock_confirm:
                mock_confirm.return_value = False
                
                result = self.runner.invoke(setup, [])
                
                assert result.exit_code == 0
                # Should not run wizard when user declines
    
    def test_setup_command_already_configured_reconfigure(self):
        """Test setup command when already configured but user wants to reconfigure."""
        config_path = Path(self.temp_dir) / "config.json"
        config_path.write_text(json.dumps({"setup_complete": True}))
        
        with patch('osint.utils.config_manager.ConfigManager') as mock_manager:
            mock_instance = MagicMock()
            mock_instance.is_setup_complete.return_value = True
            mock_instance.config_path = config_path
            mock_manager.return_value = mock_instance
            
            with patch('click.confirm') as mock_confirm:
                # First call: re-run setup, Second call: overwrite config
                mock_confirm.side_effect = [True, True]
                
                with patch('osint.cli.setup_wizard.run_setup_wizard') as mock_run_wizard:
                    mock_run_wizard.return_value = True
                    
                    result = self.runner.invoke(setup, [])
                    
                    assert result.exit_code == 0
                    assert mock_confirm.call_count == 2
                    mock_run_wizard.assert_called_once()


class TestRunSetupWizard:
    """Test cases for standalone run_setup_wizard function."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup after test method."""
        shutil.rmtree(self.temp_dir)
    
    @patch('osint.cli.setup_wizard.SetupWizard')
    def test_run_setup_wizard_success(self, mock_wizard_class):
        """Test successful setup wizard execution."""
        mock_wizard = MagicMock()
        mock_wizard.run_wizard.return_value = True
        mock_wizard_class.return_value = mock_wizard
        
        result = run_setup_wizard()
        
        assert result == True
        mock_wizard_class.assert_called_once()
        mock_wizard.run_wizard.assert_called_once()
    
    @patch('osint.cli.setup_wizard.SetupWizard')
    def test_run_setup_wizard_failure(self, mock_wizard_class):
        """Test failed setup wizard execution."""
        mock_wizard = MagicMock()
        mock_wizard.run_wizard.return_value = False
        mock_wizard_class.return_value = mock_wizard
        
        result = run_setup_wizard()
        
        assert result == False
        mock_wizard_class.assert_called_once()
        mock_wizard.run_wizard.assert_called_once()