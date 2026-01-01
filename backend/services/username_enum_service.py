import re
import json
from typing import List, Dict, Tuple, Optional, Set, Any
import asyncio
from datetime import datetime, timedelta
import hashlib
from urllib.parse import urljoin, urlparse
from fuzzywuzzy import fuzz
from dataclasses import dataclass

from ..models.schemas import PlatformResult, FuzzyMatchRequest
from ..utils.platform_registry import PlatformRegistry
from ..utils.pattern_detector import PatternDetector
from ..utils.confidence_scorer import ConfidenceScorer


@dataclass
class MatchCandidate:
    platform_name: str
    username: str
    profile_url: str
    confidence: float
    match_type: str
    metadata: Optional[Dict] = None


class UsernameEnumerationService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.platform_registry = PlatformRegistry()
        self.pattern_detector = PatternDetector()
        self.confidence_scorer = ConfidenceScorer(config)
        
        # Cache for platform responses
        self._profile_cache = {}
        self._cache_ttl = config.get('cache_ttl', 3600)
        
        # Rate limiting state (in production, use Redis)
        self._rate_limits = {}
        
    async def enumerate_username(
        self, 
        username: str, 
        email: Optional[str] = None, 
        phone: Optional[str] = None,
        platforms: Optional[List[str]] = None
    ) -> List[PlatformResult]:
        """
        Main enumeration function that combines exact, fuzzy, and pattern matching
        """
        start_time = datetime.utcnow()
        results = []
        
        # Get target platforms
        if platforms:
            target_platforms = [self.platform_registry.get_platform(p) for p in platforms]
        else:
            target_platforms = self.platform_registry.get_all_platforms()
        
        # Perform searches in parallel
        tasks = []
        for platform in target_platforms:
            if email:
                tasks.append(self._reverse_lookup_email(platform, email))
            if phone:
                tasks.append(self._reverse_lookup_phone(platform, phone))
            
            # Always search by username
            tasks.append(self._search_username_on_platform(platform, username))
            tasks.append(self._fuzzy_search_on_platform(platform, username))
        
        # Execute concurrent searches
        search_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in search_results:
            if isinstance(result, Exception):
                continue  # Log error but continue processing
            if result:
                results.extend(result)
        
        # Apply confidence scoring
        scored_results = []
        for match in results:
            confidence = self.confidence_scorer.calculate_score(
                match, username, email, phone
            )
            if confidence >= self.config.get('min_confidence', 0.3):
                match.confidence = confidence
                scored_results.append(match)
        
        # Deduplicate and sort by confidence
        unique_results = self._deduplicate_results(scored_results)
        unique_results.sort(key=lambda x: x.confidence, reverse=True)
        
        return unique_results
    
    async def fuzzy_match_search(
        self, 
        username: str, 
        tolerance: str = 'medium'
    ) -> List[PlatformResult]:
        """
        Perform fuzzy matching with configurable tolerance levels
        """
        tolerance_map = {
            'low': 80,
            'medium': 70,
            'high': 60
        }
        similarity_threshold = tolerance_map.get(tolerance, 70)
        
        results = []
        platforms = self.platform_registry.get_all_platforms()
        
        tasks = [
            self._fuzzy_search_on_platform(platform, username, similarity_threshold)
            for platform in platforms
        ]
        
        search_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for platform_results in search_results:
            if isinstance(platform_results, list):
                results.extend(platform_results)
        
        return results
    
    async def reverse_lookup(
        self, 
        email: Optional[str] = None, 
        phone: Optional[str] = None
    ) -> List[Dict]:
        """
        Find usernames associated with email or phone
        """
        results = []
        platforms = self.platform_registry.get_all_platforms()
        
        tasks = []
        for platform in platforms:
            if email:
                tasks.append(self._reverse_lookup_email(platform, email))
            if phone:
                tasks.append(self._reverse_lookup_phone(platform, phone))
        
        search_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        username_platforms = {}
        for platform_results in search_results:
            if isinstance(platform_results, list):
                for match in platform_results:
                    if match.username not in username_platforms:
                        username_platforms[match.username] = []
                    username_platforms[match.username].append(match.platform_name)
        
        for username, platform_list in username_platforms.items():
            results.append({
                'username': username,
                'platforms': list(set(platform_list))
            })
        
        return results
    
    async def build_identity_chain(self, username: str) -> Dict[str, Any]:
        """
        Build identity relationship chains
        """
        chain_data = {'nodes': [], 'relationships': [], 'chain_length': 0}
        visited = set()
        
        # Start with the main username node
        main_node_id = self._generate_node_id('username', username)
        chain_data['nodes'].append({
            'id': main_node_id,
            'type': 'username',
            'value': username,
            'platform': None,
            'confidence': 1.0
        })
        visited.add(main_node_id)
        
        # Search for profiles containing this username
        search_results = await self.enumerate_username(username)
        
        for result in search_results:
            # Add platform profile node
            profile_node_id = self._generate_node_id('profile', result.profile_url)
            if profile_node_id not in visited:
                chain_data['nodes'].append({
                    'id': profile_node_id,
                    'type': 'profile',
                    'value': result.profile_url,
                    'platform': result.platform,
                    'confidence': result.confidence
                })
                visited.add(profile_node_id)
            
            # Add relationship: username -> found_on -> profile
            chain_data['relationships'].append({
                'source_id': main_node_id,
                'target_id': profile_node_id,
                'relationship_type': 'found_on',
                'confidence': result.confidence,
                'discovered_at': datetime.utcnow()
            })
            
            # Extract emails and phones from profile metadata
            metadata = result.metadata or {}
            
            # Extract email relationships
            if 'email' in metadata:
                email_node_id = self._generate_node_id('email', metadata['email'])
                if email_node_id not in visited:
                    chain_data['nodes'].append({
                        'id': email_node_id,
                        'type': 'email',
                        'value': metadata['email'],
                        'platform': result.platform,
                        'confidence': result.confidence * 0.9  # Slightly lower confidence
                    })
                    visited.add(email_node_id)
                
                # Add relationship: profile -> linked_to -> email
                chain_data['relationships'].append({
                    'source_id': profile_node_id,
                    'target_id': email_node_id,
                    'relationship_type': 'linked_to',
                    'confidence': result.confidence * 0.9,
                    'discovered_at': datetime.utcnow()
                })
            
            # Extract phone relationships
            if 'phone' in metadata:
                phone_node_id = self._generate_node_id('phone', metadata['phone'])
                if phone_node_id not in visited:
                    chain_data['nodes'].append({
                        'id': phone_node_id,
                        'type': 'phone',
                        'value': metadata['phone'],
                        'platform': result.platform,
                        'confidence': result.confidence * 0.9
                    })
                    visited.add(phone_node_id)
                
                # Add relationship: profile -> linked_to -> phone
                chain_data['relationships'].append({
                    'source_id': profile_node_id,
                    'target_id': phone_node_id,
                    'relationship_type': 'linked_to',
                    'confidence': result.confidence * 0.9,
                    'discovered_at': datetime.utcnow()
                })
        
        chain_data['chain_length'] = len(chain_data['relationships'])
        return chain_data
    
    async def _search_username_on_platform(
        self, 
        platform, 
        username: str
    ) -> List[MatchCandidate]:
        """Search for exact username matches on a platform"""
        results = []
        
        if not platform.config.get('enabled', True):
            return results
        
        # Check cache first
        cache_key = f"exact_{platform.name}_{username}"
        if self._is_cached(cache_key):
            return self._get_cached(cache_key)
        
        # Generate profile URLs to test
        profile_urls = platform.generate_profile_urls(username)
        
        # Test each URL
        for url in profile_urls:
            try:
                result = await self._check_profile_exists(url, platform)
                if result['exists']:
                    match = MatchCandidate(
                        platform_name=platform.name,
                        username=username,
                        profile_url=url,
                        confidence=result.get('confidence', 0.9),
                        match_type='exact',
                        metadata=result.get('metadata', {})
                    )
                    results.append(match)
                    break  # Found one valid profile
            except Exception as e:
                continue
        
        self._cache_result(cache_key, results)
        return results
    
    async def _fuzzy_search_on_platform(
        self, 
        platform, 
        username: str, 
        threshold: int = 70
    ) -> List[MatchCandidate]:
        """Perform fuzzy matching on a platform"""
        results = []
        
        if not platform.config.get('fuzzy_search_enabled', False):
            return results
        
        # For demonstration, we'll use a simplified approach
        # In production, this would query the platform's user search API
        variations = self._generate_username_variations(username)
        
        for variation in variations:
            similarity = fuzz.ratio(username.lower(), variation.lower())
            if similarity >= threshold:
                profile_urls = platform.generate_profile_urls(variation)
                for url in profile_urls:
                    try:
                        result = await self._check_profile_exists(url, platform)
                        if result['exists']:
                            match = MatchCandidate(
                                platform_name=platform.name,
                                username=variation,
                                profile_url=url,
                                confidence=similarity / 100.0,
                                match_type='fuzzy',
                                metadata=result.get('metadata', {})
                            )
                            results.append(match)
                            break
                    except Exception:
                        continue
        
        return results
    
    async def _reverse_lookup_email(
        self, 
        platform, 
        email: str
    ) -> List[MatchCandidate]:
        """Find usernames associated with an email"""
        results = []
        
        # In production, this would use platform-specific APIs
        # For now, we've simplified the logic
        username_guess = email.split('@')[0]
        
        return await self._search_username_on_platform(platform, username_guess)
    
    async def _reverse_lookup_phone(
        self, 
        platform, 
        phone: str
    ) -> List[MatchCandidate]:
        """Find usernames associated with a phone"""
        # Similar to email lookup - extract patterns from phone
        digits = re.sub(r'[^\d]', '', phone)
        
        if len(digits) >= 7:
            # Try various patterns from phone number
            username_candidates = [
                digits[-7:],  # Last 7 digits
                digits[-6:],  # Last 6 digits
                digits[-8:],  # Last 8 digits
            ]
            
            results = []
            for candidate in username_candidates:
                platform_results = await self._search_username_on_platform(platform, candidate)
                results.extend(platform_results)
            
            return results
        
        return []
    
    async def _check_profile_exists(
        self, 
        url: str, 
        platform
    ) -> Dict[str, Any]:
        """Check if a profile URL exists and extract metadata"""
        # In production, this would make HTTP requests
        # For this implementation, we'll simulate responses
        
        cache_key = f"profile_check_{url}"
        if self._is_cached(cache_key):
            return self._get_cached(cache_key)
        
        # Simulated response (in reality, this would scrape/API call)
        username = self._extract_username_from_url(url, platform)
        
        # Simulate some usernames existing
        existing_usernames = [
            'john', 'johndoe', 'john123', 'j_doe', 'john.doe',
            'sarah', 'sarah_smith', 'sarah1990', 'sarah.smith'
        ]
        
        exists = username.lower() in existing_usernames
        
        result = {
            'exists': exists,
            'confidence': 0.9 if exists else 0.0,
            'metadata': {
                'username': username,
                'platform': platform.name,
                'url': url,
                'email': f"{username}@example.com" if exists else None,
                'phone': f"+1234567890" if exists else None
            } if exists else {}
        }
        
        self._cache_result(cache_key, result)
        return result
    
    def _generate_username_variations(self, username: str) -> List[str]:
        """Generate possible variations of a username"""
        variations = [username]
        
        # Add common variations
        patterns = self.pattern_detector.detect_patterns(username)
        
        for pattern in patterns:
            if pattern['type'] == 'name_number':
                base_name = pattern['components']['name']
                number = pattern['components']['number']
                
                variations.extend([
                    f"{base_name}_{number}",
                    f"{base_name}-{number}",
                    f"{base_name}.{number}",
                ])
            elif pattern['type'] == 'firstname_lastname':
                first = pattern['components']['first']
                last = pattern['components']['last']
                
                variations.extend([
                    f"{first}_{last}",
                    f"{first}-{last}",
                    f"{first}.{last}",
                    f"{first[0]}{last}",
                    f"{last}{first[0]}",
                ])
        
        # Common patterns
        base = ''.join(filter(str.isalpha, username))
        numbers = ''.join(filter(str.isdigit, username))
        
        if numbers:
            variations.extend([
                f"{base}_{numbers}",
                f"{base}{numbers}",
                f"{base}-{numbers}",
            ])
        
        return list(set(variations))
    
    def _extract_username_from_url(self, url: str, platform) -> str:
        """Extract username from profile URL"""
        path = urlparse(url).path
        
        # Remove common prefixes
        path = path.split('/')[-1]
        
        # Remove any query parameters
        path = path.split('?')[0]
        
        return path
    
    def _deduplicate_results(self, results: List[MatchCandidate]) -> List[MatchCandidate]:
        """Remove duplicate results based on profile URL"""
        seen = set()
        unique = []
        
        for result in results:
            key = (result.platform_name, result.profile_url)
            if key not in seen:
                seen.add(key)
                unique.append(result)
        
        return unique
    
    def _is_cached(self, key: str) -> bool:
        """Check if result is cached"""
        if key in self._profile_cache:
            cached_data, timestamp = self._profile_cache[key]
            if datetime.utcnow() - timestamp < timedelta(seconds=self._cache_ttl):
                return True
            else:
                del self._profile_cache[key]
        return False
    
    def _get_cached(self, key: str):
        """Get cached result"""
        cached_data, _ = self._profile_cache[key]
        return cached_data
    
    def _cache_result(self, key: str, data: Any):
        """Cache result"""
        self._profile_cache[key] = (data, datetime.utcnow())
    
    def _generate_node_id(self, node_type: str, value: str) -> str:
        """Generate unique node ID"""
        return hashlib.md5(f"{node_type}:{value}".encode()).hexdigest()
    
    def _cleanup_cache(self):
        """Remove expired cache entries"""
        now = datetime.utcnow()
        expired_keys = []
        
        for key, (data, timestamp) in self._profile_cache.items():
            if now - timestamp > timedelta(seconds=self._cache_ttl):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._profile_cache[key]