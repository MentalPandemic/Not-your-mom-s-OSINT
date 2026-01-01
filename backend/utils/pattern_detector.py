import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class DetectedPattern:
    pattern: str
    confidence: float
    components: Dict[str, str]


class PatternDetector:
    """Detects common patterns in usernames for intelligent matching"""
    
    def __init__(self):
        self.patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> List[Dict[str, Any]]:
        """Compile regex patterns for username analysis"""
        return [
            {
                'name': 'firstname_lastname',
                'regex': r'^([a-zA-Z]+)[_\-\.]([a-zA-Z]+)$',
                'components': ['first', 'last'],
                'description': 'First name and last name separated by separator'
            },
            {
                'name': 'firstname_initial_lastname',
                'regex': r'^([a-zA-Z])[_.-]?([a-zA-Z]+)$',
                'components': ['first_initial', 'last'],
                'description': 'First initial and last name'
            },
            {
                'name': 'name_number',
                'regex': r'^([a-zA-Z_\-]+)(\d+)$',
                'components': ['name', 'number'],
                'description': 'Name followed by numbers'
            },
            {
                'name': 'year_suffix',
                'regex': r'^([a-zA-Z_\-]+)(19\d{2}|20\d{2})$',
                'components': ['name', 'year'],
                'description': 'Name followed by year (1900-2099)'
            },
            {
                'name': 'repeated_characters',
                'regex': r'^.*(.)\1{2,}.*$',
                'components': ['character'],
                'description': 'Username with repeated characters'
            },
            {
                'name': 'company_email_style',
                'regex': r'^([a-zA-Z])[.\-_]?([a-zA-Z]+)[.\-_]?(\d*)$',
                'components': ['first_initial', 'last', 'number'],
                'description': 'Corporate email style username'
            },
            {
                'name': 'l33t_speak',
                'regex': r'.*[0|\-\+\=\@][a-zA-Z\d_\-\.]*',
                'components': [],
                'description': 'Leet speak patterns detected'
            },
            {
                'name': 'location_based',
                'regex': r'^([a-zA-Z_\-]+)(nyc|la|sf|uk|usa|au|ca|tx|ny|fl)(\d*)$',
                'components': ['name', 'location', 'number'],
                'description': 'Username with location abbreviation'
            },
            {
                'name': 'role_based',
                'regex': r'^([a-zA-Z_\-\.@]+)(admin|root|sys|dev|tech|mgr|ceo|ct)(\d*)$',
                'components': ['name', 'role', 'number'],
                'description': 'Username with role/position'
            },
            {
                'name': 'uuid_style',
                'regex': r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
                'components': [],
                'description': 'UUID format username'
            },
            {
                'name': 'phone_style',
                'regex': r'^\+?[1-9]\d{1,14}$',
                'components': [],
                'description': 'Phone number format'
            },
        ]
    
    def detect_patterns(self, username: str) -> List[Dict[str, Any]]:
        """
        Detect patterns in a username and return structured analysis
        
        Args:
            username: Username string to analyze
            
        Returns:
            List of detected patterns with components
        """
        detected = []
        username_lower = username.lower()
        
        for pattern_def in self.patterns:
            try:
                match = re.match(pattern_def['regex'], username)
                if match:
                    pattern_info = {
                        'type': pattern_def['name'],
                        'confidence': 0.7,  # Base confidence
                        'components': {},
                        'description': pattern_def['description']
                    }
                    
                    # Extract components if pattern has groups
                    if pattern_def['components'] and match.groups():
                        for i, component_name in enumerate(pattern_def['components']):
                            if i < len(match.groups()):
                                pattern_info['components'][component_name] = match.group(i + 1)
                    
                    # Boost confidence for exact matches
                    if match.group(0) == username:
                        pattern_info['confidence'] = 0.95
                    
                    detected.append(pattern_info)
                    
            except Exception as e:
                # Continue processing other patterns if one fails
                continue
        
        # Add special pattern detection
        self._detect_special_patterns(username, detected)
        
        return detected
    
    def _detect_special_patterns(self, username: str, detected: List[Dict[str, Any]]):
        """Detect special patterns not covered by regex"""
        username_lower = username.lower()
        
        # Common name patterns
        common_names = [
            'john', 'jane', 'mike', 'sarah', 'david', 'emma', 'alex', 'chris', 
            'lisa', 'mark', 'amy', 'tom', 'jen', 'paul', 'sam', 'ann'
        ]
        
        # Check for common first names
        for name in common_names:
            if username_lower.startswith(name):
                remaining = username_lower[len(name):]
                if remaining and (remaining[0] in '_-.@' or remaining.isdigit()):
                    detected.append({
                        'type': 'common_name',
                        'confidence': 0.85,
                        'components': {
                            'name': name,
                            'suffix': remaining
                        },
                        'description': f'Common first name with suffix'
                    })
        
        # Check for repeated patterns
        for length in range(2, 6):
            if len(username) >= length * 2:
                chunk = username[:length]
                if username == chunk * (len(username) // length):
                    detected.append({
                        'type': 'repeated_pattern',
                        'confidence': 0.9,
                        'components': {
                            'pattern': chunk,
                            'repetitions': len(username) // length
                        },
                        'description': f'Username is repeated pattern "{chunk}"'
                    })
        
        # Check for palindrome patterns
        if len(username) >= 4 and username == username[::-1]:
            detected.append({
                'type': 'palindrome',
                'confidence': 1.0,
                'components': {},
                'description': 'Username is a palindrome'
            })
        
        # Check for keyboard patterns (like 'qwerty', 'asdf')
        keyboard_patterns = [
            'qwerty', 'asdf', 'zxcv', 'qaz', 'wsx', 'edc', 'rfv', 'tgb', 
            'yhn', 'ujm', 'qazwsx', 'edc', 'rfv', 'tgb', 'yhn', 'ujm'
        ]
        
        for pattern in keyboard_patterns:
            if pattern in username_lower:
                detected.append({
                    'type': 'keyboard_pattern',
                    'confidence': 0.8,
                    'components': {
                        'pattern': pattern
                    },
                    'description': f'Contains keyboard pattern "{pattern}"'
                })
        
        # Check for sequential numbers
        sequential = self._find_sequential_numbers(username_lower)
        if sequential:
            detected.append({
                'type': 'sequential_numbers',
                'confidence': 0.75,
                'components': {
                    'sequence': sequential
                },
                'description': f'Contains sequential numbers "{sequential}"'
            })
    
    def _find_sequential_numbers(self, text: str) -> str:
        """Find sequential number patterns in text"""
        digits = ''.join(filter(str.isdigit, text))
        
        if len(digits) >= 3:
            for i in range(len(digits) - 2):
                seq = digits[i:i+3]
                if all(int(seq[j]) + 1 == int(seq[j+1]) for j in range(2)):
                    return seq
                if all(int(seq[j]) - 1 == int(seq[j+1]) for j in range(2)):
                    return seq
        
        return ''
    
    def extract_name_components(self, username: str) -> Dict[str, Any]:
        """
        Extract name components from username patterns
        
        Returns:
            Dictionary with extracted name components and metadata
        """
        patterns = self.detect_patterns(username)
        components = {
            'first_name': None,
            'last_name': None,
            'base_name': None,
            'suffix': None,
            'digits': None,
            'confidence': 0.0,
            'pattern_type': None
        }
        
        for pattern in patterns:
            if pattern['confidence'] > components['confidence']:
                components['confidence'] = pattern['confidence']
                components['pattern_type'] = pattern['type']
                
                comps = pattern['components']
                
                if 'first' in comps:
                    components['first_name'] = comps['first']
                if 'last' in comps:
                    components['last_name'] = comps['last']
                if 'name' in comps:
                    components['base_name'] = comps['name']
                if 'number' in comps:
                    components['digits'] = comps['number']
                
                # Handle various separator patterns
                if components['base_name']:
                    base_name = components['base_name']
                    if '_' in base_name:
                        parts = base_name.split('_', 1)
                        if len(parts) == 2 and not components['first_name']:
                            components['first_name'] = parts[0]
                            components['last_name'] = parts[1]
                    elif '-' in base_name:
                        parts = base_name.split('-', 1)
                        if len(parts) == 2 and not components['first_name']:
                            components['first_name'] = parts[0]
                            components['last_name'] = parts[1]
        
        # If we have first.name pattern and no last name, split at last separator
        if components['base_name'] and not components['last_name']:
            for sep in ['.', '-', '_']:
                if sep in components['base_name']:
                    parts = components['base_name'].rsplit(sep, 1)
                    if len(parts) == 2:
                        components['first_name'] = parts[0]
                        components['last_name'] = parts[1]
                        break
        
        return components
    
    def generate_variations(self, username: str, max_variations: int = 10) -> List[str]:
        """
        Generate username variations based on detected patterns
        
        Args:
            username: Original username
            max_variations: Maximum number of variations to generate
            
        Returns:
            List of username variations
        """
        variations = [username]
        components = self.extract_name_components(username)
        
        # Generate variations based on detected pattern
        if components['pattern_type'] == 'firstname_lastname':
            if components['first_name'] and components['last_name']:
                f, l = components['first_name'], components['last_name']
                variations.extend([
                    f"{f}.{l}",
                    f"{f}-{l}",
                    f"{f}_{l}",
                    f"{f[0]}{l}",
                    f"{l}{f[0]}",
                ])
        
        elif components['pattern_type'] == 'name_number':
            if components['base_name'] and components['digits']:
                base, digits = components['base_name'], components['digits']
                variations.extend([
                    f"{base}_{digits}",
                    f"{base}-{digits}",
                    f"{base}.{digits}",
                ])
        
        elif components['first_name'] and not components['last_name']:
            # Only first name detected
            f = components['first_name']
            variations.extend([
                f"{f}123",
                f"{f}2024",
                f"real_{f}",
                f"_{f}_",
            ])
        
        # Filter duplicates and limit results
        variations = list(set(variations))[:max_variations]
        
        return variations
    
    def is_suspicious_pattern(self, username: str) -> bool:
        """
        Detect if a username has suspicious patterns that might indicate spam/invalid
        
        Returns:
            True if pattern seems suspicious
        """
        username_lower = username.lower()
        
        # Check for excessive repetition
        if re.search(r'(.)\1{4,}', username):
            return True
        
        # Check for random string patterns (common in bots)
        if re.match(r'^[a-z]{8,15}\d{2,4}$', username_lower):
            return True
        
        # Check for suspicious word combinations
        suspicious_words = ['bot', 'spam', 'fake', 'test', 'temp', 'anonymous', 'user']
        if any(word in username_lower for word in suspicious_words) and len(username) > 15:
            return True
        
        # Check for UUID-like patterns (common in temporary accounts)
        if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', username_lower):
            return True
        
        return False