import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.modules.adult_sites import AdultSiteScraper
from backend.modules.personals_sites import PersonalsSiteScraper
from backend.models.database import AdultProfile, PersonalsPost, Identity
from datetime import datetime

@pytest.mark.asyncio
async def test_adult_site_scraper_initialization():
    """Test AdultSiteScraper initialization"""
    scraper = AdultSiteScraper()
    assert scraper is not None
    assert scraper.config is not None
    assert scraper.scraping_utils is not None
    assert scraper.async_scraping_utils is not None

@pytest.mark.asyncio
async def test_personals_site_scraper_initialization():
    """Test PersonalsSiteScraper initialization"""
    scraper = PersonalsSiteScraper()
    assert scraper is not None
    assert scraper.config is not None
    assert scraper.scraping_utils is not None
    assert scraper.async_scraping_utils is not None

@pytest.mark.asyncio
@patch('backend.modules.adult_sites.adult_site_scraper._search_platform')
async def test_search_adult_sites(mock_search_platform):
    """Test search_adult_sites method"""
    # Setup mock
    mock_search_platform.return_value = [{"platform": "test", "username": "testuser"}]
    
    scraper = AdultSiteScraper()
    results = await scraper.search_adult_sites("testuser")
    
    assert len(results) == 1
    assert results[0]["platform"] == "test"
    assert results[0]["username"] == "testuser"

@pytest.mark.asyncio
@patch('backend.modules.personals_sites.personals_site_scraper._search_site')
async def test_search_personals_sites(mock_search_site):
    """Test search_personals_sites method"""
    # Setup mock
    mock_search_site.return_value = [{"site": "test", "post_title": "Test Post"}]
    
    scraper = PersonalsSiteScraper()
    results = await scraper.search_personals_sites("testkeyword")
    
    assert len(results) == 1
    assert results[0]["site"] == "test"
    assert results[0]["post_title"] == "Test Post"

@pytest.mark.asyncio
@patch('backend.modules.adult_sites.AsyncSessionLocal')
async def test_store_profile_data(mock_session):
    """Test storing adult profile data"""
    # Setup mock session
    mock_session_instance = AsyncMock()
    mock_session.return_value.__aenter__.return_value = mock_session_instance
    
    # Mock execute to return None (no existing profile)
    mock_session_instance.execute.return_value.fetchone.return_value = None
    
    scraper = AdultSiteScraper()
    
    profile_data = {
        "platform": "test",
        "username": "testuser",
        "profile_url": "https://test.com/user",
        "bio": "Test bio",
        "join_date": datetime.utcnow().isoformat(),
        "profile_image_url": "https://test.com/image.jpg",
        "linked_accounts": ["https://twitter.com/user"],
        "confidence_score": 0.95
    }
    
    # This should not raise an exception
    await scraper._store_profile_data(profile_data)
    
    # Verify session operations
    mock_session_instance.execute.assert_called()
    mock_session_instance.commit.assert_called()

@pytest.mark.asyncio
@patch('backend.modules.personals_sites.AsyncSessionLocal')
async def test_store_post_data(mock_session):
    """Test storing personals post data"""
    # Setup mock session
    mock_session_instance = AsyncMock()
    mock_session.return_value.__aenter__.return_value = mock_session_instance
    
    # Mock execute to return None (no existing identity)
    mock_session_instance.execute.return_value.fetchone.return_value = None
    
    scraper = PersonalsSiteScraper()
    
    post_data = {
        "site": "test",
        "post_id": "test123",
        "post_title": "Test Post",
        "post_content": "Test content",
        "phone_number": "+1234567890",
        "email": "test@example.com",
        "location": "Test City",
        "post_date": datetime.utcnow().isoformat(),
        "image_urls": ["https://test.com/image.jpg"],
        "confidence_score": 0.85
    }
    
    # This should not raise an exception
    await scraper._store_post_data(post_data)
    
    # Verify session operations
    mock_session_instance.execute.assert_called()
    mock_session_instance.commit.assert_called()

def test_confidence_score_calculation():
    """Test confidence score calculation"""
    scraper = AdultSiteScraper()
    
    # Test exact match
    profile_data = {
        "username": "testuser",
        "bio": "This is testuser's bio",
        "profile_url": "https://test.com/testuser"
    }
    
    score = scraper._calculate_confidence_score(profile_data, "testuser")
    assert 0.0 <= score <= 1.0
    assert score > 0.5  # Should be high for exact match

def test_personals_confidence_score_calculation():
    """Test personals confidence score calculation"""
    scraper = PersonalsSiteScraper()
    
    # Test exact phone match
    post_data = {
        "post_title": "Test Post",
        "post_content": "Contact me at +1234567890",
        "phone_number": "+1234567890",
        "email": "test@example.com",
        "location": "Test City"
    }
    
    score = scraper._calculate_confidence_score(post_data, "+1234567890")
    assert 0.0 <= score <= 1.0
    assert score > 0.8  # Should be high for exact phone match

def test_scraping_utils():
    """Test scraping utilities"""
    from backend.utils.scraping_utils import ScrapingUtils
    
    utils = ScrapingUtils()
    
    # Test user agent generation
    user_agent = utils.get_user_agent()
    assert isinstance(user_agent, str)
    assert len(user_agent) > 0
    
    # Test headers
    headers = utils.get_headers()
    assert "User-Agent" in headers
    assert "Accept" in headers
    
    # Test phone number extraction
    text = "Call me at 123-456-7890 or +1 (987) 654-3210"
    phones = utils.extract_phone_numbers(text)
    assert len(phones) >= 2
    
    # Test email extraction
    text = "Email me at test@example.com or contact@domain.org"
    emails = utils.extract_emails(text)
    assert len(emails) >= 2
    
    # Test phone normalization
    normalized = utils.normalize_phone_number("123-456-7890")
    assert normalized == "+11234567890"
    
    # Test email normalization
    normalized_email = utils.normalize_email("  Test@Example.COM  ")
    assert normalized_email == "test@example.com"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])