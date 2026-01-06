"""Basic tests for Not-your-mom's-OSINT."""

import json
import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from osint import __version__
from osint.core.aggregator import OSINTAggregator
from osint.core.result import OSINTResult, SearchResult
from osint.sources.base import BaseSource
from osint.sources.sherlock_source import SherlockSource


def test_version():
    """Test package version."""
    assert __version__ == "0.1.0"


def test_imports():
    """Test that core modules can be imported."""
    try:
        from osint.core.aggregator import OSINTAggregator
        from osint.core.result import OSINTResult, SearchResult
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import core modules: {e}")


def test_search_result_creation():
    """Test SearchResult dataclass creation."""
    result = SearchResult(
        platform="GitHub",
        username="testuser",
        url="https://github.com/testuser",
        found=True
    )
    
    assert result.platform == "GitHub"
    assert result.username == "testuser"
    assert result.url == "https://github.com/testuser"
    assert result.found is True
    assert result.timestamp is not None


def test_search_result_to_dict():
    """Test SearchResult to_dict conversion."""
    result = SearchResult(
        platform="Twitter",
        username="testuser",
        url="https://twitter.com/testuser",
        found=True,
        additional_data={"followers": 100}
    )
    
    result_dict = result.to_dict()
    assert result_dict["platform"] == "Twitter"
    assert result_dict["username"] == "testuser"
    assert result_dict["found"] is True
    assert result_dict["additional_data"]["followers"] == 100
    assert "timestamp" in result_dict


def test_osint_result_creation():
    """Test OSINTResult creation and basic operations."""
    osint_result = OSINTResult(
        query="testuser",
        query_type="username"
    )
    
    assert osint_result.query == "testuser"
    assert osint_result.query_type == "username"
    assert len(osint_result.found_accounts) == 0
    assert osint_result.total_found == 0
    assert osint_result.total_searched == 0


def test_osint_result_add_result():
    """Test adding results to OSINTResult."""
    osint_result = OSINTResult(
        query="testuser",
        query_type="username"
    )
    
    # Add found result
    found_result = SearchResult(
        platform="GitHub",
        username="testuser",
        url="https://github.com/testuser",
        found=True
    )
    
    # Add not found result
    not_found_result = SearchResult(
        platform="GitLab",
        username="testuser",
        url="https://gitlab.com/users/testuser",
        found=False
    )
    
    osint_result.add_result(found_result)
    osint_result.add_result(not_found_result)
    
    assert osint_result.total_searched == 2
    assert osint_result.total_found == 1
    assert len(osint_result.get_found_accounts()) == 1


def test_osint_result_to_dict():
    """Test OSINTResult to_dict conversion."""
    osint_result = OSINTResult(
        query="testuser",
        query_type="username"
    )
    
    result = SearchResult(
        platform="GitHub",
        username="testuser",
        url="https://github.com/testuser",
        found=True
    )
    
    osint_result.add_result(result)
    
    result_dict = osint_result.to_dict()
    assert result_dict["query"] == "testuser"
    assert result_dict["query_type"] == "username"
    assert len(result_dict["found_accounts"]) == 1
    assert result_dict["summary"]["total_found"] == 1
    assert result_dict["summary"]["total_searched"] == 1


def test_aggregator_creation():
    """Test OSINTAggregator instantiation."""
    aggregator = OSINTAggregator()
    assert len(aggregator.sources) == 0


def test_aggregator_add_source():
    """Test adding sources to aggregator."""
    aggregator = OSINTAggregator()
    source = SherlockSource()
    
    aggregator.add_source(source)
    assert len(aggregator.sources) == 1
    assert aggregator.sources[0] == source


def test_sherlock_source_creation():
    """Test SherlockSource creation."""
    source = SherlockSource()
    assert source.name == "sherlock"
    assert "Sherlock" in source.description
    assert source.status in ["ready", "simulated"]


def test_base_source_abstract():
    """Test that BaseSource is abstract."""
    with pytest.raises(TypeError):
        BaseSource()


def test_sherlock_source_search_username():
    """Test SherlockSource search_username method (mock mode)."""
    source = SherlockSource()
    results = source.search_username("testuser123")
    
    assert isinstance(results, list)
    assert len(results) > 0
    
    # Check that all results are SearchResult instances
    for result in results:
        assert isinstance(result, SearchResult)
        assert result.username == "testuser123"


def test_osint_result_get_by_platform():
    """Test getting results by platform."""
    osint_result = OSINTResult(
        query="testuser",
        query_type="username"
    )
    
    result = SearchResult(
        platform="GitHub",
        username="testuser",
        url="https://github.com/testuser",
        found=True
    )
    
    osint_result.add_result(result)
    
    found = osint_result.get_by_platform("GitHub")
    assert found is not None
    assert found.platform == "GitHub"
    
    not_found = osint_result.get_by_platform("GitLab")
    assert not_found is None


def test_aggregator_get_source_by_name():
    """Test getting source by name from aggregator."""
    aggregator = OSINTAggregator()
    sherlock = SherlockSource()
    
    aggregator.add_source(sherlock)
    
    found = aggregator.get_source_by_name("sherlock")
    assert found is not None
    assert found.name == "sherlock"
    
    not_found = aggregator.get_source_by_name("nonexistent")
    assert not_found is None


def test_search_result_str():
    """Test SearchResult string representation."""
    result = SearchResult(
        platform="Twitter",
        username="testuser",
        url="https://twitter.com/testuser",
        found=True
    )
    
    result_str = str(result)
    assert "Twitter" in result_str
    assert "testuser" in result_str


def test_osint_result_str():
    """Test OSINTResult string representation."""
    osint_result = OSINTResult(
        query="testuser",
        query_type="username"
    )
    
    result_str = str(osint_result)
    assert "OSINTResult" in result_str
    assert "testuser" in result_str


def test_aggregator_search_username_empty():
    """Test aggregator search with no sources."""
    aggregator = OSINTAggregator()
    result = aggregator.search_username("testuser")
    
    assert isinstance(result, OSINTResult)
    assert result.total_found == 0
    assert "warning" in result.metadata
