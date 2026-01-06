"""Not-your-mom's OSINT - A comprehensive OSINT aggregation platform."""

__version__ = "0.1.0"
__author__ = "Not-your-mom's OSINT Team"

from osint.core.aggregator import Aggregator
from osint.core.result import SearchResult, CorrelationResult

__all__ = [
    "Aggregator",
    "SearchResult",
    "CorrelationResult",
    "__version__",
]
