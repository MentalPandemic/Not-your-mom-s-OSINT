"""
Not-your-mom's-OSINT: Comprehensive open-source intelligence aggregation platform.

A tool for aggregating OSINT data from multiple sources and highlighting
relationships between disparate data points.
"""

__version__ = "0.1.0"
__author__ = "OSINT Team"
__description__ = "Comprehensive open-source intelligence aggregation platform"

from .core.aggregator import Aggregator
from .core.result import Result, ResultSet

__all__ = ["Aggregator", "Result", "ResultSet"]