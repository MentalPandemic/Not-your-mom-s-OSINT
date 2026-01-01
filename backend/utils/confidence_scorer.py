from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
import re


@dataclass
class ConfidenceFactors:
    platform_weight: float
    match_type_weight: float
    pattern_weight: float
    metadata_weight: float
    temporal_weight: float
    similarity_weight: float


class ConfidenceScorer:
    """Calculate confidence scores for username matches"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_confidence = config.get('base_confidence', 0.5)
        
        # Weight factors for different components
        self.weights = ConfidenceFactors(
            platform_weight=config.get('platform_weight', 0.2),
            match_type_weight=config.get('match_type_weight', 0.25),
            pattern_weight=config.get('pattern_weight', 0.15),
            metadata_weight=config.get('metadata_weight', 0.2),
            temporal_weight=config.get('temporal_weight', 0.1),
            similarity_weight=config.get('similarity_weight', 0.1)
        )
        
        # Platform reliability scores (based on API quality, data freshness, etc.)
        self.platform_reliability = {
            'github': 0.95,
            'twitter': 0.90,
            'linkedin': 0.85,
            'gitlab': 0.90,
            'keybase': 0.80,
            'reddit': 0.75,
            'instagram': 0.70,
            'facebook': 0.65,
            'telegram': 0.80,
            'tiktok': 0.60,
            'youtube': 0.70,
            'pinterest': 0.65,
            'medium': 0.75,
            'stackoverflow': 0.85,
            'twitch': 0.70,
            'snapchat': 0.60,
            'default': 0.50
        }
        
        # Match type confidences
        self.match_type_confidence = {
            'exact': 1.0,
            'fuzzy': 0.7,
            'pattern': 0.8,
            'reverse': 0.6
        }
        
        # Pattern confidence boosts
        self.pattern_scores = {
            'firstname_lastname': 0.2,
            'firstname_initial_lastname': 0.15,
            'name_number': 0.1,
            'year_suffix': 0.05,
            'common_name': 0.05
        }
    
    def calculate_score(
        self, 
        match: Any, 
        search_username: str,
        search_email: Optional[str] = None,
        search_phone: Optional[str] = None
    ) -> float:
        """
        Calculate overall confidence score for a match
        
        Args:
            match: Match candidate object
            search_username: Original search username
            search_email: Original search email (if provided)
            search_phone: Original search phone (if provided)
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        score = self.base_confidence
        
        # Factor 1: Platform reliability
        platform_score = self._calculate_platform_score(match.platform_name)
        score += platform_score * self.weights.platform_weight
        
        # Factor 2: Match type confidence
        match_type_score = self._calculate_match_type_score(match.match_type)
        score += match_type_score * self.weights.match_type_weight
        
        # Factor 3: Pattern analysis
        pattern_score = self._calculate_pattern_score(match.username, search_username)
        score += pattern_score * self.weights.pattern_weight
        
        # Factor 4: Metadata quality
        metadata_score = self._calculate_metadata_score(match.metadata, search_email, search_phone)
        score += metadata_score * self.weights.metadata_weight
        
        # Factor 5: Temporal factors
        temporal_score = self._calculate_temporal_score()
        score += temporal_score * self.weights.temporal_weight
        
        # Factor 6: String similarity
        similarity_score = self._calculate_similarity_score(match.username, search_username)
        score += similarity_score * self.weights.similarity_weight
        
        # Final adjustments
        final_score = self._apply_final_adjustments(score, match)
        
        return min(max(final_score, 0.0), 1.0)
    
    def _calculate_platform_score(self, platform_name: str) -> float:
        """Calculate score based on platform reliability"""
        return self.platform_reliability.get(platform_name.lower(), self.platform_reliability['default'])
    
    def _calculate_match_type_score(self, match_type: str) -> float:
        """Calculate score based on match type"""
        return self.match_type_confidence.get(match_type, 0.5)
    
    def _calculate_pattern_score(self, matched_username: str, search_username: str) -> float:
        """Calculate score based on username pattern analysis"""
        score = 0.0
        
        # Check for name patterns
        patterns = self._analyze_name_patterns(matched_username, search_username)
        
        for pattern_type in patterns:
            score += self.pattern_scores.get(pattern_type, 0.0)
        
        # Normalize to 0-1 range
        return min(score, 1.0)
    
    def _calculate_metadata_score(
        self, 
        metadata: Optional[Dict], 
        search_email: Optional[str], 
        search_phone: Optional[str]
    ) -> float:
        """Calculate score based on metadata quality and consistency"""
        if not metadata:
            return 0.0
        
        score = 0.0
        
        # Check email consistency
        if search_email and metadata.get('email'):
            if metadata['email'].lower() == search_email.lower():
                score += 0.8  # Strong boost for email match
            elif search_email.split('@')[0].lower() in metadata['email'].lower():
                score += 0.3  # Partial match
        
        # Check phone consistency
        if search_phone and metadata.get('phone'):
            # Normalize phone numbers for comparison
            normalized_search = re.sub(r'[^\d]', '', search_phone)
            normalized_found = re.sub(r'[^\d]', '', metadata['phone'])
            
            if normalized_search == normalized_found:
                score += 0.9  # Strong boost for phone match
            elif normalized_search[-7:] == normalized_found[-7:]:  # Last 7 digits match
                score += 0.4  # Partial match
        
        # Metadata quality indicators
        quality_indicators = [
            'full_name',
            'bio',
            'location',
            'avatar_url',
            'followers_count',
            'created_date'
        ]
        
        for indicator in quality_indicators:
            if indicator in metadata and metadata[indicator]:
                score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_temporal_score(self) -> float:
        """Calculate score based on temporal factors"""
        # For now, return a neutral score
        # In production, this would consider:
        # - Profile age (older profiles are more reliable)
        # - Last activity date
        # - Account creation patterns
        return 0.5
    
    def _calculate_similarity_score(self, username1: str, username2: str) -> float:
        """Calculate string similarity score"""
        if username1 == username2:
            return 1.0
        
        # Calculate character overlap
        set1 = set(username1.lower())
        set2 = set(username2.lower())
        
        overlap = len(set1.intersection(set2))
        total_chars = len(set1.union(set2))
        
        if total_chars == 0:
            return 0.0
        
        char_similarity = overlap / total_chars
        
        # Consider length similarity
        len_diff = abs(len(username1) - len(username2))
        max_len = max(len(username1), len(username2))
        
        if max_len > 0:
            len_similarity = 1.0 - (len_diff / max_len)
        else:
            len_similarity = 0.0
        
        # Weight character similarity more than length similarity
        return (char_similarity * 0.7) + (len_similarity * 0.3)
    
    def _analyze_name_patterns(self, username1: str, username2: str) -> List[str]:
        """Analyze name patterns between two usernames"""
        patterns = []
        
        # Check for similar name components
        name1 = re.sub(r'[^a-zA-Z]', ' ', username1.lower())
        name2 = re.sub(r'[^a-zA-Z]', ' ', username2.lower())
        
        words1 = name1.split()
        words2 = name2.split()
        
        # Check for shared name components
        if any(word in words2 for word in words1):
            patterns.append('shared_name_components')
        
        # Check for first name initial patterns
        if len(words1) >= 2 and len(words2) >= 2:
            if words1[0][0] == words2[0][0]:  # Same first initial
                patterns.append('same_first_initial')
            
            if words1[-1] == words2[-1]:  # Same last name
                patterns.append('same_last_name')
        
        return patterns
    
    def _apply_final_adjustments(self, score: float, match: Any) -> float:
        """Apply final adjustments to the confidence score"""
        # Penalize for known suspicious patterns
        if hasattr(match, 'username'):
            if self._is_suspicious_pattern(match.username):
                score *= 0.7  # 30% penalty for suspicious patterns
        
        # Boost for high-confidence platforms
        if match.match_type == 'exact':
            score = min(score + 0.1, 1.0)
        
        # Normalize based on data freshness (if available)
        if hasattr(match, 'metadata') and match.metadata:
            created_date = match.metadata.get('created_date')
            if created_date:
                # Boost older accounts (more trustworthy)
                try:
                    account_age = datetime.utcnow() - created_date
                    if account_age.days > 365:  # Account is over a year old
                        score = min(score + 0.05, 1.0)
                except:
                    pass
        
        return score
    
    def _is_suspicious_pattern(self, username: str) -> bool:
        """Check if username has suspicious patterns"""
        # Similar to pattern detector but focused on spam/scam indicators
        suspicious_indicators = [
            r'bot\d*$',  # Ends with 'bot' plus optional numbers
            r'spam\d*$',  # Ends with 'spam'
            r'fake\d*$',  # Ends with 'fake'
            r'test\d*$',  # Ends with 'test'
            r'^[a-z]{8,12}\d{3,6}$',  # Random letters + numbers (bot pattern)
            r'^(.)\1{3,}\d{2,4}$',  # Repeated character + numbers
        ]
        
        username_lower = username.lower()
        
        for pattern in suspicious_indicators:
            if re.match(pattern, username_lower):
                return True
        
        return False
    
    def get_explanation(self, score: float, factors: Dict[str, float]) -> Dict[str, Any]:
        """Generate human-readable explanation of confidence score"""
        explanation = {
            'overall_score': round(score, 3),
            'breakdown': {},
            'interpretation': self._interpret_score(score)
        }
        
        for factor_name, factor_score in factors.items():
            weight = getattr(self.weights, f'{factor_name}_weight', 0.1)
            contribution = factor_score * weight
            
            explanation['breakdown'][factor_name] = {
                'raw_score': round(factor_score, 3),
                'weight': weight,
                'contribution': round(contribution, 3)
            }
        
        return explanation
    
    def _interpret_score(self, score: float) -> str:
        """Provide textual interpretation of confidence score"""
        if score >= 0.9:
            return "Very High Confidence - Strong evidence this is a correct match"
        elif score >= 0.7:
            return "High Confidence - Likely to be a correct match"
        elif score >= 0.5:
            return "Medium Confidence - Possible match, verify with additional data"
        elif score >= 0.3:
            return "Low Confidence - Weak match, requires verification"
        else:
            return "Very Low Confidence - Unlikely to be a correct match"