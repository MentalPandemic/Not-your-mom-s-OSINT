"""
Abstract base class for OSINT data sources.

This module provides the base interface that all OSINT sources must implement.
"""

from abc import ABC, abstractmethod
from typing import List

from osint.core.result import SearchResult


class BaseSource(ABC):
    """Abstract base class for all OSINT sources."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of this source."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Get a description of what this source does."""
        pass
    
    @property
    @abstractmethod
    def status(self) -> str:
        """Get the current status of this source."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this source is available for use.
        
        Returns:
            True if the source is available, False otherwise
        """
        pass
    
    @abstractmethod
    def search_username(self, username: str) -> List[SearchResult]:
        """
        Search for a username using this source.
        
        Args:
            username: Username to search for
            
        Returns:
            List of search results
        """
        pass
    
    def search_email(self, email: str) -> List[SearchResult]:
        """
        Search for an email address using this source.
        
        Args:
            email: Email address to search for
            
        Returns:
            List of search results
            
        Note:
            This method is optional for sources that don't support email search.
            Default implementation returns empty list.
        """
        return []
    
    def search_phone(self, phone: str) -> List[SearchResult]:
        """
        Search for a phone number using this source.
        
        Args:
            phone: Phone number to search for
            
        Returns:
            List of search results
            
        Note:
            This method is optional for sources that don't support phone search.
            Default implementation returns empty list.
        """
        return []
