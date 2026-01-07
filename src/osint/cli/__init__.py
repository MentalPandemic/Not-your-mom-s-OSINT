"""
Main CLI module for Not-your-mom's-OSINT platform.
"""

import click
import sys
from pathlib import Path
from typing import Optional

from .setup_wizard import setup as setup_command
from ..utils.config_manager import ConfigManager


@click.group(invoke_without_command=True)
@click.option('--version', '-v', is_flag=True, help='Show version and exit')
@click.option('--skip-setup', is_flag=True, help='Skip setup wizard on first run')
@click.pass_context
def cli(ctx, version, skip_setup):
    """Not-your-mom's-OSINT - Comprehensive OSINT aggregation platform."""
    
    # Show version if requested
    if version:
        click.echo("Not-your-mom's-OSINT v1.0.0")
        return
    
    # If no command was invoked, this is the first run
    if ctx.invoked_subcommand is None:
        if not skip_setup:
            # Check if this is first run or setup is incomplete
            config_manager = ConfigManager()
            if not config_manager.is_setup_complete():
                click.echo(click.style("Welcome to Not-your-mom's-OSINT!", fg="green", bold=True))
                click.echo("It looks like this is your first time running the platform.")
                click.echo("Let's get you set up!\n")
                
                if click.confirm("Would you like to run the setup wizard now?", default=True):
                    # Import and run setup wizard
                    from .setup_wizard import run_setup_wizard
                    if not run_setup_wizard():
                        sys.exit(1)
                    click.echo("\nSetup complete! You can now use the platform.")
                else:
                    click.echo("Setup skipped. Run 'osint setup' to configure later.")
                    return
        else:
            click.echo("Setup wizard skipped. Run 'osint setup' to configure the platform.")
            return


# Register subcommands
cli.add_command(setup_command, name='setup')


@cli.command()
@click.option('--show', '-s', is_flag=True, help='Show current configuration')
@click.option('--reset', '-r', is_flag=True, help='Reset configuration to defaults')
@click.option('--path', '-p', is_flag=True, help='Show configuration file path')
def config(show, reset, path):
    """Manage platform configuration."""
    config_manager = ConfigManager()
    
    if path:
        click.echo(f"Configuration file: {config_manager.get_config_path()}")
        return
    
    if reset:
        if click.confirm("This will reset all configuration to defaults. Continue?"):
            default_config = config_manager.create_default_config()
            if config_manager.save_config(default_config):
                click.echo("Configuration reset to defaults.")
            else:
                click.echo(click.style("Failed to reset configuration.", fg="red"))
        else:
            click.echo("Reset cancelled.")
        return
    
    if show:
        config = config_manager.load_config()
        
        click.echo("=" * 50)
        click.echo(click.style("Current Configuration", fg="cyan"))
        click.echo("=" * 50)
        click.echo(f"Config file: {config_manager.get_config_path()}")
        click.echo()
        click.echo(f"Output format: {config['output_format']}")
        click.echo(f"Verbose logging: {'Enabled' if config['verbose_logging'] else 'Disabled'}")
        click.echo(f"Results path: {config['results_path']}")
        click.echo(f"Sherlock integration: {'Enabled' if config['sherlock_enabled'] else 'Disabled'}")
        click.echo()
        
        # Show API keys status (without revealing actual keys)
        click.echo("API Keys configured:")
        for platform, key in config['api_keys'].items():
            status = "✓ Configured" if key else "✗ Not configured"
            click.echo(f"  {platform.title()}: {status}")
        
        click.echo()
        click.echo(f"Auto updates: {'Enabled' if config['auto_updates'] else 'Disabled'}")
        if config['notification_email']:
            click.echo(f"Notification email: {config['notification_email']}")
        click.echo(f"Advanced features: {'Enabled' if config['advanced_features'] else 'Disabled'}")
        click.echo(f"Setup completed: {'Yes' if config['setup_complete'] else 'No'}")
        click.echo()
        
        if not config['setup_complete']:
            click.echo(click.style("Setup incomplete. Run 'osint setup' to complete configuration.", fg="yellow"))
    else:
        click.echo("Configuration commands:")
        click.echo("  osint config --show    - Show current configuration")
        click.echo("  osint config --reset   - Reset to defaults")
        click.echo("  osint config --path    - Show config file path")
        click.echo()
        click.echo("Run 'osint config --show' to view your current configuration.")


if __name__ == '__main__':
    cli()