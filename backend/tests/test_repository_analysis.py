import pytest
from unittest.mock import MagicMock, AsyncMock
from backend.modules.repository_analysis import RepositoryAnalysisModule
from backend.modules.github_client import GitHubClient

@pytest.fixture
def mock_github_client():
    client = MagicMock(spec=GitHubClient)
    return client

@pytest.mark.asyncio
async def test_get_repositories(mock_github_client):
    mock_user = MagicMock()
    mock_repo = MagicMock()
    mock_repo.name = "test-repo"
    mock_repo.full_name = "testuser/test-repo"
    mock_repo.description = "A test repo"
    from datetime import datetime
    mock_repo.created_at = datetime(2020, 1, 1)
    mock_repo.updated_at = datetime(2020, 1, 2)
    mock_repo.stargazers_count = 5
    mock_repo.forks_count = 2
    mock_repo.watchers_count = 3
    mock_repo.language = "Python"
    mock_repo.license.name = "MIT"
    mock_repo.html_url = "https://github.com/testuser/test-repo"
    
    mock_user.get_repos.return_value = [mock_repo]
    mock_github_client.get_user = AsyncMock(return_value=mock_user)
    
    module = RepositoryAnalysisModule(mock_github_client)
    repos = await module.get_repositories("testuser")
    
    assert len(repos) == 1
    assert repos[0]["name"] == "test-repo"
    assert repos[0]["language"] == "Python"
