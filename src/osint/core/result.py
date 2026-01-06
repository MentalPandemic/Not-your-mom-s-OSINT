"""Result data structures for OSINT findings."""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd


@dataclass
class Result:
    """Represents a single OSINT finding."""
    
    source: str
    query: str
    url: str
    found: bool
    username: Optional[str] = None
    email: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    confidence: float = 0.0
    
    def __post_init__(self):
        """Initialize timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.additional_data is None:
            self.additional_data = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        data = asdict(self)
        if self.timestamp:
            data['timestamp'] = self.timestamp.isoformat()
        return data
    
    def to_json(self) -> str:
        """Convert result to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class ResultSet:
    """Collection of OSINT results with export capabilities."""
    
    def __init__(self, results: Optional[List[Result]] = None):
        """Initialize result set."""
        self.results = results if results is not None else []
        self.generated_at = datetime.utcnow()
    
    def add_result(self, result: Result):
        """Add a result to the set."""
        self.results.append(result)
    
    def add_results(self, results: List[Result]):
        """Add multiple results to the set."""
        self.results.extend(results)
    
    def get_found(self) -> List[Result]:
        """Get only results where something was found."""
        return [r for r in self.results if r.found]
    
    def get_by_source(self, source: str) -> List[Result]:
        """Get results from a specific source."""
        return [r for r in self.results if r.source == source]
    
    def get_by_query(self, query: str) -> List[Result]:
        """Get results for a specific query."""
        return [r for r in self.results if r.query == query]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result set to dictionary."""
        return {
            "generated_at": self.generated_at.isoformat(),
            "total_results": len(self.results),
            "found_results": len(self.get_found()),
            "results": [r.to_dict() for r in self.results]
        }
    
    def to_json(self) -> str:
        """Convert result set to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert result set to pandas DataFrame."""
        if not self.results:
            return pd.DataFrame()
        
        data = []
        for result in self.results:
            row = {
                "source": result.source,
                "query": result.query,
                "url": result.url,
                "found": result.found,
                "username": result.username,
                "email": result.email,
                "confidence": result.confidence,
                "timestamp": result.timestamp.isoformat() if result.timestamp else None
            }
            
            # Flatten additional data
            if result.additional_data:
                for key, value in result.additional_data.items():
                    row[f"additional_{key}"] = str(value)
            
            data.append(row)
        
        return pd.DataFrame(data)
    
    def export_json(self, filepath: str):
        """Export results to JSON file."""
        with open(filepath, 'w') as f:
            f.write(self.to_json())
    
    def export_csv(self, filepath: str):
        """Export results to CSV file."""
        df = self.to_dataframe()
        df.to_csv(filepath, index=False)
    
    def __len__(self) -> int:
        """Return number of results."""
        return len(self.results)
    
    def __iter__(self):
        """Iterate over results."""
        return iter(self.results)
    
    def __getitem__(self, index: int) -> Result:
        """Get result by index."""
        return self.results[index]