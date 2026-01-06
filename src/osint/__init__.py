"""
Not Your Mom's OSINT

A comprehensive OSINT aggregation platform for highlighting relationships 
between disparate data points.
"""

__version__ = "0.1.0"
__author__ = "OSINT Platform Development"
__email__ = "osint@example.com"

from .core.aggregator import OSINTAggregator
from .core.result import OSINTResult, SearchResult

__all__ = ["OSINTAggregator", "OSINTResult", "SearchResult"]
