# Not-your-mom's-OSINT

Comprehensive open-source intelligence aggregation platform for highlighting relationships between disparate data points.

## Overview

Not-your-mom's-OSINT is a powerful OSINT aggregation tool that consolidates data from multiple sources to identify connections and relationships between pieces of information. The platform provides a unified interface for querying various OSINT sources and correlating findings.

## Features

- **Multi-source aggregation**: Query multiple OSINT sources simultaneously
- **Correlation engine**: Identify relationships between disparate data points
- **Flexible export**: Export results in CSV or JSON formats
- **Extensible architecture**: Easy to add new data sources
- **Sherlock integration**: Built-in username enumeration across social platforms

## Installation

### Requirements

- Python 3.9 or higher
- pip (Python package installer)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd Not-your-mom-s-OSINT
```

2. Install the package in development mode:
```bash
pip install -e .
```

3. Install development dependencies (optional):
```bash
pip install -e ".[dev]"
```

### Alternative: Install from requirements.txt

```bash
pip install -r requirements.txt
pip install -e .
```

## Usage

### Command Line Interface

After installation, you can use the `osint` command:

```bash
# Show all available commands
osint --help

# Search for a username across all configured sources
osint search --username john_doe

# Correlate findings from a data file
osint correlate --data findings.json

# Export results in CSV format
osint export --format csv

# Export results in JSON format
osint export --format json
```

### Programmatic Usage

```python
from osint import Aggregator, ResultSet

# Initialize the aggregator
agg = Aggregator()

# Search for a username
results = agg.search_username("john_doe")

# Export results
results.export_csv("output.csv")
results.export_json("output.json")
```

## Project Structure

```
Not-your-mom-s-OSINT/
├── src/osint/
│   ├── __init__.py
│   ├── __main__.py              # CLI entry point
│   ├── cli/
│   │   └── commands.py          # CLI command definitions
│   ├── core/
│   │   ├── aggregator.py        # Core aggregation engine
│   │   └── result.py            # Result data structures
│   ├── sources/
│   │   ├── base.py              # Abstract base class for sources
│   │   └── sherlock_source.py   # Sherlock integration
│   └── utils/
│       └── config.py            # Configuration utilities
├── tests/                       # Test suite
├── pyproject.toml              # Project configuration
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

## Development

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage report
pytest tests/ --cov=src/osint --cov-report=term-missing

# Run specific test file
pytest tests/test_basic.py
```

### Code Style

This project follows PEP 8 standards. Use the following tools to ensure code quality:

```bash
# Format code
black src/ tests/

# Check for style issues
flake8 src/ tests/
```

### Adding New Sources

1. Create a new source class inheriting from `SourceBase`
2. Implement required methods: `search_username()`, `search_email()`, etc.
3. Register the source in the aggregator

Example:
```python
from osint.sources.base import SourceBase
from osint.core.result import Result

class MyCustomSource(SourceBase):
    def search_username(self, username: str) -> Result:
        # Implementation here
        pass
```

## Configuration

Configuration files are stored in the user's home directory:
- Linux/macOS: `~/.config/osint/`
- Windows: `%APPDATA%\osint\`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational and authorized security research purposes only. Users are responsible for complying with all applicable laws and regulations. Always obtain proper authorization before scanning or investigating targets.