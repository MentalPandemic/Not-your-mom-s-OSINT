"""
Interactive setup wizard for Not-your-mom's-OSINT platform.
Provides guided configuration for first-time users.
"""

import click
import re
from pathlib import Path
from typing import Dict, Any, Optional

from ..utils.config_manager import ConfigManager
from ..utils.config import ensure_config_dir, expand_path


class SetupWizard:
    """Interactive setup wizard for OSINT platform configuration."""
    
    def __init__(self):
        """Initialize the setup wizard."""
        self.config_manager = ConfigManager()
        self.current_config = self.config_manager.create_default_config()
    
    def run_wizard(self) -> bool:
        """Run the complete setup wizard.
        
        Returns:
            True if setup completed successfully, False otherwise.
        """
        try:
            self._display_welcome()
            
            # Collect configuration through interactive prompts
            self._setup_output_format()
            self._setup_verbose_logging()
            self._setup_results_path()
            self._setup_sherlock_integration()
            self._setup_social_media_apis()
            self._setup_auto_updates()
            self._setup_notifications()
            self._setup_advanced_features()
            
            # Validate and save configuration
            if self._validate_and_save():
                self._display_completion()
                return True
            else:
                click.echo("Setup failed. Please try again.", err=True)
                return False
                
        except KeyboardInterrupt:
            click.echo("\n\nSetup cancelled by user.", err=True)
            return False
        except Exception as e:
            click.echo(f"\nSetup failed with error: {e}", err=True)
            return False
    
    def _display_welcome(self):
        """Display welcome message and platform description."""
        click.echo(click.style("=" * 60, fg="blue"))
        click.echo(click.style("Welcome to Not-your-mom's-OSINT!", fg="green", bold=True))
        click.echo(click.style("=" * 60, fg="blue"))
        click.echo()
        click.echo("This setup wizard will guide you through the initial")
        click.echo("configuration of your OSINT platform.")
        click.echo()
        click.echo("You can re-run this setup at any time using:")
        click.echo("  osint setup")
        click.echo()
        if not ensure_config_dir():
            click.echo(click.style("Warning: Could not create config directory", fg="yellow"))
    
    def _setup_output_format(self):
        """Setup preferred output format."""
        click.echo("\n" + "=" * 50)
        click.echo(click.style("Output Format Configuration", fg="cyan"))
        click.echo("=" * 50)
        
        choices = {
            "1": "json",
            "2": "csv", 
            "3": "both"
        }
        
        click.echo("What is your preferred output format?")
        click.echo("(1) JSON")
        click.echo("(2) CSV")
        click.echo("(3) Both")
        
        while True:
            choice = click.prompt("Enter choice [1/2/3]", default="1")
            if choice in choices:
                self.current_config["output_format"] = choices[choice]
                break
            click.echo(click.style("Invalid choice. Please enter 1, 2, or 3.", fg="red"))
    
    def _setup_verbose_logging(self):
        """Setup verbose logging preference."""
        click.echo("\n" + "=" * 50)
        click.echo(click.style("Logging Configuration", fg="cyan"))
        click.echo("=" * 50)
        
        enable_verbose = click.confirm("Would you like to enable verbose logging?", default=False)
        self.current_config["verbose_logging"] = enable_verbose
    
    def _setup_results_path(self):
        """Setup results directory path."""
        click.echo("\n" + "=" * 50)
        click.echo(click.style("Results Path Configuration", fg="cyan"))
        click.echo("=" * 50)
        
        default_path = self.current_config["results_path"]
        click.echo(f"Please enter the path where results should be saved:")
        click.echo(f"(Default: {default_path})")
        
        while True:
            path = click.prompt("Enter path", default=default_path)
            expanded_path = expand_path(path)
            
            # Try to create the directory to validate the path
            try:
                Path(expanded_path).mkdir(parents=True, exist_ok=True)
                self.current_config["results_path"] = expanded_path
                break
            except (OSError, ValueError):
                click.echo(click.style("Invalid path. Please enter a valid directory path.", fg="red"))
    
    def _setup_sherlock_integration(self):
        """Setup Sherlock integration preference."""
        click.echo("\n" + "=" * 50)
        click.echo(click.style("Sherlock Integration", fg="cyan"))
        click.echo("=" * 50)
        
        enable_sherlock = click.confirm("Do you want to integrate Sherlock for username enumeration?", default=False)
        self.current_config["sherlock_enabled"] = enable_sherlock
    
    def _setup_social_media_apis(self):
        """Setup social media API keys."""
        click.echo("\n" + "=" * 50)
        click.echo(click.style("Social Media API Configuration", fg="cyan"))
        click.echo("=" * 50)
        
        configure_apis = click.confirm("Would you like to configure social media API keys now?", default=False)
        
        if configure_apis:
            self._configure_api_keys()
    
    def _configure_api_keys(self):
        """Configure individual social media API keys."""
        platforms = {
            "twitter": "Twitter/X API",
            "facebook": "Facebook API", 
            "linkedin": "LinkedIn API",
            "instagram": "Instagram API"
        }
        
        click.echo("\nConfigure API keys for each platform (press Enter to skip):")
        
        for platform, display_name in platforms.items():
            click.echo(f"\n{display_name}:")
            api_key = click.prompt(f"Enter {display_name} API key", default="", show_default=False)
            self.current_config["api_keys"][platform] = api_key.strip()
    
    def _setup_auto_updates(self):
        """Setup automatic updates preference."""
        click.echo("\n" + "=" * 50)
        click.echo(click.style("Automatic Updates", fg="cyan"))
        click.echo("=" * 50)
        
        enable_updates = click.confirm("Would you like to enable automatic updates for OSINT sources?", default=False)
        self.current_config["auto_updates"] = enable_updates
    
    def _setup_notifications(self):
        """Setup notification email."""
        click.echo("\n" + "=" * 50)
        click.echo(click.style("Notification Configuration", fg="cyan"))
        click.echo("=" * 50)
        
        click.echo("Please enter your email address for notifications (optional):")
        click.echo("(Press Enter to skip)")
        
        while True:
            email = click.prompt("Enter email", default="", show_default=False)
            email = email.strip()
            
            if not email:
                self.current_config["notification_email"] = ""
                break
            elif self._is_valid_email(email):
                self.current_config["notification_email"] = email
                break
            else:
                click.echo(click.style("Invalid email format. Please try again.", fg="red"))
    
    def _setup_advanced_features(self):
        """Setup advanced features preference."""
        click.echo("\n" + "=" * 50)
        click.echo(click.style("Advanced Features", fg="cyan"))
        click.echo("=" * 50)
        
        enable_advanced = click.confirm("Enable advanced correlation engine features?", default=False)
        self.current_config["advanced_features"] = enable_advanced
    
    def _validate_and_save(self) -> bool:
        """Validate configuration and save to file.
        
        Returns:
            True if validation and save were successful.
        """
        is_valid, errors = self.config_manager.validate_config(self.current_config)
        
        if not is_valid:
            click.echo(click.style("Configuration validation failed:", fg="red"))
            for error in errors:
                click.echo(f"  - {error}")
            return False
        
        if not self.config_manager.save_config(self.current_config):
            click.echo(click.style("Failed to save configuration file.", fg="red"))
            return False
        
        # Mark setup as complete
        self.current_config["setup_complete"] = True
        self.config_manager.mark_setup_complete()
        
        return True
    
    def _display_completion(self):
        """Display setup completion summary."""
        click.echo("\n" + "=" * 60)
        click.echo(click.style("Setup Complete!", fg="green", bold=True))
        click.echo("=" * 60)
        click.echo()
        click.echo("Configuration saved successfully!")
        click.echo(f"Config file location: {self.config_manager.get_config_path()}")
        click.echo()
        click.echo("Summary of your configuration:")
        click.echo(f"  • Output format: {self.current_config['output_format']}")
        click.echo(f"  • Verbose logging: {'Enabled' if self.current_config['verbose_logging'] else 'Disabled'}")
        click.echo(f"  • Results path: {self.current_config['results_path']}")
        click.echo(f"  • Sherlock integration: {'Enabled' if self.current_config['sherlock_enabled'] else 'Disabled'}")
        
        api_keys_configured = sum(1 for key in self.current_config['api_keys'].values() if key.strip())
        click.echo(f"  • API keys configured: {api_keys_configured}/4 platforms")
        
        click.echo(f"  • Auto updates: {'Enabled' if self.current_config['auto_updates'] else 'Disabled'}")
        if self.current_config['notification_email']:
            click.echo(f"  • Notification email: {self.current_config['notification_email']}")
        click.echo(f"  • Advanced features: {'Enabled' if self.current_config['advanced_features'] else 'Disabled'}")
        click.echo()
        click.echo("Next steps:")
        click.echo("  • Run 'osint --help' to see available commands")
        click.echo("  • Run 'osint config --show' to view your configuration")
        click.echo("  • Re-run setup with 'osint setup' to modify settings")
        click.echo()
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None


def run_setup_wizard():
    """Entry point for running the setup wizard."""
    wizard = SetupWizard()
    return wizard.run_wizard()


@click.command()
@click.option('--force', '-f', is_flag=True, help='Force setup wizard to run even if already configured')
def setup(force: bool):
    """Run the interactive setup wizard for initial configuration."""
    config_manager = ConfigManager()
    
    if not force and config_manager.is_setup_complete():
        if not click.confirm("Setup has already been completed. Re-run setup wizard?"):
            click.echo("Setup cancelled.")
            return
        
        if not click.confirm("This will overwrite your current configuration. Continue?"):
            click.echo("Setup cancelled.")
            return
    
    success = run_setup_wizard()
    if not success:
        click.get_current_context().exit(1)