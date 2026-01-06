"""Core aggregation engine for OSINT data collection."""

from typing import Optional

import pandas as pd

from osint.core.result import SearchResult, CorrelationResult
from osint.sources.base import BaseSource


class Aggregator:
    """Main class that orchestrates queries across multiple OSINT sources."""

    def __init__(self) -> None:
        """Initialize the Aggregator with an empty list of sources."""
        self.sources: list[BaseSource] = []

    def add_source(self, source: BaseSource) -> None:
        """Add a data source to the aggregator.

        Args:
            source: An instance of a class implementing BaseSource
        """
        self.sources.append(source)

    def remove_source(self, source: BaseSource) -> None:
        """Remove a data source from the aggregator.

        Args:
            source: The source instance to remove
        """
        if source in self.sources:
            self.sources.remove(source)

    def search_username(self, username: str) -> list[SearchResult]:
        """Search for a username across all registered sources.

        Args:
            username: The username to search for

        Returns:
            List of SearchResult objects from all sources
        """
        all_results: list[SearchResult] = []

        for source in self.sources:
            try:
                results = source.search_username(username)
                all_results.extend(results)
            except Exception as e:
                print(f"Error querying {source.__class__.__name__}: {e}")

        return all_results

    def correlate_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Correlate findings from a dataset to identify patterns.

        Args:
            data: DataFrame containing OSINT data to analyze

        Returns:
            DataFrame with correlation results
        """
        if data.empty:
            return pd.DataFrame()

        correlations = []

        # Simple correlation: find duplicate values across columns
        for col in data.columns:
            if data[col].dtype == "object":
                value_counts = data[col].value_counts()
                for value, count in value_counts.items():
                    if count > 1 and pd.notna(value):
                        matching_rows = data[data[col] == value].index.tolist()
                        correlations.append(
                            {
                                "field": col,
                                "value": str(value),
                                "occurrences": count,
                                "rows": matching_rows,
                            }
                        )

        if correlations:
            return pd.DataFrame(correlations)
        else:
            return pd.DataFrame(columns=["field", "value", "occurrences", "rows"])

    def get_active_sources(self) -> list[str]:
        """Get list of currently registered source names.

        Returns:
            List of source class names
        """
        return [source.__class__.__name__ for source in self.sources]

    def clear_sources(self) -> None:
        """Remove all registered sources."""
        self.sources.clear()
