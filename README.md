# Not-your-mom's OSINT

A comprehensive open-source intelligence aggregation platform that helps you discover relationships between disparate data points across multiple sources.

## Features

- **Username Enumeration**: Search for usernames across multiple platforms using Sherlock integration
- **Data Correlation**: Analyze and correlate findings to reveal hidden connections
- **Flexible Export**: Export results in CSV or JSON formats for further analysis
- **Extensible Architecture**: Easily add new data sources with plugin-based architecture
- **CLI Interface**: Powerful command-line interface for batch processing and automation

## Installation

### Prerequisites

- Python 3.9 or higher

### Install from source

```bash
# Clone the repository
git clone https://github.com/yourusername/not-your-moms-osint.git
cd not-your-moms-osint

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package in development mode
pip install -e .

# Install development dependencies (optional)
pip install -e ".[dev]"
```

### Install dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Command Line Interface

The `osint` command provides access to all functionality:

```bash
# Show help
osint --help

# Search for a username across multiple sources
osint search --username johndoe

# Correlate findings from a data file
osint correlate --data results.csv

# Export results in different formats
osint export --format json --output results.json
osint export --format csv --output results.csv
```

### Python API

```python
from osint.core.aggregator import Aggregator
from osint.sources.sherlock_source import SherlockSource

# Initialize the aggregator with sources
aggregator = Aggregator()
aggregator.add_source(SherlockSource())

# Perform a search
results = aggregator.search_username("johndoe")

# Process results
for result in results:
    print(f"Found on {result.source}: {result.url}")
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=osint

# Run tests with coverage report
pytest --cov=osint --cov-report=html
```

### Code Quality

```bash
# Format code with Black
black src/ tests/

# Lint with Flake8
flake8 src/ tests/

# Type check with MyPy
mypy src/
```

## Project Structure

```
not-your-moms-osint/
├── src/
│   └── osint/
│       ├── __init__.py
│       ├── __main__.py          # CLI entry point
│       ├── cli/
│       │   └── commands.py      # CLI command definitions
│       ├── core/
│       │   ├── aggregator.py    # Core aggregation engine
│       │   └── result.py        # Result data structures
│       ├── sources/
│       │   ├── base.py          # Abstract base class for sources
│       │   └── sherlock_source.py  # Sherlock integration
│       └── utils/
│           └── config.py        # Configuration utilities
├── tests/
│   └── test_basic.py            # Basic tests
├── pyproject.toml               # Project configuration
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built on top of [Sherlock Project](https://github.com/sherlock-project/sherlock) for username enumeration
- Inspired by the need for better OSINT correlation tools

## Roadmap

- [ ] Add more data sources (social media, public records, etc.)
- [ ] Implement advanced correlation algorithms
- [ ] Add web UI for interactive exploration
- [ ] Support for batch processing and automation
- [ ] Integration with threat intelligence feeds
