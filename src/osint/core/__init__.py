"""Core module for OSINT aggregation."""

from osint.core.aggregator import Aggregator
from osint.core.result import CorrelationResult, SearchResult

__all__ = ["Aggregator", "SearchResult", "CorrelationResult"]
