"""
Advanced Username Matching Module

Provides exact matching, fuzzy matching, pattern recognition,
and cross-referencing capabilities for identity discovery.
"""

import re
import asyncio
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
from difflib import SequenceMatcher
import logging

try:
    from thefuzz import fuzz, process
    THEFUZZ_AVAILABLE = True
except ImportError:
    try:
        from fuzzywuzzy import fuzz, process
        THEFUZZ_AVAILABLE = True
    except ImportError:
        THEFUZZ_AVAILABLE = False
        logging.warning("thefuzz/fuzzywuzzy not available, using built-in matching")

logger = logging.getLogger(__name__)


class MatchType(Enum):
    """Types of username matches"""
    EXACT = "exact"
    FUZZY = "fuzzy"
    VARIATION = "variation"
    PATTERN = "pattern"
    DERIVED = "derived"


@dataclass
class UsernameVariation:
    """A username variation with metadata"""
    username: str
    match_type: MatchType
    similarity_score: float
    derivation_method: str


class UsernameMatcher:
    """
    Advanced username matching with fuzzy matching, pattern recognition,
    and cross-referencing capabilities.
    """

    # Common substitutions in usernames
    COMMON_SUBSTITUTIONS = {
        'a': ['4', '@', '*', 'æ'],
        'b': ['8', '6', '|3'],
        'e': ['3', '€'],
        'g': ['9', '6'],
        'i': ['1', '!', '|', 'ï'],
        'l': ['1', '|', '£'],
        'o': ['0', '@'],
        's': ['5', '$', 'z'],
        't': ['7', '+', '†'],
        'z': ['2', 's'],
    }

    # Common username patterns
    COMMON_PATTERNS = [
        r'^[a-z]+\d+$',          # letters followed by numbers (e.g., john123)
        r'^[a-z]+_[a-z]+$',      # underscore separated (e.g., john_doe)
        r'^[a-z]+\.[a-z]+$',     # dot separated (e.g., john.doe)
        r'^[a-z]+-[a-z]+$',      # hyphen separated (e.g., john-doe)
        r'^\d+[a-z]+$',          # numbers followed by letters (e.g., 123john)
        r'^[a-z]{3,}$',          # 3+ letters only
        r'^[a-z]+\d{4}$',        # letters + 4 digits (common birth year)
    ]

    # Common separators
    SEPARATORS = ['_', '.', '-', '']

    def __init__(self, fuzzy_threshold: int = 70, max_variations: int = 50):
        """
        Initialize the username matcher.
        
        Args:
            fuzzy_threshold: Minimum similarity score for fuzzy matches (0-100)
            max_variations: Maximum variations to generate
        """
        self.fuzzy_threshold = fuzzy_threshold
        self.max_variations = max_variations

    def generate_variations(
        self,
        username: str,
        match_types: Optional[List[MatchType]] = None,
    ) -> List[str]:
        """
        Generate username variations for fuzzy matching.
        
        Args:
            username: Original username
            match_types: Types of variations to generate (None = all)
            
        Returns:
            List of username variations
        """
        if not username:
            return []
        
        variations = set()
        variations.add(username.lower())
        
        if match_types is None:
            match_types = [MatchType.VARIATION, MatchType.PATTERN, MatchType.DERIVED]
        
        # Generate different types of variations
        if MatchType.VARIATION in match_types:
            variations.update(self._generate_separator_variations(username))
            variations.update(self._generate_leet_speak_variations(username))
            variations.update(self._generate_case_variations(username))
        
        if MatchType.PATTERN in match_types:
            variations.update(self._generate_pattern_variations(username))
            variations.update(self._generate_number_variations(username))
        
        if MatchType.DERIVED in match_types:
            variations.update(self._generate_abbreviations(username))
            variations.update(self._generate_common_additions(username))
        
        # Remove duplicates and limit count
        result = list(variations)[:self.max_variations]
        logger.debug(f"Generated {len(result)} variations for '{username}'")
        return result

    def _generate_separator_variations(self, username: str) -> Set[str]:
        """Generate variations by changing separators"""
        variations = set()
        
        # Replace existing separators with alternatives
        for sep_from in ['_', '.', '-']:
            if sep_from in username:
                for sep_to in self.SEPARATORS:
                    variations.add(username.replace(sep_from, sep_to))
        
        # Add separators to letter-number boundaries
        for sep in self.SEPARATORS:
            # Insert separator before numbers
            with_num = re.sub(r'([a-z])(\d)', rf'\1{sep}\2', username)
            if with_num != username:
                variations.add(with_num)
        
        return variations

    def _generate_leet_speak_variations(self, username: str) -> Set[str]:
        """Generate leet speak variations"""
        variations = set()
        
        # Generate single substitution variations
        for char, subs in self.COMMON_SUBSTITUTIONS.items():
            if char in username.lower():
                for sub in subs:
                    variations.add(username.lower().replace(char, sub))
        
        # Generate limited multi-substitution variations
        leet_variations = [username.lower()]
        for _ in range(2):  # Limit depth to avoid exponential explosion
            new_variations = []
            for var in leet_variations:
                for char, subs in self.COMMON_SUBSTITUTIONS.items():
                    if char in var:
                        for sub in subs:
                            new_var = var.replace(char, sub)
                            if new_var not in leet_variations:
                                new_variations.append(new_var)
            if not new_variations:
                break
            variations.update(new_variations[:5])  # Limit per iteration
        
        return variations

    def _generate_case_variations(self, username: str) -> Set[str]:
        """Generate case variations (for case-insensitive matching)"""
        variations = set()
        lower = username.lower()
        variations.add(lower)
        
        # Capitalize first letter
        variations.add(lower.capitalize())
        
        # Capitalize each word (after separators)
        for sep in ['_', '.', '-']:
            if sep in lower:
                parts = lower.split(sep)
                capitalized = sep.join(p.capitalize() for p in parts)
                variations.add(capitalized)
        
        return variations

    def _generate_pattern_variations(self, username: str) -> Set[str]:
        """Generate pattern-based variations"""
        variations = set()
        
        # Extract base name (remove numbers)
        base_name = re.sub(r'\d+$', '', username)
        if base_name and base_name != username:
            variations.add(base_name)
        
        # Extract numbers
        numbers = re.findall(r'\d+', username)
        if numbers:
            base_without_nums = re.sub(r'\d+', '', username)
            variations.add(base_without_nums.strip('_.-'))
        
        return variations

    def _generate_number_variations(self, username: str) -> Set[str]:
        """Generate variations by adding common number patterns"""
        variations = set()
        base = re.sub(r'\d+$', '', username)
        
        if not base:
            return variations
        
        # Common years
        years = ['90', '91', '92', '93', '94', '95', '96', '97', '98', '99',
                 '00', '01', '02', '03', '04', '05', '06', '07', '08', '09']
        
        # Common number suffixes
        common_nums = ['1', '123', '007', '42', '69', '99', '365', '777']
        
        for suffix in years + common_nums:
            variations.add(f"{base}{suffix}")
        
        # Prepend numbers
        for prefix in ['1', '2', '3', 'the', 'mr', 'ms']:
            variations.add(f"{prefix}{base}")
        
        return variations

    def _generate_abbreviations(self, username: str) -> Set[str]:
        """Generate abbreviation-based variations"""
        variations = set()
        
        # Split by common separators
        parts = re.split(r'[_.-]', username)
        
        if len(parts) > 1:
            # Initials
            initials = ''.join(p[0] for p in parts if p)
            variations.add(initials.lower())
            
            # First word + initial
            if len(parts) >= 2:
                variations.add(f"{parts[0]}{parts[1][0]}".lower())
            
            # Mixed abbreviations
            if len(parts) >= 3:
                variations.add(f"{parts[0]}{parts[2]}".lower())
                variations.add(f"{parts[0]}{parts[1]}{parts[2][0]}".lower())
        
        return variations

    def _generate_common_additions(self, username: str) -> Set[str]:
        """Generate variations with common additions"""
        variations = set()
        base = username
        
        # Common prefixes
        prefixes = ['the', 'mr', 'mrs', 'ms', 'dr', 'real', 'iam', 'its', 'im']
        for prefix in prefixes:
            variations.add(f"{prefix}{base}")
            variations.add(f"{prefix}_{base}")
            variations.add(f"{prefix}.{base}")
        
        # Common suffixes
        suffixes = ['official', 'official_', 'offical', 'real', 'verified', 
                   'verified_', 'xoxo', 'xo', 'xx', 'lol', 'yolo']
        for suffix in suffixes:
            variations.add(f"{base}{suffix}")
            variations.add(f"{base}_{suffix}")
            variations.add(f"{base}.{suffix}")
        
        return variations

    def fuzzy_match(
        self,
        username: str,
        candidates: List[str],
        threshold: Optional[int] = None,
        limit: int = 10,
    ) -> List[Tuple[str, int]]:
        """
        Find fuzzy matches from a list of candidates.
        
        Args:
            username: Username to match
            candidates: List of candidate usernames
            threshold: Minimum similarity score (uses instance threshold if None)
            limit: Maximum number of matches to return
            
        Returns:
            List of (candidate, score) tuples sorted by score
        """
        if threshold is None:
            threshold = self.fuzzy_threshold
        
        if not candidates:
            return []
        
        if THEFUZZ_AVAILABLE:
            # Use thefuzz/fuzzywuzzy for better matching
            results = process.extract(
                username.lower(),
                [c.lower() for c in candidates],
                limit=limit * 2,  # Get more to filter by threshold
            )
            # Filter by threshold
            filtered = [(c, s) for c, s in results if s >= threshold]
            return sorted(filtered, key=lambda x: x[1], reverse=True)[:limit]
        else:
            # Fallback to built-in difflib
            username_lower = username.lower()
            results = []
            for candidate in candidates:
                score = int(SequenceMatcher(None, username_lower, candidate.lower()).ratio() * 100)
                if score >= threshold:
                    results.append((candidate, score))
            return sorted(results, key=lambda x: x[1], reverse=True)[:limit]

    def exact_match(self, username: str, candidates: List[str]) -> List[str]:
        """
        Find exact matches from a list of candidates.
        
        Args:
            username: Username to match
            candidates: List of candidate usernames
            
        Returns:
            List of exact matches (case-insensitive)
        """
        username_lower = username.lower()
        return [c for c in candidates if c.lower() == username_lower]

    def extract_username_from_email(self, email: str) -> List[str]:
        """
        Extract potential usernames from an email address.
        
        Args:
            email: Email address to parse
            
        Returns:
            List of potential usernames derived from the email
        """
        if not email or '@' not in email:
            return []
        
        local_part = email.split('@')[0].lower()
        usernames = [local_part]
        
        # Remove common patterns from local part
        # Remove numbers at end
        base = re.sub(r'\d+$', '', local_part)
        if base and base != local_part:
            usernames.append(base)
        
        # Remove dots
        no_dots = local_part.replace('.', '')
        if no_dots != local_part:
            usernames.append(no_dots)
        
        # Remove plus and everything after (gmail style)
        plus_removed = local_part.split('+')[0]
        if plus_removed != local_part:
            usernames.append(plus_removed)
        
        # Split on dots and recombine
        parts = local_part.split('.')
        if len(parts) > 1:
            usernames.append(''.join(parts))
            usernames.append('_'.join(parts))
            usernames.append('-'.join(parts))
        
        return list(set(usernames))

    def extract_username_from_name(self, name: str) -> List[str]:
        """
        Extract potential usernames from a person's name.
        
        Args:
            name: Full name (e.g., "John Doe", "Jane Marie Smith")
            
        Returns:
            List of potential usernames derived from the name
        """
        if not name:
            return []
        
        # Clean and split name
        parts = re.findall(r'[a-z]+', name.lower())
        if not parts:
            return []
        
        usernames = set()
        
        if len(parts) >= 2:
            first, last = parts[0], parts[-1]
            
            # Common patterns
            usernames.add(f"{first}{last}")
            usernames.add(f"{first}.{last}")
            usernames.add(f"{first}_{last}")
            usernames.add(f"{first}-{last}")
            usernames.add(f"{first}{last[0]}")
            usernames.add(f"{first}_{last[0]}")
            usernames.add(f"{first[0]}{last}")
            usernames.add(f"{first[0]}_{last}")
            usernames.add(f"{last}{first}")
            usernames.add(f"{last}.{first}")
            
            # With middle initial
            if len(parts) >= 3:
                middle = parts[1]
                usernames.add(f"{first}{middle}{last}")
                usernames.add(f"{first}{middle[0]}{last}")
                usernames.add(f"{first}_{middle[0]}_{last}")
        
        # Just first name
        usernames.add(parts[0])
        
        return list(usernames)

    def extract_username_from_phone(self, phone: str) -> List[str]:
        """
        Extract potential usernames from a phone number.
        
        Args:
            phone: Phone number string
            
        Returns:
            List of potential usernames derived from the phone
        """
        if not phone:
            return []
        
        # Extract digits
        digits = re.sub(r'[^\d]', '', phone)
        
        usernames = []
        
        # Last 4 digits (common)
        if len(digits) >= 4:
            usernames.append(digits[-4:])
        
        # Last 6-7 digits
        if len(digits) >= 6:
            usernames.append(digits[-6:])
            if len(digits) >= 7:
                usernames.append(digits[-7:])
        
        # T9 word conversion (basic)
        t9_map = {
            '2': ['a', 'b', 'c'],
            '3': ['d', 'e', 'f'],
            '4': ['g', 'h', 'i'],
            '5': ['j', 'k', 'l'],
            '6': ['m', 'n', 'o'],
            '7': ['p', 'q', 'r', 's'],
            '8': ['t', 'u', 'v'],
            '9': ['w', 'x', 'y', 'z'],
        }
        
        if len(digits) >= 4:
            last_4 = digits[-4:]
            # Generate some T9 combinations
            words = ['']
            for d in last_4:
                if d in t9_map:
                    new_words = []
                    for word in words:
                        for letter in t9_map[d]:
                            new_words.append(word + letter)
                    words = new_words
            usernames.extend(words[:10])  # Limit to 10 T9 combinations
        
        return usernames

    def calculate_similarity(self, username1: str, username2: str) -> int:
        """
        Calculate similarity score between two usernames.
        
        Args:
            username1: First username
            username2: Second username
            
        Returns:
            Similarity score (0-100)
        """
        if not username1 or not username2:
            return 0
        
        if username1.lower() == username2.lower():
            return 100
        
        if THEFUZZ_AVAILABLE:
            return fuzz.ratio(username1.lower(), username2.lower())
        else:
            return int(SequenceMatcher(
                None, 
                username1.lower(), 
                username2.lower()
            ).ratio() * 100)

    def get_match_type(
        self,
        username1: str,
        username2: str,
        similarity_score: int,
    ) -> MatchType:
        """
        Determine the type of match between two usernames.
        
        Args:
            username1: First username
            username2: Second username
            similarity_score: Similarity score
            
        Returns:
            MatchType enum value
        """
        if username1.lower() == username2.lower():
            return MatchType.EXACT
        
        if similarity_score >= 90:
            return MatchType.FUZZY
        
        # Check if it's a separator variation
        norm1 = re.sub(r'[_.-]', '', username1.lower())
        norm2 = re.sub(r'[_.-]', '', username2.lower())
        if norm1 == norm2:
            return MatchType.VARIATION
        
        if similarity_score >= 70:
            return MatchType.FUZZY
        
        return MatchType.PATTERN


class CrossReferenceEngine:
    """
    Engine for cross-referencing identities across platforms
    and building connection chains.
    """

    def __init__(self):
        """Initialize the cross-reference engine"""
        self.matcher = UsernameMatcher()

    async def build_identity_chain(
        self,
        initial_username: str,
        found_matches: List[Dict],
        max_depth: int = 3,
    ) -> List[Dict]:
        """
        Build a connection chain from initial username to related identities.
        
        Args:
            initial_username: Starting username
            found_matches: List of found username matches from enumeration
            max_depth: Maximum depth of connection chain
            
        Returns:
            List of connection chains
        """
        chains = []
        
        # Extract additional identifiers from found matches
        for match in found_matches:
            chain = {
                "start_username": initial_username,
                "connections": [],
            }
            
            platform = match.get("platform", "")
            profile_data = match.get("additional_info", {}).get("profile_data", {})
            
            # Extract emails, linked usernames, etc.
            extracted = self._extract_identifiers(profile_data)
            
            for identifier_type, identifier_value in extracted.items():
                connection = {
                    "type": identifier_type,
                    "value": identifier_value,
                    "source_platform": platform,
                    "depth": 1,
                }
                chain["connections"].append(connection)
            
            if chain["connections"]:
                chains.append(chain)
        
        return chains

    def _extract_identifiers(self, profile_data: Dict) -> Dict[str, str]:
        """
        Extract additional identifiers from profile data.
        
        Args:
            profile_data: Profile data dictionary
            
        Returns:
            Dictionary of identifier types to values
        """
        identifiers = {}
        
        # Common email patterns
        if "email" in profile_data:
            identifiers["email"] = profile_data["email"]
        
        # Look for email in profile bio
        if "bio" in profile_data or "description" in profile_data:
            text = profile_data.get("bio", "") or profile_data.get("description", "")
            email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)
            if email_match:
                identifiers["email"] = email_match.group()
        
        # Extract linked usernames
        if "links" in profile_data:
            for link in profile_data["links"]:
                # Extract username from URL
                url_match = re.search(r'/([a-zA-Z0-9_-]+)(?:/|$)', link)
                if url_match:
                    username = url_match.group(1)
                    if len(username) >= 3:  # Reasonable username length
                        identifiers["linked_username"] = username
        
        return identifiers

    def find_related_usernames(
        self,
        usernames: List[str],
        threshold: int = 80,
    ) -> Dict[str, List[Tuple[str, int]]]:
        """
        Find relationships between usernames based on similarity.
        
        Args:
            usernames: List of usernames to compare
            threshold: Minimum similarity score to consider related
            
        Returns:
            Dictionary mapping username to list of (related_username, score) tuples
        """
        relationships = {}
        
        for i, username1 in enumerate(usernames):
            related = []
            for username2 in usernames:
                if username1 == username2:
                    continue
                
                similarity = self.matcher.calculate_similarity(username1, username2)
                if similarity >= threshold:
                    related.append((username2, similarity))
            
            if related:
                relationships[username1] = sorted(
                    related,
                    key=lambda x: x[1],
                    reverse=True,
                )
        
        return relationships


def get_username_matcher(
    fuzzy_threshold: int = 70,
    max_variations: int = 50,
) -> UsernameMatcher:
    """
    Factory function to get a configured UsernameMatcher instance.
    
    Args:
        fuzzy_threshold: Minimum similarity score for fuzzy matches
        max_variations: Maximum variations to generate
        
    Returns:
        UsernameMatcher instance
    """
    return UsernameMatcher(
        fuzzy_threshold=fuzzy_threshold,
        max_variations=max_variations,
    )


if __name__ == "__main__":
    # Example usage
    matcher = UsernameMatcher()
    
    # Generate variations
    username = "john_smith123"
    variations = matcher.generate_variations(username)
    print(f"Variations for '{username}':")
    for var in variations[:20]:
        print(f"  {var}")
    
    # Extract from email
    email = "john.smith+work@gmail.com"
    from_email = matcher.extract_username_from_email(email)
    print(f"\nUsernames from email '{email}':")
    for u in from_email:
        print(f"  {u}")
    
    # Extract from name
    name = "John Michael Smith"
    from_name = matcher.extract_username_from_name(name)
    print(f"\nUsernames from name '{name}':")
    for u in from_name[:10]:
        print(f"  {u}")
