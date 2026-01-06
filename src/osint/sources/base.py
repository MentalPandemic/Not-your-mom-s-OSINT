"""Abstract base class for OSINT data sources."""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..core.result import Result


class SourceBase(ABC):
    """Abstract base class for all OSINT data sources."""
    
    def __init__(self, name: str, enabled: bool = True):
        """Initialize the source.
        
        Args:
            name: Name of the source
            enabled: Whether this source is enabled
        """
        self.name = name
        self.enabled = enabled
    
    @abstractmethod
    def search_username(self, username: str) -> Result:
        """Search for a username.
        
        Args:
            username: Username to search for
            
        Returns:
            Result object containing findings
        """
        pass
    
    @abstractmethod
    def search_email(self, email: str) -> Result:
        """Search for an email address.
        
        Args:
            email: Email address to search for
            
        Returns:
            Result object containing findings
        """
        pass
    
    def can_search_username(self) -> bool:
        """Check if this source supports username searching."""
        return True
    
    def can_search_email(self) -> bool:
        """Check if this source supports email searching."""
        return True
    
    def is_enabled(self) -> bool:
        """Check if this source is enabled."""
        return self.enabled
    
    def set_enabled(self, enabled: bool):
        """Enable or disable this source."""
        self.enabled = enabled
    
    def get_name(self) -> str:
        """Get the source name."""
        return self.name