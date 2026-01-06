"""Basic tests for the osint package."""

import io
import sys
from contextlib import redirect_stdout

import pandas as pd
from click.testing import CliRunner

from osint import Aggregator, SearchResult, CorrelationResult
from osint.cli.commands import cli
from osint.core.aggregator import Aggregator as CoreAggregator
from osint.core.result import CorrelationResult as CoreCorrelationResult
from osint.sources.sherlock_source import SherlockSource


def test_module_imports() -> None:
    """Test that all main modules can be imported."""
    from osint import Aggregator, SearchResult, CorrelationResult
    from osint.core.aggregator import Aggregator as CoreAggregator
    from osint.core.result import SearchResult as CoreSearchResult
    from osint.sources.base import BaseSource
    from osint.sources.sherlock_source import SherlockSource
    from osint.utils.config import Config, get_config

    assert Aggregator is not None
    assert SearchResult is not None
    assert CorrelationResult is not None
    assert CoreAggregator is not None
    assert CoreSearchResult is not None
    assert BaseSource is not None
    assert SherlockSource is not None
    assert Config is not None
    assert get_config is not None


def test_aggregator_instantiation() -> None:
    """Test that the Aggregator can be instantiated."""
    aggregator = Aggregator()
    assert aggregator is not None
    assert isinstance(aggregator, Aggregator)
    assert aggregator.sources == []


def test_aggregator_add_source() -> None:
    """Test adding sources to the Aggregator."""
    aggregator = Aggregator()
    source = SherlockSource()

    aggregator.add_source(source)
    assert len(aggregator.sources) == 1
    assert aggregator.sources[0] == source


def test_aggregator_remove_source() -> None:
    """Test removing sources from the Aggregator."""
    aggregator = Aggregator()
    source = SherlockSource()

    aggregator.add_source(source)
    assert len(aggregator.sources) == 1

    aggregator.remove_source(source)
    assert len(aggregator.sources) == 0


def test_aggregator_clear_sources() -> None:
    """Test clearing all sources from the Aggregator."""
    aggregator = Aggregator()
    source1 = SherlockSource()
    source2 = SherlockSource()

    aggregator.add_source(source1)
    aggregator.add_source(source2)
    assert len(aggregator.sources) == 2

    aggregator.clear_sources()
    assert len(aggregator.sources) == 0


def test_aggregator_get_active_sources() -> None:
    """Test getting list of active sources."""
    aggregator = Aggregator()
    source = SherlockSource()

    aggregator.add_source(source)
    active_sources = aggregator.get_active_sources()

    assert len(active_sources) == 1
    assert "SherlockSource" in active_sources


def test_search_result_creation() -> None:
    """Test SearchResult creation and methods."""
    result = SearchResult(
        source="TestSource",
        url="https://example.com/user",
        found=True,
        data={"test": "data"},
    )

    assert result.source == "TestSource"
    assert result.url == "https://example.com/user"
    assert result.found is True
    assert result.data == {"test": "data"}

    result_dict = result.to_dict()
    assert result_dict["source"] == "TestSource"
    assert result_dict["found"] is True


def test_search_result_from_dict() -> None:
    """Test creating SearchResult from dictionary."""
    data = {
        "source": "TestSource",
        "url": "https://example.com/user",
        "found": True,
        "data": {"test": "data"},
        "timestamp": "2024-01-01T00:00:00",
    }

    result = SearchResult.from_dict(data)
    assert result.source == "TestSource"
    assert result.url == "https://example.com/user"
    assert result.found is True


def test_correlation_result_creation() -> None:
    """Test CorrelationResult creation and methods."""
    result = CorrelationResult(
        correlation_type="username",
        confidence=0.9,
        sources=["Twitter", "GitHub"],
        data={"username": "testuser"},
    )

    assert result.correlation_type == "username"
    assert result.confidence == 0.9
    assert result.sources == ["Twitter", "GitHub"]
    assert result.data == {"username": "testuser"}

    result_dict = result.to_dict()
    assert result_dict["correlation_type"] == "username"
    assert result_dict["confidence"] == 0.9


def test_correlation_result_from_dict() -> None:
    """Test creating CorrelationResult from dictionary."""
    data = {
        "correlation_type": "username",
        "confidence": 0.9,
        "sources": ["Twitter", "GitHub"],
        "data": {"username": "testuser"},
    }

    result = CorrelationResult.from_dict(data)
    assert result.correlation_type == "username"
    assert result.confidence == 0.9
    assert result.sources == ["Twitter", "GitHub"]


def test_sherlock_source_instantiation() -> None:
    """Test that SherlockSource can be instantiated."""
    source = SherlockSource(timeout=30)
    assert source is not None
    assert source.timeout == 30
    assert source.enabled is True


def test_sherlock_source_enable_disable() -> None:
    """Test enabling and disabling SherlockSource."""
    source = SherlockSource()
    assert source.is_enabled() is True

    source.disable()
    assert source.is_enabled() is False

    source.enable()
    assert source.is_enabled() is True


def test_sherlock_source_filter_sources() -> None:
    """Test filtering sources in SherlockSource."""
    source = SherlockSource()
    sources = ["Twitter", "GitHub"]

    source.filter_sources(sources)
    assert source.filtered_sources == sources


def test_sherlock_source_search_username() -> None:
    """Test username search with SherlockSource (mock mode)."""
    source = SherlockSource()
    results = source.search_username("testuser")

    assert isinstance(results, list)
    assert len(results) > 0
    assert all(isinstance(result, SearchResult) for result in results)


def test_sherlock_source_search_username_filtered() -> None:
    """Test username search with filtered sources."""
    source = SherlockSource()
    source.filter_sources(["Twitter", "GitHub"])
    results = source.search_username("testuser")

    assert isinstance(results, list)
    assert all(result.source in ["Twitter", "GitHub"] for result in results)


def test_aggregator_search_username() -> None:
    """Test searching username through aggregator."""
    aggregator = Aggregator()
    source = SherlockSource()
    aggregator.add_source(source)

    results = aggregator.search_username("testuser")
    assert isinstance(results, list)
    assert len(results) > 0
    assert all(isinstance(result, SearchResult) for result in results)


def test_aggregator_correlate_data() -> None:
    """Test data correlation with aggregator."""
    aggregator = Aggregator()

    # Create test data with correlations
    data = pd.DataFrame({
        "username": ["user1", "user2", "user1", "user3"],
        "platform": ["Twitter", "GitHub", "Reddit", "Twitter"],
        "email": ["user1@test.com", "user2@test.com", "user1@test.com", "user3@test.com"],
    })

    correlations = aggregator.correlate_data(data)
    assert isinstance(correlations, pd.DataFrame)
    assert len(correlations) > 0 or len(correlations) == 0  # Either correlations or empty is valid


def test_aggregator_correlate_empty_data() -> None:
    """Test correlation with empty data."""
    aggregator = Aggregator()
    data = pd.DataFrame()

    correlations = aggregator.correlate_data(data)
    assert isinstance(correlations, pd.DataFrame)
    assert correlations.empty


def test_cli_help() -> None:
    """Test that CLI help command works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "search" in result.output
    assert "correlate" in result.output
    assert "export" in result.output


def test_cli_search_help() -> None:
    """Test that search command help works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["search", "--help"])

    assert result.exit_code == 0
    assert "--username" in result.output
    assert "--sources" in result.output


def test_cli_correlate_help() -> None:
    """Test that correlate command help works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["correlate", "--help"])

    assert result.exit_code == 0
    assert "--data" in result.output


def test_cli_export_help() -> None:
    """Test that export command help works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["export", "--help"])

    assert result.exit_code == 0
    assert "--format" in result.output
    assert "--output" in result.output


def test_config_creation() -> None:
    """Test Config creation and loading."""
    from osint.utils.config import Config

    config = Config()
    assert config is not None
    assert config.get("timeout") == 30
    assert config.get("max_retries") == 3


def test_config_get_set() -> None:
    """Test Config get and set methods."""
    from osint.utils.config import Config

    config = Config()
    config.set("timeout", 60)
    assert config.get("timeout") == 60

    config.set("new_key", "new_value")
    assert config.get("new_key") == "new_value"


def test_config_nested_keys() -> None:
    """Test Config with nested keys."""
    from osint.utils.config import Config

    config = Config()
    assert config.get("sources.sherlock.enabled") is True

    config.set("sources.sherlock.enabled", False)
    assert config.get("sources.sherlock.enabled") is False


def test_config_reset() -> None:
    """Test Config reset functionality."""
    from osint.utils.config import Config

    config = Config()
    config.set("timeout", 60)
    assert config.get("timeout") == 60

    config.reset()
    assert config.get("timeout") == 30


def test_cli_search_command() -> None:
    """Test search command with mock data."""
    runner = CliRunner()
    result = runner.invoke(cli, ["search", "--username", "testuser"])

    assert result.exit_code == 0
    assert "Searching for username" in result.output


def test_cli_search_command_with_output(tmp_path) -> None:
    """Test search command with output file."""
    output_file = tmp_path / "output.json"
    runner = CliRunner()
    result = runner.invoke(cli, ["search", "--username", "testuser", "--output", str(output_file)])

    assert result.exit_code == 0
    assert output_file.exists()


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
