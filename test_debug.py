from fastapi.testclient import TestClient
from backend.main import create_app
from unittest.mock import Mock, AsyncMock
import pytest

app = create_app()
app.state.username_service = Mock()
app.state.username_service.enumerate_username = AsyncMock(return_value=[])
app.state.cache_manager = Mock()
app.state.cache_manager.get = AsyncMock(return_value=None)
app.state.db_manager = Mock()
app.state.rate_limiter = Mock()
app.state.rate_limiter.check_rate_limit = AsyncMock(return_value=(True, {}))

client = TestClient(app)
response = client.post(
    "/api/search/username",
    json={"username": "johndoe"}
)
print(response.status_code)
print(response.json())
