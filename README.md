# Not-your-mom's-OSINT

A comprehensive open-source intelligence (OSINT) aggregation platform that highlights relationships between disparate data points.

## Features

- **Interactive Setup Wizard**: First-time users are guided through configuration
- **Flexible Output Formats**: Support for JSON, CSV, or both
- **Modular Architecture**: Easily extensible with new OSINT sources
- **Sherlock Integration**: Username enumeration capabilities
- **Social Media API Integration**: Twitter, Facebook, LinkedIn, Instagram support
- **Automated Updates**: Keep OSINT sources current
- **Notification System**: Email alerts for completed investigations
- **Advanced Correlation Engine**: Sophisticated data relationship analysis

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd not-your-moms-osint

# Install dependencies
pip install -r requirements.txt
```

### First Run

The first time you run the platform, you'll be guided through an interactive setup wizard:

```bash
# Run the OSINT platform (will trigger setup wizard on first run)
./osint
```

Or run the setup wizard explicitly:

```bash
./osint setup
```

### Configuration Management

View current configuration:
```bash
./osint config --show
```

Reset configuration to defaults:
```bash
./osint config --reset
```

Skip setup wizard (for automation):
```bash
./osint --skip-setup
```

## Setup Wizard

The interactive setup wizard guides you through:

1. **Welcome Message** - Platform introduction
2. **Output Format** - Choose JSON, CSV, or both
3. **Verbose Logging** - Enable detailed logging
4. **Results Path** - Specify where to save results
5. **Sherlock Integration** - Enable username enumeration
6. **Social Media APIs** - Configure API keys (optional)
   - Twitter/X API
   - Facebook API
   - LinkedIn API
   - Instagram API
7. **Auto-Updates** - Enable automatic source updates
8. **Notifications** - Set email for alerts (optional)
9. **Advanced Features** - Enable correlation engine
10. **Completion Summary** - Review your configuration

### Configuration File

Configuration is stored in `~/.osint_config.json` or `./osint_config.json`:

```json
{
  "output_format": "json",
  "verbose_logging": false,
  "results_path": "./results",
  "sherlock_enabled": false,
  "api_keys": {
    "twitter": "",
    "facebook": "",
    "linkedin": "",
    "instagram": ""
  },
  "auto_updates": false,
  "notification_email": "",
  "advanced_features": false,
  "setup_complete": true
}
```

## Project Structure

```
not-your-moms-osint/
├── src/osint/
│   ├── cli/                   # CLI interface and commands
│   │   ├── __init__.py       # Main CLI entry point
│   │   └── setup_wizard.py   # Interactive setup wizard
│   ├── utils/                 # Utility modules
│   │   ├── config.py         # Configuration utilities
│   │   ├── config_manager.py # Configuration file management
│   │   └── __init__.py
│   ├── core/                 # Core OSINT functionality
│   │   └── __init__.py
│   ├── __init__.py
│   └── __main__.py           # Module entry point
├── tests/                     # Test suite
│   ├── unit/                 # Unit tests
│   │   ├── test_cli.py
│   │   ├── test_config_manager.py
│   │   └── test_setup_wizard.py
│   └── integration/          # Integration tests
│       └── test_setup_workflow.py
├── requirements.txt           # Python dependencies
├── osint                      # Main executable script
└── README.md
```

## Development

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=src/osint

# Run specific test file
python -m pytest tests/unit/test_setup_wizard.py
```

### Adding New OSINT Sources

The platform is designed to be easily extensible. Add new sources by:

1. Creating source modules in `src/osint/core/`
2. Implementing the standard interface
3. Adding configuration options to the setup wizard
4. Writing tests for the new functionality

### Configuration Validation

All configuration values are validated for:
- Email format validation
- Path validation and creation
- API key format checking
- Boolean value validation
- Required field presence

## Usage Examples

### Basic OSINT Investigation

```bash
# Run with default configuration
./osint

# Run with verbose logging
./osint --verbose

# Run specific investigation module
./osint investigate --target "example.com"
```

### Configuration Management

```bash
# Show current configuration
./osint config --show

# Show configuration file location
./osint config --path

# Reset to default configuration
./osint config --reset

# Re-run setup wizard
./osint setup
```

## Security Considerations

- API keys are stored securely in configuration files
- No sensitive data is logged
- Configuration files should be protected with appropriate file permissions
- Consider using environment variables for sensitive configuration in production

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## Support

For issues and questions:
- Create an issue on GitHub
- Check existing documentation
- Review test cases for usage examples