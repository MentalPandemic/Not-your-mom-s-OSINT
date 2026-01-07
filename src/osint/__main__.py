"""
Main entry point for Not-your-mom's-OSINT CLI.
"""

import sys
from pathlib import Path

# Add src to Python path for imports
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from osint.cli import cli


if __name__ == '__main__':
    cli()