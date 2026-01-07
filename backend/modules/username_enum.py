"""
Username Enumeration Engine - Core Identity Discovery Module

This module provides async concurrent username enumeration across hundreds of platforms,
serving as the foundation for identity enrichment and OSINT discovery.
"""

import asyncio
import aiohttp
import random
import re
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import logging
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """Confidence levels for username matches"""
    HIGH = 3  # Exact match, verified profile
    MEDIUM = 2  # Partial match or unverified
    LOW = 1  # Possible match, uncertain
    NONE = 0  # No match


class PlatformStatus(Enum):
    """Status codes for platform checks"""
    FOUND = "found"
    NOT_FOUND = "not_found"
    TIMEOUT = "timeout"
    ERROR = "error"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


@dataclass
class PlatformResult:
    """Result from checking a single platform"""
    platform: str
    url: str
    status: PlatformStatus
    confidence: ConfidenceLevel
    response_code: Optional[int] = None
    response_time: float = 0.0
    error_message: Optional[str] = None
    profile_data: Dict = field(default_factory=dict)
    discovered_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UsernameMatch:
    """A matched username with metadata"""
    username: str
    platform: str
    profile_url: str
    confidence: ConfidenceLevel
    is_verified: bool = False
    discovery_method: str = "direct"
    additional_info: Dict = field(default_factory=dict)


class UserAgentRotator:
    """Rotates user agents to avoid detection"""

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    ]

    @classmethod
    def get_random(cls) -> str:
        """Get a random user agent"""
        return random.choice(cls.USER_AGENTS)


class UsernameEnumerator:
    """
    Main username enumeration engine with async concurrent platform checking.
    
    Supports checking a username across 100+ platforms with configurable
    concurrency, timeouts, and retry logic.
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        max_concurrent: int = 50,
        timeout: float = 10.0,
        max_retries: int = 2,
        enable_cache: bool = True,
    ):
        """
        Initialize the username enumerator.
        
        Args:
            config_path: Path to platform configuration JSON
            max_concurrent: Maximum concurrent requests
            timeout: Per-request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
            enable_cache: Enable result caching
        """
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.max_retries = max_retries
        self.enable_cache = enable_cache
        self.cache: Dict[str, List[PlatformResult]] = {}
        
        # Load platform configurations
        self.platforms = self._load_platform_config(config_path)
        
        # Session will be created when needed
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(max_concurrent)

    def _load_platform_config(self, config_path: Optional[str]) -> Dict:
        """Load platform configurations from JSON file"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "username_enum_sources.json"
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                logger.info(f"Loaded {len(config.get('platforms', {}))} platform configurations")
                return config.get("platforms", {})
        except FileNotFoundError:
            logger.warning(f"Config file not found at {config_path}, using built-in config")
            return self._get_builtin_platforms()
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing config file: {e}")
            return self._get_builtin_platforms()

    def _get_builtin_platforms(self) -> Dict:
        """Fallback built-in platform configurations"""
        # This is a subset - full list should be in config file
        return {
            "twitter": {
                "name": "Twitter/X",
                "url_template": "https://twitter.com/{username}",
                "category": "social_media",
                "method": "status_code",
                "not_found_status": [404],
                "found_status": [200],
                "timeout": 5,
                "user_agent_required": True,
            },
            "github": {
                "name": "GitHub",
                "url_template": "https://github.com/{username}",
                "category": "code",
                "method": "status_code",
                "not_found_status": [404],
                "found_status": [200],
                "timeout": 5,
                "user_agent_required": True,
            },
            "reddit": {
                "name": "Reddit",
                "url_template": "https://www.reddit.com/user/{username}",
                "category": "social_media",
                "method": "html_content",
                "not_found_patterns": ["Sorry, nobody on Reddit goes by that name", "page not found"],
                "found_patterns": ["karma", "cake day"],
                "timeout": 7,
                "user_agent_required": True,
            },
        }

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def start(self):
        """Initialize the aiohttp session"""
        connector = aiohttp.TCPConnector(
            limit=self.max_concurrent,
            limit_per_host=10,
            ttl_dns_cache=300,
            enable_cleanup_closed=True,
        )
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            },
        )
        logger.info("Username enumerator session started")

    async def close(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()
            logger.info("Username enumerator session closed")

    async def search(
        self,
        username: str,
        platforms: Optional[List[str]] = None,
        fuzzy_match: bool = False,
        progress_callback: Optional[callable] = None,
    ) -> List[UsernameMatch]:
        """
        Search for a username across platforms.
        
        Args:
            username: Username to search for
            platforms: List of platform keys to search (None = all)
            fuzzy_match: Enable fuzzy matching variations
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of UsernameMatch objects with found profiles
        """
        if not username:
            raise ValueError("Username cannot be empty")
        
        # Normalize username
        username = username.strip().lower()
        
        # Check cache first
        cache_key = f"{username}:{platforms}:{fuzzy_match}"
        if self.enable_cache and cache_key in self.cache:
            logger.info(f"Returning cached results for {username}")
            return self._results_to_matches(self.cache[cache_key])
        
        # Determine which platforms to check
        platforms_to_check = (
            [self.platforms[k] for k in platforms if k in self.platforms]
            if platforms
            else list(self.platforms.values())
        )
        
        logger.info(f"Searching for username '{username}' across {len(platforms_to_check)} platforms")
        
        # If fuzzy matching enabled, generate variations
        usernames_to_check = [username]
        if fuzzy_match:
            from .username_matching import UsernameMatcher
            matcher = UsernameMatcher()
            usernames_to_check = matcher.generate_variations(username)
            logger.info(f"Fuzzy matching enabled, checking {len(usernames_to_check)} variations")
        
        # Create tasks for concurrent execution
        tasks = []
        for platform_config in platforms_to_check:
            for username_variant in usernames_to_check:
                task = self._check_platform(
                    platform_config,
                    username_variant,
                    is_variant=(username_variant != username),
                )
                tasks.append(task)
        
        # Execute tasks with progress tracking
        results = []
        total_tasks = len(tasks)
        completed = 0
        
        for future in asyncio.as_completed(tasks):
            result = await future
            
            # Only count variants for the primary username in progress
            if not result.get("is_variant"):
                completed += 1
                if progress_callback:
                    progress = (completed / total_tasks) * 100
                    progress_callback(progress, result.get("platform", "unknown"))
            
            if result["status"] == PlatformStatus.FOUND:
                results.append(result)
        
        logger.info(f"Search complete: found {len(results)} matches for '{username}'")
        
        # Convert to UsernameMatch objects
        matches = self._results_to_matches(results)
        
        # Cache results
        if self.enable_cache:
            self.cache[cache_key] = results
        
        return matches

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
    )
    async def _check_platform(
        self,
        platform_config: Dict,
        username: str,
        is_variant: bool = False,
    ) -> Dict:
        """
        Check a single platform for the given username.
        
        Args:
            platform_config: Platform configuration dictionary
            username: Username to check
            is_variant: Whether this is a username variation
            
        Returns:
            Dictionary with check results
        """
        platform_key = platform_config.get("name", "unknown")
        url = platform_config["url_template"].format(username=username)
        method = platform_config.get("method", "status_code")
        timeout = platform_config.get("timeout", self.timeout)
        
        start_time = datetime.utcnow()
        result = {
            "platform": platform_key,
            "username": username,
            "url": url,
            "is_variant": is_variant,
            "status": PlatformStatus.UNKNOWN,
            "confidence": ConfidenceLevel.NONE,
            "response_code": None,
            "response_time": 0.0,
            "error_message": None,
            "profile_data": {},
        }
        
        try:
            async with self.semaphore:
                headers = {}
                if platform_config.get("user_agent_required", False):
                    headers["User-Agent"] = UserAgentRotator.get_random()
                
                async with self.session.get(url, headers=headers, timeout=timeout) as response:
                    result["response_code"] = response.status
                    result["response_time"] = (datetime.utcnow() - start_time).total_seconds()
                    
                    # Determine status based on method
                    if method == "status_code":
                        result = self._check_by_status_code(response, platform_config, result)
                    elif method == "html_content":
                        html = await response.text()
                        result = self._check_by_html_content(html, platform_config, result)
                    elif method == "json_api":
                        json_data = await response.json()
                        result = self._check_by_json_api(json_data, platform_config, result)
                    elif method == "redirect":
                        result = self._check_by_redirect(response, platform_config, result)
                    
        except asyncio.TimeoutError:
            result["status"] = PlatformStatus.TIMEOUT
            result["error_message"] = "Request timeout"
            logger.debug(f"Timeout checking {platform_key} for {username}")
            
        except aiohttp.ClientError as e:
            result["status"] = PlatformStatus.ERROR
            result["error_message"] = str(e)
            logger.debug(f"Error checking {platform_key} for {username}: {e}")
            
        except Exception as e:
            result["status"] = PlatformStatus.ERROR
            result["error_message"] = f"Unexpected error: {e}"
            logger.error(f"Unexpected error checking {platform_key}: {e}")
        
        # Adjust confidence based on whether this is a variant
        if is_variant and result["status"] == PlatformStatus.FOUND:
            result["confidence"] = ConfidenceLevel.MEDIUM
        
        return result

    def _check_by_status_code(
        self,
        response: aiohttp.ClientResponse,
        platform_config: Dict,
        result: Dict,
    ) -> Dict:
        """Check if username exists based on HTTP status code"""
        found_status = platform_config.get("found_status", [200])
        not_found_status = platform_config.get("not_found_status", [404])
        
        if response.status in found_status:
            result["status"] = PlatformStatus.FOUND
            result["confidence"] = ConfidenceLevel.HIGH
        elif response.status in not_found_status:
            result["status"] = PlatformStatus.NOT_FOUND
        elif response.status == 429:
            result["status"] = PlatformStatus.BLOCKED
            result["error_message"] = "Rate limited"
        else:
            result["status"] = PlatformStatus.UNKNOWN
        
        return result

    def _check_by_html_content(
        self,
        html: str,
        platform_config: Dict,
        result: Dict,
    ) -> Dict:
        """Check if username exists based on HTML content patterns"""
        found_patterns = platform_config.get("found_patterns", [])
        not_found_patterns = platform_config.get("not_found_patterns", [])
        
        soup = BeautifulSoup(html, "html.parser")
        body_text = soup.get_text().lower()
        html_lower = html.lower()
        
        # Check for not-found patterns first (more reliable)
        for pattern in not_found_patterns:
            if pattern.lower() in body_text or pattern.lower() in html_lower:
                result["status"] = PlatformStatus.NOT_FOUND
                return result
        
        # Check for found patterns
        matches_found = 0
        for pattern in found_patterns:
            if pattern.lower() in body_text or pattern.lower() in html_lower:
                matches_found += 1
        
        if matches_found > 0:
            result["status"] = PlatformStatus.FOUND
            result["confidence"] = (
                ConfidenceLevel.HIGH if matches_found >= 2 else ConfidenceLevel.MEDIUM
            )
            # Extract additional profile data
            result["profile_data"] = self._extract_profile_data(soup, platform_config)
        else:
            result["status"] = PlatformStatus.NOT_FOUND
        
        return result

    def _check_by_json_api(
        self,
        json_data: Dict,
        platform_config: Dict,
        result: Dict,
    ) -> Dict:
        """Check if username exists based on JSON API response"""
        not_found_indicators = platform_config.get("not_found_indicators", ["error", "not_found"])
        found_indicators = platform_config.get("found_indicators", ["user", "profile", "data"])
        
        # Check if response indicates not found
        for indicator in not_found_indicators:
            if indicator in str(json_data).lower():
                result["status"] = PlatformStatus.NOT_FOUND
                return result
        
        # Check if response indicates found
        for indicator in found_indicators:
            if indicator in json_data:
                result["status"] = PlatformStatus.FOUND
                result["confidence"] = ConfidenceLevel.HIGH
                result["profile_data"] = json_data
                return result
        
        result["status"] = PlatformStatus.UNKNOWN
        return result

    def _check_by_redirect(
        self,
        response: aiohttp.ClientResponse,
        platform_config: Dict,
        result: Dict,
    ) -> Dict:
        """Check if username exists based on redirect behavior"""
        redirect_pattern = platform_config.get("redirect_not_found_pattern", "")
        
        if response.history:
            # Check if redirected to a "not found" page
            final_url = str(response.url)
            if redirect_pattern and redirect_pattern in final_url:
                result["status"] = PlatformStatus.NOT_FOUND
            else:
                result["status"] = PlatformStatus.FOUND
                result["confidence"] = ConfidenceLevel.MEDIUM
        else:
            # No redirect - check status code
            if response.status == 200:
                result["status"] = PlatformStatus.FOUND
                result["confidence"] = ConfidenceLevel.HIGH
            elif response.status == 404:
                result["status"] = PlatformStatus.NOT_FOUND
        
        return result

    def _extract_profile_data(
        self,
        soup: BeautifulSoup,
        platform_config: Dict,
    ) -> Dict:
        """Extract additional profile data from HTML"""
        data = {}
        
        # Common profile data extraction patterns
        selectors = platform_config.get("profile_selectors", {})
        
        for key, selector in selectors.items():
            elements = soup.select(selector)
            if elements:
                data[key] = elements[0].get_text(strip=True)
        
        # Extract meta tags
        meta_tags = {
            "title": soup.title.get_text(strip=True) if soup.title else None,
            "description": None,
        }
        
        for meta in soup.find_all("meta", attrs={"name": "description"}):
            meta_tags["description"] = meta.get("content")
        
        data["meta"] = meta_tags
        
        return data

    def _results_to_matches(self, results: List[Dict]) -> List[UsernameMatch]:
        """Convert result dictionaries to UsernameMatch objects"""
        matches = []
        seen_urls = set()
        
        for result in results:
            url = result["url"]
            
            # Deduplicate by URL
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            match = UsernameMatch(
                username=result["username"],
                platform=result["platform"],
                profile_url=url,
                confidence=result["confidence"],
                is_verified=result["confidence"] == ConfidenceLevel.HIGH,
                discovery_method="fuzzy" if result.get("is_variant") else "direct",
                additional_info={
                    "response_code": result.get("response_code"),
                    "response_time": result.get("response_time"),
                    "profile_data": result.get("profile_data", {}),
                },
            )
            matches.append(match)
        
        return matches

    async def search_multiple(
        self,
        usernames: List[str],
        platforms: Optional[List[str]] = None,
        fuzzy_match: bool = False,
        progress_callback: Optional[callable] = None,
    ) -> Dict[str, List[UsernameMatch]]:
        """
        Search for multiple usernames in parallel.
        
        Args:
            usernames: List of usernames to search
            platforms: List of platform keys to search (None = all)
            fuzzy_match: Enable fuzzy matching variations
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary mapping username to list of UsernameMatch objects
        """
        results = {}
        total = len(usernames)
        
        for i, username in enumerate(usernames):
            matches = await self.search(
                username,
                platforms=platforms,
                fuzzy_match=fuzzy_match,
                progress_callback=progress_callback,
            )
            results[username] = matches
            
            if progress_callback:
                progress = ((i + 1) / total) * 100
                progress_callback(progress, username)
        
        return results

    def clear_cache(self):
        """Clear the result cache"""
        self.cache.clear()
        logger.info("Result cache cleared")

    def get_platform_stats(self) -> Dict:
        """Get statistics about configured platforms"""
        categories = {}
        for platform in self.platforms.values():
            category = platform.get("category", "other")
            categories[category] = categories.get(category, 0) + 1
        
        return {
            "total_platforms": len(self.platforms),
            "categories": categories,
            "max_concurrent": self.max_concurrent,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
        }


async def enumerate_username(
    username: str,
    config_path: Optional[str] = None,
    max_concurrent: int = 50,
) -> List[UsernameMatch]:
    """
    Convenience function for username enumeration.
    
    Args:
        username: Username to search for
        config_path: Optional path to platform configuration
        max_concurrent: Maximum concurrent requests
        
    Returns:
        List of UsernameMatch objects
    """
    async with UsernameEnumerator(config_path=config_path, max_concurrent=max_concurrent) as enumerator:
        return await enumerator.search(username)


if __name__ == "__main__":
    # Example usage
    async def main():
        matches = await enumerate_username("example_user", max_concurrent=20)
        for match in matches:
            print(f"{match.platform}: {match.profile_url} (confidence: {match.confidence.name})")
    
    asyncio.run(main())
