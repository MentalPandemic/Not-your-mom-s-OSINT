# Not-your-mom's-OSINT

A comprehensive open-source intelligence aggregation platform aimed at highlighting relationships between disparate data points and showing connections between pieces of information.

## Installation

```bash
pip install -e .
```

For development:
```bash
pip install -e ".[dev]"
```

## Quick Start

On first run, the interactive setup wizard will guide you through initial configuration:

```bash
osint
```

Or explicitly run the setup wizard:

```bash
osint setup
```

## Configuration

### Setup Wizard

The setup wizard will prompt you for:

1. **Output Format** - Choose between JSON, CSV, or both
2. **Verbose Logging** - Enable detailed logging output
3. **Results Path** - Directory where results will be saved (default: ./results)
4. **Sherlock Integration** - Enable username enumeration across platforms
5. **Social Media API Keys** - Configure Twitter/X, Facebook, LinkedIn, and Instagram APIs
6. **Auto-Updates** - Enable automatic updates for OSINT sources
7. **Notification Email** - Optional email address for notifications
8. **Advanced Features** - Enable advanced correlation engine features

### Configuration File

Configuration is stored in JSON format at:
- `~/.osint_config.json` (default)
- `./osint_config.json` (if present in current directory)

Example configuration:
```json
{
  "output_format": "json",
  "verbose_logging": true,
  "results_path": "./results",
  "sherlock_enabled": true,
  "api_keys": {
    "twitter": "your_twitter_api_key",
    "facebook": "",
    "linkedin": "",
    "instagram": ""
  },
  "auto_updates": true,
  "notification_email": "user@example.com",
  "advanced_features": false,
  "setup_complete": true
}
```

### Configuration Commands

View current configuration:
```bash
osint config --show
```

Re-run setup wizard:
```bash
osint setup
```

Reset configuration:
```bash
osint config --reset
```

Skip setup wizard on first run:
```bash
osint --skip-setup
```

## Development

Run tests:
```bash
pytest
```

## Features

- Interactive CLI setup wizard
- Flexible configuration management
- Secure API key storage (file permissions: 600)
- Email validation
- Automatic results directory creation
- Support for multiple output formats

## License

See LICENSE file for details.
