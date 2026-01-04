import pytest
from unittest.mock import MagicMock, AsyncMock
from backend.modules.github_profiles import GitHubProfileModule
from backend.modules.github_client import GitHubClient

@pytest.fixture
def mock_github_client():
    client = MagicMock(spec=GitHubClient)
    return client

@pytest.mark.asyncio
async def test_get_profile_data(mock_github_client):
    mock_user = MagicMock()
    mock_user.login = "testuser"
    mock_user.name = "Test User"
    mock_user.bio = "A test bio"
    mock_user.location = "Test City"
    mock_user.company = "Test Co"
    mock_user.blog = "https://test.com"
    mock_user.email = "test@test.com"
    mock_user.followers = 10
    mock_user.following = 5
    from datetime import datetime
    mock_user.created_at = datetime(2020, 1, 1)
    mock_user.avatar_url = "https://avatar.com"
    mock_user.organizations_url = "https://orgs.com"
    mock_user.public_repos = 2
    mock_user.public_gists = 1
    
    mock_user.get_orgs.return_value = []
    
    mock_github_client.get_user = AsyncMock(return_value=mock_user)
    
    module = GitHubProfileModule(mock_github_client)
    profile = await module.get_profile_data("testuser")
    
    assert profile["username"] == "testuser"
    assert profile["real_name"] == "Test User"
    assert profile["email"] == "test@test.com"
