"""Core modules for OSINT aggregation."""

from .aggregator import Aggregator
from .result import Result, ResultSet

__all__ = ["Aggregator", "Result", "ResultSet"]