"""Main aggregation engine that orchestrates queries across sources."""

import asyncio
from typing import List, Optional, Dict, Any
from .result import Result, ResultSet
from ..sources.base import SourceBase
from ..sources.sherlock_source import SherlockSource
from ..utils.config import get_cached_config, is_source_enabled


class Aggregator:
    """Main class that orchestrates OSINT queries across multiple sources."""
    
    def __init__(self, sources: Optional[List[SourceBase]] = None):
        """Initialize the aggregator.
        
        Args:
            sources: List of sources to use (if None, uses default sources)
        """
        self.sources = sources if sources is not None else self._get_default_sources()
        self.config = get_cached_config()
        
        # Filter sources based on configuration
        self.sources = [
            source for source in self.sources
            if is_source_enabled(self.config, source.get_name())
        ]
    
    def _get_default_sources(self) -> List[SourceBase]:
        """Get default sources based on configuration.
        
        Returns:
            List of enabled source instances
        """
        sources = []
        
        # Sherlock source (enabled by default in config)
        sources.append(SherlockSource())
        
        # Additional sources can be added here
        # sources.append(AnotherSource())
        # sources.append(YetAnotherSource())
        
        return sources
    
    def search_username(self, username: str) -> ResultSet:
        """Search for a username across all enabled sources.
        
        Args:
            username: Username to search for
            
        Returns:
            ResultSet containing all findings
        """
        results = ResultSet()
        
        for source in self.sources:
            try:
                if source.can_search_username():
                    result = source.search_username(username)
                    results.add_result(result)
            except Exception as e:
                # Create error result if source fails
                error_result = Result(
                    source=source.get_name(),
                    query=username,
                    url="",
                    found=False,
                    username=username,
                    additional_data={"error": str(e)}
                )
                results.add_result(error_result)
        
        return results
    
    def search_email(self, email: str) -> ResultSet:
        """Search for an email across all enabled sources.
        
        Args:
            email: Email address to search for
            
        Returns:
            ResultSet containing all findings
        """
        results = ResultSet()
        
        for source in self.sources:
            try:
                if source.can_search_email():
                    result = source.search_email(email)
                    results.add_result(result)
            except Exception as e:
                # Create error result if source fails
                error_result = Result(
                    source=source.get_name(),
                    query=email,
                    url="",
                    found=False,
                    email=email,
                    additional_data={"error": str(e)}
                )
                results.add_result(error_result)
        
        return results
    
    def add_source(self, source: SourceBase):
        """Add a new source to the aggregator.
        
        Args:
            source: Source instance to add
        """
        self.sources.append(source)
    
    def remove_source(self, source_name: str):
        """Remove a source by name.
        
        Args:
            source_name: Name of source to remove
        """
        self.sources = [
            source for source in self.sources
            if source.get_name() != source_name
        ]
    
    def get_sources(self) -> List[SourceBase]:
        """Get all configured sources.
        
        Returns:
            List of source instances
        """
        return self.sources.copy()
    
    def get_source_names(self) -> List[str]:
        """Get names of all configured sources.
        
        Returns:
            List of source names
        """
        return [source.get_name() for source in self.sources]
    
    def correlate_findings(self, data_file: Optional[str] = None) -> ResultSet:
        """Correlate findings to identify relationships.
        
        Args:
            data_file: Optional path to data file to correlate
            
        Returns:
            ResultSet with correlated findings
        """
        # This is a placeholder for correlation functionality
        # In production, this would:
        # 1. Analyze patterns across results
        # 2. Identify common usernames/emails
        # 3. Find temporal patterns
        # 4. Cross-reference with external data
        
        results = ResultSet()
        
        if data_file:
            # Load and correlate data from file
            try:
                correlated_results = self._correlate_from_file(data_file)
                results.add_results(correlated_results)
            except Exception as e:
                error_result = Result(
                    source="correlation",
                    query=data_file,
                    url="",
                    found=False,
                    additional_data={"error": f"Failed to correlate file: {str(e)}"}
                )
                results.add_result(error_result)
        else:
            # Create a mock correlation result
            correlation_result = Result(
                source="correlation",
                query="correlation_analysis",
                url="",
                found=True,
                additional_data={
                    "status": "correlation_engine_active",
                    "features": [
                        "pattern_matching",
                        "temporal_analysis",
                        "cross_referencing"
                    ],
                    "note": "Load data with --data option to perform actual correlation"
                }
            )
            results.add_result(correlation_result)
        
        return results
    
    def _correlate_from_file(self, data_file: str) -> List[Result]:
        """Correlate findings from a data file.
        
        Args:
            data_file: Path to data file
            
        Returns:
            List of correlation results
        """
        # Placeholder for file-based correlation
        # In production, this would:
        # 1. Load data from file (JSON, CSV, etc.)
        # 2. Parse and standardize the data
        # 3. Perform correlation analysis
        # 4. Return findings
        
        return [
            Result(
                source="correlation",
                query=data_file,
                url="",
                found=True,
                additional_data={
                    "correlated_entries": 0,
                    "relationships_found": 0,
                    "status": "file_correlation_not_implemented"
                }
            )
        ]
    
    def export_results(self, results: ResultSet, format: str = "json", filepath: Optional[str] = None) -> str:
        """Export results in specified format.
        
        Args:
            results: ResultSet to export
            format: Export format ("json" or "csv")
            filepath: Optional filepath to save to
            
        Returns:
            Exported data as string
        """
        if format.lower() == "json":
            if filepath:
                results.export_json(filepath)
                return f"Results exported to {filepath}"
            else:
                return results.to_json()
        elif format.lower() == "csv":
            if filepath:
                results.export_csv(filepath)
                return f"Results exported to {filepath}"
            else:
                return results.to_dataframe().to_csv(index=False)
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'json' or 'csv'.")
    
    async def search_username_async(self, username: str) -> ResultSet:
        """Asynchronously search for a username.
        
        Args:
            username: Username to search for
            
        Returns:
            ResultSet containing all findings
        """
        # This would be implemented for concurrent source queries
        # For now, fall back to synchronous implementation
        return self.search_username(username)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get aggregator statistics.
        
        Returns:
            Dictionary with aggregator stats
        """
        return {
            "sources_configured": len(self.sources),
            "sources_enabled": len([s for s in self.sources if s.is_enabled()]),
            "source_names": self.get_source_names(),
            "config_loaded": True
        }