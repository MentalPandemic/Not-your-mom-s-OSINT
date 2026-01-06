"""Basic functionality tests."""

import subprocess
import sys
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

import osint
from osint import Aggregator, Result, ResultSet
from osint.sources.base import SourceBase
from osint.sources.sherlock_source import SherlockSource
from osint.utils.config import get_default_config


class TestBasic:
    """Basic functionality tests."""
    
    def test_imports(self):
        """Test that all modules can be imported."""
        assert osint is not None
        assert Aggregator is not None
        assert Result is not None
        assert ResultSet is not None
        assert SourceBase is not None
        assert SherlockSource is not None
    
    def test_aggregator_instantiation(self):
        """Test that Aggregator can be instantiated."""
        aggregator = Aggregator()
        assert aggregator is not None
        assert len(aggregator.get_sources()) > 0
    
    def test_result_creation(self):
        """Test Result creation and basic functionality."""
        result = Result(
            source="test",
            query="test_query",
            url="https://example.com",
            found=True,
            username="testuser"
        )
        
        assert result.source == "test"
        assert result.query == "test_query"
        assert result.found is True
        assert result.username == "testuser"
        assert result.confidence == 0.0
        
        # Test to_dict method
        result_dict = result.to_dict()
        assert result_dict["source"] == "test"
        assert result_dict["found"] is True
        
        # Test to_json method
        result_json = result.to_json()
        assert "test" in result_json
        assert "true" in result_json or "True" in result_json
    
    def test_resultset_functionality(self):
        """Test ResultSet basic functionality."""
        result_set = ResultSet()
        
        # Add a result
        result = Result(
            source="test",
            query="test_query",
            url="https://example.com",
            found=True
        )
        result_set.add_result(result)
        
        assert len(result_set) == 1
        assert len(result_set.get_found()) == 1
        assert result_set[0].source == "test"
        
        # Test export methods don't error
        json_output = result_set.to_json()
        assert "test_query" in json_output
        
        df = result_set.to_dataframe()
        assert len(df) == 1
    
    def test_config_loading(self):
        """Test configuration loading."""
        config = get_default_config()
        assert config is not None
        assert "sources" in config
        assert "output" in config
        assert "requests" in config
    
    def test_sherlock_source_instantiation(self):
        """Test SherlockSource instantiation."""
        sherlock = SherlockSource()
        assert sherlock is not None
        assert sherlock.get_name() == "sherlock"
        assert sherlock.is_enabled() is True
        
        platforms = sherlock.get_supported_platforms()
        assert len(platforms) > 0
        assert "Twitter" in platforms
    
    def test_cli_help_command(self):
        """Test CLI help command."""
        result = subprocess.run(
            [sys.executable, "-m", "osint", "--help"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "osint" in result.stdout.lower()
        assert "search" in result.stdout.lower()
        assert "correlate" in result.stdout.lower()
        assert "export" in result.stdout.lower()
    
    def test_search_command_basic(self):
        """Test search command basic functionality."""
        result = subprocess.run(
            [sys.executable, "-m", "osint", "search", "--username", "testuser"],
            capture_output=True,
            text=True
        )
        
        # Should succeed (returncode 0) and contain results
        assert result.returncode == 0
        output = result.stdout.lower()
        assert "testuser" in output or "completed" in output or "json" in output
    
    def test_info_command(self):
        """Test info command."""
        result = subprocess.run(
            [sys.executable, "-m", "osint", "info"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        output = result.stdout.lower()
        assert "sources" in output
        assert "sherlock" in output or "configured" in output
    
    def test_config_command(self):
        """Test config command."""
        result = subprocess.run(
            [sys.executable, "-m", "osint", "config"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        output = result.stdout.lower()
        assert "configuration" in output or "config" in output
    
    def test_version_option(self):
        """Test version option."""
        result = subprocess.run(
            [sys.executable, "-m", "osint", "--version"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "0.1.0" in result.stdout
    
    def test_aggregator_stats(self):
        """Test aggregator statistics."""
        aggregator = Aggregator()
        stats = aggregator.get_stats()
        
        assert "sources_configured" in stats
        assert "sources_enabled" in stats
        assert "source_names" in stats
        assert isinstance(stats["source_names"], list)
        assert "sherlock" in stats["source_names"]
    
    def test_sherlock_search_username(self):
        """Test Sherlock username search."""
        sherlock = SherlockSource()
        result = sherlock.search_username("testuser123")
        
        assert result is not None
        assert result.source == "sherlock"
        assert result.username == "testuser123"
        assert result.query == "testuser123"
        
        # Additional data should be populated
        if result.found:
            assert "platforms" in result.additional_data
    
    def test_correlation_basic(self):
        """Test correlation functionality."""
        aggregator = Aggregator()
        results = aggregator.correlate_findings()
        
        assert results is not None
        assert len(results) > 0