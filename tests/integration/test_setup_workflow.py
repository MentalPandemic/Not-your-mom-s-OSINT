"""
Integration tests for the OSINT platform setup workflow.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from osint.cli import cli
from osint.utils.config_manager import ConfigManager


class TestSetupWorkflowIntegration:
    """Integration tests for complete setup workflow."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.runner = CliRunner()
    
    def teardown_method(self):
        """Cleanup after test method."""
        shutil.rmtree(self.temp_dir)
    
    def test_complete_setup_workflow(self):
        """Test complete setup workflow from start to finish."""
        config_path = Path(self.temp_dir) / "test_config.json"
        
        # Simulate complete setup wizard interaction
        inputs = [
            "2",  # CSV output format
            "y",  # Enable verbose logging
            "/tmp/test_results",  # Results path
            "y",  # Enable Sherlock
            "y",  # Configure APIs
            "test_twitter_key",  # Twitter API key
            "",  # Facebook API key (skip)
            "",  # LinkedIn API key (skip)
            "test_instagram_key",  # Instagram API key
            "n",  # Disable auto updates
            "test@example.com",  # Notification email
            "y"  # Enable advanced features
        ]
        
        with patch('osint.utils.config_manager.ConfigManager') as mock_manager:
            mock_instance = MagicMock()
            
            # Mock file operations
            def mock_save_config(config):
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=2)
                return True
            
            mock_instance.save_config.side_effect = mock_save_config
            mock_instance.load_config.return_value = self._create_complete_config()
            mock_instance.is_setup_complete.return_value = False
            mock_instance.get_config_path.return_value = config_path
            mock_instance.create_default_config.return_value = self._create_complete_config()
            mock_manager.return_value = mock_instance
            
            # Mock all prompts
            with patch('click.prompt') as mock_prompt, \
                 patch('click.confirm') as mock_confirm, \
                 patch('osint.cli.setup_wizard.expand_path') as mock_expand, \
                 patch('osint.cli.setup_wizard.Path') as mock_path:
                
                # Set up responses for prompts and confirms
                prompt_responses = inputs
                confirm_responses = [True, True, True]  # Sherlock, APIs, Advanced features
                
                call_count = [0]
                def prompt_side_effect(*args, **kwargs):
                    response = prompt_responses[call_count[0] % len(prompt_responses)]
                    call_count[0] += 1
                    return response
                
                def confirm_side_effect(*args, **kwargs):
                    response = confirm_responses[0]
                    confirm_responses.pop(0)
                    return response
                
                mock_prompt.side_effect = prompt_side_effect
                mock_confirm.side_effect = confirm_side_effect
                mock_expand.return_value = "/tmp/test_results"
                mock_path.return_value.mkdir.return_value = None
                
                result = self.runner.invoke(cli, ['setup', '--force'])
                
                assert result.exit_code == 0
                assert "Setup Complete!" in result.output
                assert config_path.exists()
                
                # Verify saved configuration
                with open(config_path, 'r') as f:
                    saved_config = json.load(f)
                
                assert saved_config['output_format'] == 'csv'
                assert saved_config['verbose_logging'] == True
                assert saved_config['results_path'] == '/tmp/test_results'
                assert saved_config['sherlock_enabled'] == True
                assert saved_config['api_keys']['twitter'] == 'test_twitter_key'
                assert saved_config['api_keys']['instagram'] == 'test_instagram_key'
                assert saved_config['api_keys']['facebook'] == ''
                assert saved_config['api_keys']['linkedin'] == ''
                assert saved_config['auto_updates'] == False
                assert saved_config['notification_email'] == 'test@example.com'
                assert saved_config['advanced_features'] == True
                assert saved_config['setup_complete'] == True
    
    def test_config_display_after_setup(self):
        """Test displaying configuration after setup."""
        config_path = Path(self.temp_dir) / "test_config.json"
        test_config = self._create_complete_config()
        
        with open(config_path, 'w') as f:
            json.dump(test_config, f)
        
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
            assert "✓ Configured" in result.output  # For configured API keys
            assert "✗ Not configured" in result.output  # For unconfigured API keys
    
    def test_setup_reconfiguration(self):
        """Test re-running setup wizard after initial configuration."""
        config_path = Path(self.temp_dir) / "test_config.json"
        initial_config = self._create_complete_config()
        
        with open(config_path, 'w') as f:
            json.dump(initial_config, f)
        
        with patch('osint.utils.config_manager.ConfigManager') as mock_manager:
            mock_instance = MagicMock()
            mock_instance.is_setup_complete.return_value = True
            mock_instance.get_config_path.return_value = config_path
            mock_manager.return_value = mock_instance
            
            with patch('click.confirm') as mock_confirm:
                # User wants to reconfigure
                mock_confirm.side_effect = [True, True]  # Re-run setup, overwrite config
                
                with patch('osint.cli.setup_wizard.run_setup_wizard') as mock_run_wizard:
                    mock_run_wizard.return_value = True
                    
                    result = self.runner.invoke(cli, ['setup'])
                    
                    assert result.exit_code == 0
                    assert mock_confirm.call_count == 2
    
    def test_setup_cancellation(self):
        """Test cancelling setup wizard."""
        with patch('osint.utils.config_manager.ConfigManager') as mock_manager:
            mock_instance = MagicMock()
            mock_instance.is_setup_complete.return_value = False
            mock_manager.return_value = mock_instance
            
            with patch('click.confirm') as mock_confirm:
                mock_confirm.return_value = False  # User cancels setup
                
                result = self.runner.invoke(cli, [])
                
                assert result.exit_code == 0
                assert "Setup skipped" in result.output
    
    def test_invalid_configuration_handling(self):
        """Test handling of invalid configuration."""
        config_path = Path(self.temp_dir) / "test_config.json"
        invalid_config = {
            "output_format": "invalid_format",
            "verbose_logging": "not_boolean"
        }
        
        with open(config_path, 'w') as f:
            json.dump(invalid_config, f)
        
        with patch('osint.utils.config_manager.ConfigManager') as mock_manager:
            mock_instance = MagicMock()
            mock_instance.load_config.return_value = invalid_config
            mock_instance.create_default_config.return_value = self._create_complete_config()
            mock_instance.get_config_path.return_value = config_path
            mock_manager.return_value = mock_instance
            
            # Should fall back to defaults for invalid config
            result = self.runner.invoke(cli, ['config', '--show'])
            
            assert result.exit_code == 0
            # Should show default values for invalid/missing config
    
    def test_first_run_without_skip_setup(self):
        """Test first run behavior without --skip-setup flag."""
        with patch('osint.utils.config_manager.ConfigManager') as mock_manager:
            mock_instance = MagicMock()
            mock_instance.is_setup_complete.return_value = False
            mock_manager.return_value = mock_instance
            
            with patch('click.confirm') as mock_confirm:
                mock_confirm.return_value = False  # User declines setup
                
                result = self.runner.invoke(cli, [])
                
                assert result.exit_code == 0
                mock_instance.is_setup_complete.assert_called_once()
    
    def _create_complete_config(self):
        """Create a complete test configuration."""
        return {
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
            "auto_updates": False,
            "notification_email": "user@example.com",
            "advanced_features": True,
            "setup_complete": True
        }