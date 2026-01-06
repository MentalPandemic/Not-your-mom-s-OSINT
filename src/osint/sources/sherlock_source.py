"""Sherlock integration for username enumeration across social platforms.

This module provides an interface to the Sherlock tool for searching usernames
across multiple social networks and websites.

Note: This is a mock implementation for demonstration purposes. In production,
this would integrate with the actual Sherlock tool or implement similar functionality.
"""

import json
import random
from typing import Dict, Any
from .base import SourceBase
from ..core.result import Result


class SherlockSource(SourceBase):
    """Sherlock-based username search implementation."""
    
    def __init__(self, enabled: bool = True):
        """Initialize Sherlock source.
        
        Args:
            enabled: Whether this source is enabled
        """
        super().__init__("sherlock", enabled)
        
        # Mock sites that Sherlock would typically check
        # In production, this would be loaded from Sherlock's data.json
        self.mock_sites = [
            "Twitter", "Instagram", "Facebook", "LinkedIn", "GitHub",
            "Reddit", "YouTube", "TikTok", "Snapchat", "Pinterest",
            "Spotify", "Medium", "DeviantArt", "Steam", "Xbox Live"
        ]
    
    def search_username(self, username: str) -> Result:
        """Search for a username across social platforms.
        
        Args:
            username: Username to search for
            
        Returns:
            Result object containing findings
        """
        if not self.enabled:
            return Result(
                source=self.name,
                query=username,
                url="",
                found=False,
                additional_data={"error": "Source disabled"}
            )
        
        try:
            # Mock the search process
            # In production, this would call Sherlock or implement similar logic
            found_accounts = self._mock_search(username)
            
            if found_accounts:
                # Create a summary of findings
                additional_data = {
                    "total_sites_checked": len(self.mock_sites),
                    "accounts_found": len(found_accounts),
                    "platforms": list(found_accounts.keys())
                }
                
                # Create a representative URL (in production, this would be a real URL)
                sample_platform = list(found_accounts.keys())[0]
                sample_url = found_accounts[sample_platform]
                
                return Result(
                    source=self.name,
                    query=username,
                    url=sample_url,
                    found=True,
                    username=username,
                    additional_data=additional_data,
                    confidence=self._calculate_confidence(len(found_accounts))
                )
            else:
                return Result(
                    source=self.name,
                    query=username,
                    url="",
                    found=False,
                    username=username,
                    additional_data={"total_sites_checked": len(self.mock_sites)}
                )
                
        except Exception as e:
            return Result(
                source=self.name,
                query=username,
                url="",
                found=False,
                additional_data={"error": str(e)}
            )
    
    def search_email(self, email: str) -> Result:
        """Search for an email address.
        
        Note: Sherlock primarily focuses on username searches.
        This method provides a basic implementation.
        
        Args:
            email: Email address to search for
            
        Returns:
            Result object containing findings
        """
        if not self.enabled:
            return Result(
                source=self.name,
                query=email,
                url="",
                found=False,
                additional_data={"error": "Source disabled"}
            )
        
        # Extract username from email (before @)
        username = email.split('@')[0]
        
        # For emails, we can try to search the username portion
        username_result = self.search_username(username)
        
        # Modify the result for email context
        return Result(
            source=self.name,
            query=email,
            url=username_result.url,
            found=username_result.found,
            email=email,
            username=username,
            additional_data=username_result.additional_data,
            confidence=username_result.confidence * 0.7  # Lower confidence for email searches
        )
    
    def _mock_search(self, username: str) -> Dict[str, str]:
        """Mock search function that simulates Sherlock behavior.
        
        In production, this would:
        1. Load site data from Sherlock's data.json
        2. Make HTTP requests to check each site
        3. Parse responses to determine if account exists
        
        Args:
            username: Username to search for
            
        Returns:
            Dictionary of found accounts with platform names as keys and URLs as values
        """
        found_accounts = {}
        
        # Simulate finding accounts on some platforms
        # This is deterministic based on username for consistent testing
        random.seed(hash(username))
        
        # Randomly decide which platforms have this username
        # About 30-40% of platforms will have the username
        for platform in self.mock_sites:
            if random.random() < 0.35:  # 35% chance of finding on each platform
                # Generate a realistic URL based on platform
                url = self._generate_profile_url(platform, username)
                found_accounts[platform] = url
        
        return found_accounts
    
    def _generate_profile_url(self, platform: str, username: str) -> str:
        """Generate a realistic profile URL for a platform.
        
        Args:
            platform: Social platform name
            username: Username to include in URL
            
        Returns:
            Formatted profile URL
        """
        platform_urls = {
            "Twitter": f"https://twitter.com/{username}",
            "Instagram": f"https://instagram.com/{username}",
            "Facebook": f"https://facebook.com/{username}",
            "LinkedIn": f"https://linkedin.com/in/{username}",
            "GitHub": f"https://github.com/{username}",
            "Reddit": f"https://reddit.com/user/{username}",
            "YouTube": f"https://youtube.com/@{username}",
            "TikTok": f"https://tiktok.com/@{username}",
            "Snapchat": f"https://snapchat.com/add/{username}",
            "Pinterest": f"https://pinterest.com/{username}",
            "Spotify": f"https://open.spotify.com/user/{username}",
            "Medium": f"https://medium.com/@{username}",
            "DeviantArt": f"https://{username}.deviantart.com",
            "Steam": f"https://steamcommunity.com/id/{username}",
            "Xbox Live": f"https://xboxgamertag.com/search/{username}"
        }
        
        return platform_urls.get(platform, f"https://example.com/{username}")
    
    def _calculate_confidence(self, accounts_found: int) -> float:
        """Calculate confidence score based on number of accounts found.
        
        Args:
            accounts_found: Number of accounts found
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if accounts_found == 0:
            return 0.0
        elif accounts_found == 1:
            return 0.6
        elif accounts_found <= 3:
            return 0.8
        elif accounts_found <= 5:
            return 0.9
        else:
            return 1.0
    
    def get_supported_platforms(self) -> list:
        """Get list of platforms this source can search."""
        return self.mock_sites.copy()