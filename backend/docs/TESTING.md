# Username Enumeration API - Testing Documentation

## Overview

This document provides comprehensive information about the testing suite for the Username Enumeration API, including how to run tests, what is being tested, and how to write new tests.

## Test Structure

```
backend/tests/
├── __init__.py
├── test_username_enum_api.py    # API endpoint tests
├── test_database.py              # Database operation tests
├── test_rate_limiting.py         # Rate limiting tests
├── test_caching.py              # Caching functionality tests
└── test_integration.py           # End-to-end integration tests
```

## Test Categories

### 1. API Endpoint Tests (`test_username_enum_api.py`)

Tests all API endpoints with various input scenarios:

- **TestUsernameSearchEndpoint**
  - Successful username search
  - Pagination
  - Input validation
  - Cache hits/misses
  - Rate limiting

- **TestReverseLookupEndpoint**
  - Email-based lookup
  - Phone-based lookup
  - Input validation

- **TestFuzzyMatchEndpoint**
  - Different tolerance levels
  - Pagination
  - Invalid inputs

- **TestGetUsernameResults**
  - Result retrieval
  - Metadata handling

- **TestGetIdentityChain**
  - Identity chain building
  - Max depth parameter

### 2. Database Tests (`test_database.py`)

Tests database operations:

- **TestPostgreSQLManager**
  - Connection initialization
  - Query logging
  - Identity data retrieval

- **TestNeo4jManager**
  - Node creation
  - Relationship creation
  - Chain retrieval

- **TestDatabaseManager**
  - Orchestration of both databases
  - Partial initialization scenarios

### 3. Rate Limiting Tests (`test_rate_limiting.py`)

Tests rate limiting functionality:

- **TestInMemoryRateLimiter**
  - Rate limit enforcement
  - Endpoint-specific limits
  - Different IPs have separate limits
  - Burst handling
  - Hourly limit reset

- **TestRedisRateLimiter**
  - Redis-based rate limiting
  - Redis connection handling

### 4. Caching Tests (`test_caching.py`)

Tests caching functionality:

- **TestInMemoryCache**
  - Set and get operations
  - TTL expiration
  - Cache deletion
  - JSON serialization

- **TestRedisCache**
  - Redis-based caching
  - Key management

### 5. Integration Tests (`test_integration.py`)

End-to-end integration tests:

- **TestEndToEndUsernameSearch**
  - Complete search flow
  - Results retrieval
  - Export functionality

- **TestEndToEndReverseLookup**
  - Complete reverse lookup flow
  - Discovered username searches

- **TestEndToFuzzyMatch**
  - Complete fuzzy match flow
  - Match type verification

- **TestEndToErrorHandling**
  - Invalid inputs
  - Service errors
  - Error propagation

- **TestEndToRateLimiting**
  - Rate limit enforcement
  - Header presence

- **TestEndToCaching**
  - Cache hit scenarios

- **TestEndToPagination**
  - Large result sets
  - Multiple pages

## Running Tests

### Prerequisites

Install test dependencies:

```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
# Run all tests with coverage
pytest --cov=backend --cov-report=html

# Run all tests with verbose output
pytest -v

# Run tests and show coverage in terminal
pytest --cov=backend --cov-report=term-missing
```

### Run Specific Test Files

```bash
# Run API endpoint tests
pytest backend/tests/test_username_enum_api.py

# Run database tests
pytest backend/tests/test_database.py

# Run integration tests
pytest backend/tests/test_integration.py
```

### Run Specific Test Classes

```bash
# Run only username search tests
pytest backend/tests/test_username_enum_api.py::TestUsernameSearchEndpoint

# Run only rate limiting tests
pytest backend/tests/test_rate_limiting.py::TestInMemoryRateLimiter
```

### Run Specific Tests

```bash
# Run a specific test
pytest backend/tests/test_username_enum_api.py::TestUsernameSearchEndpoint::test_search_username_success

# Run tests matching a pattern
pytest -k "test_search_username"
```

### Run Tests with Markers

```bash
# Run only integration tests
pytest -m integration

# Run only unit tests
pytest -m unit

# Run slow tests
pytest -m slow

# Run all tests except slow ones
pytest -m "not slow"
```

## Test Configuration

Configuration is in `pytest.ini`:

```ini
[tool:pytest]
testpaths = backend/tests
addopts = -v --strict-markers --tb=short
markers =
    asyncio: mark test as async
    integration: mark test as integration test
    unit: mark test as unit test
    e2e: mark test as end-to-end test
    slow: mark test as slow running
    rate_limiting: mark test as rate limiting test
    caching: mark test as caching test
    database: mark test as database test
```

## Writing New Tests

### Basic Test Template

```python
import pytest
from unittest.mock import Mock, AsyncMock

class TestNewFeature:
    """Tests for new feature"""
    
    @pytest.fixture
    def setup(self):
        """Setup for tests"""
        return {}
    
    def test_basic_functionality(self, setup):
        """Test basic functionality"""
        # Arrange
        expected = "result"
        
        # Act
        actual = "result"
        
        # Assert
        assert actual == expected
    
    @pytest.mark.asyncio
    async def test_async_functionality(self, setup):
        """Test async functionality"""
        # Arrange
        async_service = Mock()
        async_service.method = AsyncMock(return_value="result")
        
        # Act
        result = await async_service.method()
        
        # Assert
        assert result == "result"
```

### Testing API Endpoints

```python
def test_endpoint(self, client, app):
    """Test API endpoint"""
    # Mock service responses
    app.state.username_service.method = AsyncMock(return_value=mock_data)
    
    # Make request
    response = client.post("/api/endpoint", json={"param": "value"})
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "key" in data
```

### Testing with Mocks

```python
def test_with_mocks(self, app):
    """Test with mocked dependencies"""
    # Mock database
    app.state.db_manager.postgresql = Mock()
    app.state.db_manager.postgresql.method = AsyncMock()
    
    # Mock cache
    app.state.cache_manager.get = AsyncMock(return_value=cached_data)
    
    # Test code that uses these mocks
    ...
```

## Test Coverage

### Current Coverage Areas

✅ **API Endpoints**
- All 5 main endpoints
- Export endpoints
- WebSocket endpoints
- Health checks

✅ **Input Validation**
- Username formats
- Email validation
- Phone validation
- Required fields

✅ **Error Handling**
- Service errors
- Database errors
- Network failures
- Rate limit exceeded

✅ **Caching**
- Cache hits/misses
- TTL expiration
- Cache invalidation
- Redis fallback

✅ **Rate Limiting**
- Per-IP limits
- Per-endpoint limits
- Burst handling
- Limit reset

✅ **Database**
- PostgreSQL operations
- Neo4j operations
- Connection pooling
- Transaction handling

✅ **Integration**
- End-to-end flows
- Multiple endpoint calls
- Data persistence
- Export functionality

### Coverage Goals

Target coverage: **>80%**

To check current coverage:

```bash
pytest --cov=backend --cov-report=html
open htmlcov/index.html
```

## CI/CD Integration

Tests should run automatically in CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pytest --cov=backend --cov-report=xml --cov-report=term
    
- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage.xml
```

## Common Testing Patterns

### 1. Testing Async Code

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

### 2. Testing Exceptions

```python
def test_exception_handling():
    with pytest.raises(ValueError):
        raise ValueError("Test error")
    
    with pytest.raises(HTTPException) as exc_info:
        raise HTTPException(status_code=404)
    assert exc_info.value.status_code == 404
```

### 3. Testing with Fixtures

```python
@pytest.fixture
def sample_data():
    return {"key": "value"}

def test_with_fixture(sample_data):
    assert sample_data["key"] == "value"
```

### 4. Parameterized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("test@example.com", True),
    ("invalid-email", False),
])
def test_email_validation(input, expected):
    result = validate_email(input)
    assert result == expected
```

## Debugging Tests

### Verbose Output

```bash
pytest -v -s
```

### Stop on First Failure

```bash
pytest -x
```

### Show Local Variables on Failure

```bash
pytest -l
```

### Enter Debugger on Failure

```bash
pytest --pdb
```

### Run Specific Test with Logging

```bash
pytest test_file.py::test_function --log-cli-level=DEBUG
```

## Best Practices

1. **Keep tests independent**: Each test should be able to run alone
2. **Use descriptive names**: `test_search_username_with_invalid_email`
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Mock external dependencies**: Don't make real API calls
5. **Test edge cases**: Empty inputs, maximum values, etc.
6. **Test error conditions**: Not just success paths
7. **Keep tests fast**: Avoid slow operations in tests
8. **Use fixtures wisely**: For common setup code

## Troubleshooting

### Tests Fail with Import Errors

```bash
# Ensure Python path includes project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

### Async Tests Hang

```bash
# Ensure pytest-asyncio is installed
pip install pytest-asyncio

# Use asyncio mode
pytest --asyncio-mode=auto
```

### Coverage Shows Uncovered Code

- Check if tests exist for all functions
- Add tests for edge cases
- Test exception paths
- Test all branches in conditional logic

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
