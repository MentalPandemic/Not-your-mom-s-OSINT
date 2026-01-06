"""Sources module for OSINT data collection."""

from osint.sources.base import BaseSource
from osint.sources.sherlock_source import SherlockSource

__all__ = ["BaseSource", "SherlockSource"]
