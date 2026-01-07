"""
Unit tests for Username Matching Module
"""

import pytest
from backend.modules.username_matching import (
    UsernameMatcher,
    CrossReferenceEngine,
    MatchType,
    UsernameVariation,
)


class TestUsernameMatcher:
    """Tests for UsernameMatcher"""
    
    @pytest.fixture
    def matcher(self):
        """Fixture for UsernameMatcher instance"""
        return UsernameMatcher(fuzzy_threshold=70, max_variations=50)
    
    def test_initialization(self, matcher):
        """Test matcher initialization"""
        assert matcher.fuzzy_threshold == 70
        assert matcher.max_variations == 50
    
    def test_generate_variations_basic(self, matcher):
        """Test basic variation generation"""
        username = "john_smith"
        variations = matcher.generate_variations(username)
        
        assert len(variations) > 0
        assert username.lower() in variations
        assert len(variations) <= matcher.max_variations
    
    def test_generate_variations_separator_variations(self, matcher):
        """Test separator variations"""
        username = "john_smith"
        variations = matcher.generate_variations(
            username,
            match_types=[MatchType.VARIATION],
        )
        
        # Should include different separators
        assert any('_' in v or '.' in v or '-' in v for v in variations)
    
    def test_generate_variations_leet_speak(self, matcher):
        """Test leet speak variations"""
        username = "john"
        variations = matcher.generate_variations(
            username,
            match_types=[MatchType.VARIATION],
        )
        
        # Should include some leet speak variations
        assert any(any(c.isdigit() for c in v) for v in variations)
    
    def test_generate_variations_case_variations(self, matcher):
        """Test case variations"""
        username = "JohnSmith"
        variations = matcher.generate_variations(
            username,
            match_types=[MatchType.VARIATION],
        )
        
        # Should include lowercase version
        assert username.lower() in variations
    
    def test_generate_variations_empty_username(self, matcher):
        """Test variation generation with empty username"""
        variations = matcher.generate_variations("")
        assert len(variations) == 0
    
    def test_extract_username_from_email_basic(self, matcher):
        """Test extracting username from email"""
        email = "john.smith@gmail.com"
        usernames = matcher.extract_username_from_email(email)
        
        assert "john.smith" in usernames
        assert "johnsmith" in usernames
        assert len(usernames) > 0
    
    def test_extract_username_from_email_with_plus(self, matcher):
        """Test extracting username from email with plus notation"""
        email = "john.smith+work@gmail.com"
        usernames = matcher.extract_username_from_email(email)
        
        assert "john.smith" in usernames
        assert "john.smith+work" in usernames
        # Plus removal should be included
        assert any("work" not in u for u in usernames if "+" not in u)
    
    def test_extract_username_from_email_with_numbers(self, matcher):
        """Test extracting username from email with numbers"""
        email = "john.smith123@gmail.com"
        usernames = matcher.extract_username_from_email(email)
        
        assert "john.smith123" in usernames
        assert "john.smith" in usernames  # Should include version without numbers
    
    def test_extract_username_from_name_basic(self, matcher):
        """Test extracting username from name"""
        name = "John Doe"
        usernames = matcher.extract_username_from_name(name)
        
        assert "johndoe" in usernames
        assert "john.doe" in usernames or "john_doe" in usernames
        assert len(usernames) > 0
    
    def test_extract_username_from_name_middle_name(self, matcher):
        """Test extracting username from name with middle name"""
        name = "John Michael Smith"
        usernames = matcher.extract_username_from_name(name)
        
        assert "johnsmith" in usernames
        assert len(usernames) > 5  # Should generate multiple variations
    
    def test_extract_username_from_phone(self, matcher):
        """Test extracting username from phone"""
        phone = "+1-555-123-4567"
        usernames = matcher.extract_username_from_phone(phone)
        
        assert len(usernames) > 0
        # Should include last 4 digits
        assert any(len(u) == 4 and u.isdigit() for u in usernames)
    
    def test_calculate_similarity_exact(self, matcher):
        """Test similarity calculation for exact match"""
        score = matcher.calculate_similarity("john_doe", "john_doe")
        assert score == 100
    
    def test_calculate_similarity_case_insensitive(self, matcher):
        """Test similarity calculation is case insensitive"""
        score = matcher.calculate_similarity("John_Doe", "john_doe")
        assert score == 100
    
    def test_calculate_similarity_similar(self, matcher):
        """Test similarity calculation for similar usernames"""
        score = matcher.calculate_similarity("john_doe", "john_doe1")
        assert score > 80
    
    def test_calculate_similarity_different(self, matcher):
        """Test similarity calculation for different usernames"""
        score = matcher.calculate_similarity("john_doe", "jane_smith")
        assert score < 50
    
    def test_calculate_similarity_empty(self, matcher):
        """Test similarity calculation with empty strings"""
        score = matcher.calculate_similarity("", "john_doe")
        assert score == 0
    
    def test_fuzzy_match(self, matcher):
        """Test fuzzy matching against candidates"""
        username = "john_doe"
        candidates = ["john_doe", "john_doe1", "jane_smith", "john.smith"]
        
        matches = matcher.fuzzy_match(username, candidates)
        
        assert len(matches) > 0
        assert all(score >= matcher.fuzzy_threshold for _, score in matches)
        # Exact match should be first
        assert matches[0][0] == "john_doe"
        assert matches[0][1] == 100
    
    def test_fuzzy_match_empty_candidates(self, matcher):
        """Test fuzzy matching with empty candidates"""
        matches = matcher.fuzzy_match("john_doe", [])
        assert len(matches) == 0
    
    def test_fuzzy_match_custom_threshold(self, matcher):
        """Test fuzzy matching with custom threshold"""
        username = "john_doe"
        candidates = ["john_doe1", "john_doe2"]
        
        matches_high = matcher.fuzzy_match(username, candidates, threshold=90)
        matches_low = matcher.fuzzy_match(username, candidates, threshold=50)
        
        # Lower threshold should return more matches
        assert len(matches_low) >= len(matches_high)
    
    def test_exact_match(self, matcher):
        """Test exact matching"""
        username = "John_Doe"
        candidates = ["john_doe", "jane_smith", "JOHN_DOE"]
        
        matches = matcher.exact_match(username, candidates)
        
        # Should match case-insensitively
        assert "john_doe" in matches
        assert "JOHN_DOE" in matches
        assert "jane_smith" not in matches
    
    def test_get_match_type_exact(self, matcher):
        """Test determining match type for exact match"""
        match_type = matcher.get_match_type("john_doe", "john_doe", 100)
        assert match_type == MatchType.EXACT
    
    def test_get_match_type_fuzzy(self, matcher):
        """Test determining match type for fuzzy match"""
        match_type = matcher.get_match_type("john_doe", "john_doe1", 92)
        assert match_type == MatchType.FUZZY
    
    def test_get_match_type_variation(self, matcher):
        """Test determining match type for separator variation"""
        match_type = matcher.get_match_type("john_doe", "john.doe", 80)
        assert match_type == MatchType.VARIATION
    
    def test_get_match_type_pattern(self, matcher):
        """Test determining match type for pattern match"""
        match_type = matcher.get_match_type("john_doe", "jane_smith", 30)
        assert match_type == MatchType.PATTERN


class TestCrossReferenceEngine:
    """Tests for CrossReferenceEngine"""
    
    @pytest.fixture
    def engine(self):
        """Fixture for CrossReferenceEngine instance"""
        return CrossReferenceEngine()
    
    def test_initialization(self, engine):
        """Test engine initialization"""
        assert engine.matcher is not None
        assert isinstance(engine.matcher, UsernameMatcher)
    
    @pytest.mark.asyncio
    async def test_build_identity_chain_empty(self, engine):
        """Test building identity chain with no matches"""
        chain = await engine.build_identity_chain("test_user", [])
        
        assert isinstance(chain, list)
        assert len(chain) == 0
    
    @pytest.mark.asyncio
    async def test_build_identity_chain_basic(self, engine):
        """Test building identity chain with basic matches"""
        matches = [
            {
                "platform": "twitter",
                "additional_info": {
                    "profile_data": {
                        "bio": "Check out my email at test@example.com",
                    }
                }
            }
        ]
        
        chains = await engine.build_identity_chain("test_user", matches)
        
        assert len(chains) > 0
        assert chains[0]["start_username"] == "test_user"
    
    @pytest.mark.asyncio
    async def test_extract_identifiers_from_email(self, engine):
        """Test extracting email identifiers"""
        profile_data = {
            "email": "test@example.com",
            "bio": "My username is @john_doe",
        }
        
        identifiers = engine._extract_identifiers(profile_data)
        
        assert "email" in identifiers
        assert identifiers["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_extract_identifiers_from_bio(self, engine):
        """Test extracting identifiers from bio"""
        profile_data = {
            "bio": "Contact me at john@example.com",
            "links": ["https://twitter.com/john_doe"],
        }
        
        identifiers = engine._extract_identifiers(profile_data)
        
        assert "email" in identifiers
        assert "linked_username" in identifiers
    
    def test_find_related_usernames_empty(self, engine):
        """Test finding related usernames with empty list"""
        related = engine.find_related_usernames([])
        assert len(related) == 0
    
    def test_find_related_usernames_basic(self, engine):
        """Test finding related usernames"""
        usernames = ["john_doe", "john.doe", "jane_smith", "j_doe"]
        
        related = engine.find_related_usernames(usernames, threshold=70)
        
        # Should find relationships between similar usernames
        assert len(related) > 0
        assert all(score >= 70 for _, matches in related.items() for _, score in matches)
    
    def test_find_related_usernames_threshold(self, engine):
        """Test finding related usernames with different thresholds"""
        usernames = ["john_doe", "john_doe1"]
        
        related_high = engine.find_related_usernames(usernames, threshold=90)
        related_low = engine.find_related_usernames(usernames, threshold=50)
        
        # Lower threshold should find more relationships
        total_related_high = sum(len(m) for m in related_high.values())
        total_related_low = sum(len(m) for m in related_low.values())
        assert total_related_low >= total_related_high


def test_get_username_matcher():
    """Test username matcher factory function"""
    matcher = get_username_matcher(fuzzy_threshold=80, max_variations=30)
    
    assert isinstance(matcher, UsernameMatcher)
    assert matcher.fuzzy_threshold == 80
    assert matcher.max_variations == 30
