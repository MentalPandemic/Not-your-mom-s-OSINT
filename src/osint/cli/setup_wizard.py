"""Interactive setup wizard for Not-your-mom's-OSINT."""

from __future__ import annotations

from typing import Any

import click

from osint.utils.config_manager import read_config, resolve_config_path, update_config, validate_email


def display_welcome() -> None:
    click.echo()
    click.echo("=" * 70)
    click.echo(" " * 15 + "Not-your-mom's-OSINT Setup Wizard")
    click.echo("=" * 70)
    click.echo()
    click.echo("Welcome! This wizard will help you configure your OSINT platform.")
    click.echo("You can re-run this wizard anytime with: osint setup")
    click.echo()


def prompt_output_format(current: str) -> str:
    click.echo("What is your preferred output format?")
    click.echo("(1) JSON")
    click.echo("(2) CSV")
    click.echo("(3) Both")

    default_choice = {"json": "1", "csv": "2", "both": "3"}.get(current, "1")

    choice = click.prompt(
        "Enter choice [1/2/3]",
        type=click.Choice(["1", "2", "3"], case_sensitive=False),
        default=default_choice,
        show_default=False,
        show_choices=False,
    )

    return {"1": "json", "2": "csv", "3": "both"}[choice]


def _confirm(prompt: str, default: bool) -> bool:
    return click.confirm(prompt, default=default, prompt_suffix=" (y/n): ", show_default=False)


def prompt_verbose_logging(current: bool) -> bool:
    return _confirm("Would you like to enable verbose logging?", default=current)


def prompt_results_path(current: str) -> str:
    click.echo("Please enter the path where results should be saved:")
    click.echo("(Default: ./results)")

    path = click.prompt(
        "Enter path [./results]",
        type=str,
        default=current or "./results",
        show_default=False,
    ).strip()

    if not path:
        return "./results"

    return path


def prompt_sherlock_integration(current: bool) -> bool:
    return _confirm(
        "Do you want to integrate Sherlock for username enumeration?",
        default=current,
    )


def _normalize_api_keys(api_keys: dict[str, str] | None) -> dict[str, str]:
    base = {"twitter": "", "facebook": "", "linkedin": "", "instagram": ""}
    if api_keys:
        base.update({k: str(v) for k, v in api_keys.items() if k in base})
    return base


def prompt_social_media_api_keys(existing: dict[str, str] | None) -> dict[str, str]:
    existing_keys = _normalize_api_keys(existing)

    configure = _confirm("Would you like to configure social media API keys now?", default=False)
    if not configure:
        return existing_keys

    click.echo()
    click.echo("(Press Enter to skip individual APIs)")

    platforms = [
        ("twitter", "Twitter/X"),
        ("facebook", "Facebook"),
        ("linkedin", "LinkedIn"),
        ("instagram", "Instagram"),
    ]

    updated = dict(existing_keys)
    for key, name in platforms:
        value = click.prompt(f"{name} API key", type=str, default="", show_default=False).strip()
        if value:
            updated[key] = value

    return updated


def prompt_twitter_config(existing: dict[str, Any] | None) -> dict[str, Any]:
    """Prompt for Twitter-specific configuration."""
    existing = existing or {}
    click.echo("\nTwitter/X Configuration:")

    configure = _confirm("Configure Twitter API now?", default=bool(existing.get("enabled")))
    if not configure:
        return {"enabled": False}

    bearer_token = click.prompt(
        "Bearer Token",
        type=str,
        default=existing.get("bearer_token", ""),
        show_default=False,
    ).strip()

    return {
        "enabled": bool(bearer_token),
        "bearer_token": bearer_token,
        "api_version": "v2",
        "rate_limit": 450,
    }


def prompt_facebook_config(existing: dict[str, Any] | None) -> dict[str, Any]:
    """Prompt for Facebook-specific configuration."""
    existing = existing or {}
    click.echo("\nFacebook Configuration:")

    configure = _confirm("Configure Facebook API now?", default=bool(existing.get("enabled")))
    if not configure:
        return {"enabled": False}

    access_token = click.prompt(
        "Access Token",
        type=str,
        default=existing.get("access_token", ""),
        show_default=False,
    ).strip()

    return {
        "enabled": bool(access_token),
        "access_token": access_token,
        "rate_limit": 200,
    }


def prompt_linkedin_config(existing: dict[str, Any] | None) -> dict[str, Any]:
    """Prompt for LinkedIn-specific configuration."""
    existing = existing or {}
    click.echo("\nLinkedIn Configuration:")

    configure = _confirm("Configure LinkedIn API now?", default=bool(existing.get("enabled")))
    if not configure:
        return {"enabled": False}

    username = click.prompt(
        "LinkedIn Username",
        type=str,
        default=existing.get("username", ""),
        show_default=False,
    ).strip()

    password = click.prompt(
        "LinkedIn Password",
        type=str,
        default=existing.get("password", ""),
        show_default=False,
        hide_input=True,
    ).strip()

    return {
        "enabled": bool(username and password),
        "username": username,
        "password": password,
        "rate_limit": 100,
    }


def prompt_instagram_config(existing: dict[str, Any] | None) -> dict[str, Any]:
    """Prompt for Instagram-specific configuration."""
    existing = existing or {}
    click.echo("\nInstagram Configuration:")

    configure = _confirm("Configure Instagram API now?", default=bool(existing.get("enabled")))
    if not configure:
        return {"enabled": False}

    session_id = click.prompt(
        "Session ID (recommended) or Username",
        type=str,
        default=existing.get("session_id", ""),
        show_default=False,
    ).strip()

    if session_id and len(session_id) > 50:
        return {
            "enabled": True,
            "session_id": session_id,
            "rate_limit": 200,
        }

    username = click.prompt(
        "Username",
        type=str,
        default=existing.get("username", ""),
        show_default=False,
    ).strip()

    password = click.prompt(
        "Password",
        type=str,
        default=existing.get("password", ""),
        show_default=False,
        hide_input=True,
    ).strip()

    return {
        "enabled": bool(username and password),
        "username": username,
        "password": password,
        "rate_limit": 200,
    }


def prompt_social_media_config(existing: dict[str, dict[str, Any]] | None) -> dict[str, dict[str, Any]]:
    """Prompt for comprehensive social media configuration."""
    configure = _confirm("Would you like to configure social media APIs now?", default=False)
    if not configure:
        return existing or {}

    existing = existing or {}

    return {
        "twitter": prompt_twitter_config(existing.get("twitter")),
        "facebook": prompt_facebook_config(existing.get("facebook")),
        "linkedin": prompt_linkedin_config(existing.get("linkedin")),
        "instagram": prompt_instagram_config(existing.get("instagram")),
    }


def prompt_caching_config(existing: dict[str, Any] | None) -> dict[str, Any]:
    """Prompt for caching configuration."""
    existing = existing or {}
    click.echo("\nCaching Configuration:")

    enabled = _confirm("Enable response caching?", default=existing.get("enabled", True))

    backend = "file"
    if enabled:
        backend = click.prompt(
            "Cache backend",
            type=click.Choice(["file"], case_sensitive=False),
            default="file",
            show_default=False,
        )

    return {
        "enabled": enabled,
        "backend": backend,
        "ttl": {
            "profile": 86400,
            "posts": 604800,
            "followers": 86400,
        },
    }


def prompt_auto_updates(current: bool) -> bool:
    return _confirm("Would you like to enable automatic updates for OSINT sources?", default=current)


def prompt_notification_email(existing: str) -> str:
    click.echo("Please enter your email address for notifications (optional):")
    click.echo("(Press Enter to skip)")

    while True:
        raw = click.prompt("Enter email", type=str, default="", show_default=False)
        raw = raw.strip()

        if not raw:
            return existing

        try:
            return validate_email(raw)
        except ValueError as e:
            click.echo(f"Error: {e}", err=True)


def prompt_advanced_features(current: bool) -> bool:
    return _confirm("Enable advanced correlation engine features?", default=current)


def _mask_set(value: str) -> str:
    return "set" if value else "not set"


def display_completion(config: dict[str, Any]) -> None:
    config_path = resolve_config_path()

    click.echo()
    click.echo("=" * 70)
    click.echo(" " * 20 + "Setup Complete!")
    click.echo("=" * 70)
    click.echo()
    click.echo(f"Saved configuration to: {config_path}")
    click.echo()

    click.echo("Configuration Summary:")
    click.echo(f"  • Output Format: {str(config.get('output_format', 'json')).upper()}")
    click.echo(
        f"  • Verbose Logging: {'Enabled' if config.get('verbose_logging') else 'Disabled'}"
    )
    click.echo(f"  • Results Path: {config.get('results_path', './results')}")
    click.echo(
        f"  • Sherlock Integration: {'Enabled' if config.get('sherlock_enabled') else 'Disabled'}"
    )

    api_keys = config.get("api_keys") or {}
    click.echo(
        "  • Social Media API Keys: "
        f"twitter={_mask_set(str(api_keys.get('twitter', '')))}, "
        f"facebook={_mask_set(str(api_keys.get('facebook', '')))}, "
        f"linkedin={_mask_set(str(api_keys.get('linkedin', '')))}, "
        f"instagram={_mask_set(str(api_keys.get('instagram', '')))}"
    )

    click.echo(f"  • Auto-Updates: {'Enabled' if config.get('auto_updates') else 'Disabled'}")

    email = str(config.get("notification_email") or "")
    if email:
        click.echo(f"  • Notification Email: {email}")

    click.echo(
        f"  • Advanced Features: {'Enabled' if config.get('advanced_features') else 'Disabled'}"
    )

    click.echo()
    click.echo("Next Steps:")
    click.echo("  • View your configuration: osint config --show")
    click.echo("  • Re-run setup wizard: osint setup")
    click.echo("  • Run without the wizard: osint --skip-setup")
    click.echo()


def run_setup_wizard() -> dict[str, Any]:
    display_welcome()

    config = read_config()

    config["output_format"] = prompt_output_format(str(config.get("output_format") or "json"))
    click.echo()

    config["verbose_logging"] = prompt_verbose_logging(bool(config.get("verbose_logging")))
    click.echo()

    config["results_path"] = prompt_results_path(str(config.get("results_path") or "./results"))
    click.echo()

    config["sherlock_enabled"] = prompt_sherlock_integration(bool(config.get("sherlock_enabled")))
    click.echo()

    config["api_keys"] = prompt_social_media_api_keys(config.get("api_keys"))
    click.echo()

    config["social_media"] = prompt_social_media_config(config.get("social_media"))
    click.echo()

    config["caching"] = prompt_caching_config(config.get("caching"))
    click.echo()

    config["auto_updates"] = prompt_auto_updates(bool(config.get("auto_updates", True)))
    click.echo()

    config["notification_email"] = prompt_notification_email(str(config.get("notification_email") or ""))
    click.echo()

    config["advanced_features"] = prompt_advanced_features(bool(config.get("advanced_features")))
    click.echo()

    config["setup_complete"] = True

    final_config = update_config(config)

    display_completion(final_config)

    return final_config
