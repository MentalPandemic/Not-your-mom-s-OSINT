"""
Core OSINT aggregation engine.

This module provides the main orchestration class that coordinates queries across multiple OSINT sources.
"""

from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from osint.core.result import OSINTResult, SearchResult
from osint.sources.base import BaseSource


class OSINTAggregator:
    """
    Main orchestration class for OSINT operations.
    
    This class coordinates queries across multiple OSINT sources and aggregates results.
    """
    
    def __init__(self, max_workers: int = 5):
        """
        Initialize the OSINT aggregator.
        
        Args:
            max_workers: Maximum number of concurrent workers for parallel queries
        """
        self._sources: List[BaseSource] = []
        self._max_workers = max_workers
    
    def add_source(self, source: BaseSource) -> None:
        """
        Add an OSINT source to the aggregator.
        
        Args:
            source: Source instance to add
        """
        if not isinstance(source, BaseSource):
            raise TypeError("Source must be an instance of BaseSource")
        self._sources.append(source)
    
    def remove_source(self, source: BaseSource) -> None:
        """
        Remove an OSINT source from the aggregator.
        
        Args:
            source: Source instance to remove
        """
        if source in self._sources:
            self._sources.remove(source)
    
    @property
    def sources(self) -> List[BaseSource]:
        """Get list of registered sources."""
        return self._sources.copy()
    
    def search_username(self, username: str, parallel: bool = True) -> OSINTResult:
        """
        Search for a username across all registered sources.
        
        Args:
            username: Username to search for
            parallel: Whether to search sources in parallel
            
        Returns:
            Aggregated OSINTResult containing all findings
        """
        result = OSINTResult(query=username, query_type="username")
        
        if not self._sources:
            result.metadata["warning"] = "No sources registered"
            return result
        
        if parallel:
            self._search_parallel(username, result)
        else:
            self._search_sequential(username, result)
        
        result.metadata["search_method"] = "parallel" if parallel else "sequential"
        return result
    
    def _search_parallel(self, username: str, result: OSINTResult) -> None:
        """Search sources in parallel using thread pool."""
        with ThreadPoolExecutor(max_workers=min(self._max_workers, len(self._sources))) as executor:
            # Submit all search tasks
            future_to_source = {
                executor.submit(source.search_username, username): source 
                for source in self._sources
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    search_results = future.result()
                    for search_result in search_results:
                        result.add_result(search_result)
                except Exception as e:
                    result.metadata.setdefault("errors", []).append({
                        "source": source.name,
                        "error": str(e)
                    })
    
    def _search_sequential(self, username: str, result: OSINTResult) -> None:
        """Search sources sequentially."""
        for source in self._sources:
            try:
                search_results = source.search_username(username)
                for search_result in search_results:
                    result.add_result(search_result)
            except Exception as e:
                result.metadata.setdefault("errors", []).append({
                    "source": source.name,
                    "error": str(e)
                })
    
    def correlate_findings(self, data: List[Dict[str, Any]]) -> OSINTResult:
        """
        Correlate findings from OSINT data.
        
        Args:
            data: List of findings to correlate
            
        Returns:
            OSINTResult with correlated information
        """
        result = OSINTResult(query="correlation", query_type="correlation")
        
        # Basic correlation logic - can be extended
        platforms = {}
        
        for finding in data:
            platform = finding.get("platform", "unknown")
            username = finding.get("username", "")
            
            if platform not in platforms:
                platforms[platform] = []
            
            if username:
                platforms[platform].append(username)
        
        # Create correlation results
        for platform, usernames in platforms.items():
            correlation_result = SearchResult(
                platform=platform,
                username=", ".join(set(usernames)) if usernames else "unknown",
                url="",
                found=True,
                additional_data={
                    "user_count": len(set(usernames)),
                    "all_usernames": list(set(usernames)),
                    "source": "correlation"
                }
            )
            result.add_result(correlation_result)
        
        result.metadata["total_platforms"] = len(platforms)
        result.metadata["correlated_entries"] = len(data)
        
        return result
    
    def export_results(self, result: OSINTResult, filepath: str, format: str = "json") -> None:
        """
        Export OSINT results to a file.
        
        Args:
            result: OSINTResult to export
            filepath: Path to output file
            format: Export format ("json" or "csv")
        """
        if format.lower() == "json":
            with open(filepath, "w") as f:
                json.dump(result.to_dict(), f, indent=2)
        elif format.lower() == "csv":
            import csv
            
            found_accounts = result.get_found_accounts()
            if not found_accounts:
                return
            
            # Get all fieldnames
            fieldnames = ["platform", "username", "url", "found", "timestamp"]
            additional_keys = set()
            
            for account in found_accounts:
                if account.additional_data:
                    additional_keys.update(account.additional_data.keys())
            
            fieldnames.extend(additional_keys)
            
            with open(filepath, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for account in found_accounts:
                    row = account.to_dict()
                    # Flatten additional_data into the row
                    if "additional_data" in row:
                        row.update(row.pop("additional_data"))
                    writer.writerow(row)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def get_source_by_name(self, name: str) -> Optional[BaseSource]:
        """
        Get a source by its name.
        
        Args:
            name: Name of the source to find
            
        Returns:
            Source instance if found, None otherwise
        """
        for source in self._sources:
            if source.name.lower() == name.lower():
                return source
        return None
