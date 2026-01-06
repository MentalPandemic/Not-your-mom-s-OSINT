"""CLI command definitions for the osint tool."""

import json
import sys
from pathlib import Path
from typing import Optional

import click
import pandas as pd

from osint.core.aggregator import Aggregator
from osint.core.result import SearchResult
from osint.sources.sherlock_source import SherlockSource


@click.group()
@click.version_option(version="0.1.0", prog_name="osint")
def cli() -> None:
    """Not-your-mom's OSINT - A comprehensive OSINT aggregation platform."""
    pass


@cli.command()
@click.option(
    "--username",
    "-u",
    required=True,
    help="Username to search for across sources",
)
@click.option(
    "--sources",
    "-s",
    multiple=True,
    help="Specific sources to search (default: all sources)",
)
@click.option(
    "--timeout",
    "-t",
    type=int,
    default=30,
    help="Request timeout in seconds",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file path (if not specified, prints to stdout)",
)
def search(username: str, sources: tuple, timeout: int, output: Optional[str]) -> None:
    """Search for a username across multiple OSINT sources.

    This command queries various platforms to find occurrences of the
    specified username and returns matching results.
    """
    click.echo(f"Searching for username: {username}")

    aggregator = Aggregator()
    sherlock_source = SherlockSource(timeout=timeout)

    if sources:
        sherlock_source.filter_sources(list(sources))

    aggregator.add_source(sherlock_source)

    try:
        results = aggregator.search_username(username)
        output_results(results, output)
    except Exception as e:
        click.echo(f"Error during search: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--data",
    "-d",
    type=click.Path(exists=True),
    required=True,
    help="Input data file (CSV or JSON)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file for correlation results",
)
def correlate(data: str, output: Optional[str]) -> None:
    """Correlate findings from a data file.

    Analyzes the input data to identify patterns and relationships
    between different data points.
    """
    click.echo(f"Correlating data from: {data}")

    data_path = Path(data)

    try:
        if data_path.suffix == ".csv":
            df = pd.read_csv(data_path)
        elif data_path.suffix == ".json":
            df = pd.read_json(data_path)
        else:
            click.echo("Error: Unsupported file format. Use CSV or JSON.", err=True)
            sys.exit(1)

        aggregator = Aggregator()
        correlations = aggregator.correlate_data(df)

        if output:
            output_path = Path(output)
            if output_path.suffix == ".csv":
                correlations.to_csv(output, index=False)
            elif output_path.suffix == ".json":
                correlations.to_json(output, orient="records", indent=2)
            else:
                correlations.to_json(output, orient="records", indent=2)
            click.echo(f"Correlation results saved to: {output}")
        else:
            click.echo("\nCorrelation Results:")
            click.echo(correlations.to_string())

    except Exception as e:
        click.echo(f"Error during correlation: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--format",
    "-f",
    type=click.Choice(["csv", "json"]),
    required=True,
    help="Export format",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    required=True,
    help="Output file path",
)
@click.option(
    "--data",
    "-d",
    type=click.Path(exists=True),
    help="Input data file to export (if not specified, uses stdin)",
)
def export(format: str, output: str, data: Optional[str]) -> None:
    """Export results in various formats.

    Converts data to the specified format and writes to the output file.
    """
    click.echo(f"Exporting data to {format.upper()} format: {output}")

    try:
        if data:
            data_path = Path(data)
            if data_path.suffix == ".csv":
                df = pd.read_csv(data_path)
            elif data_path.suffix == ".json":
                df = pd.read_json(data_path)
            else:
                click.echo("Error: Unsupported input file format. Use CSV or JSON.", err=True)
                sys.exit(1)
        else:
            click.echo("Reading data from stdin...")
            data_text = sys.stdin.read()
            try:
                df = pd.read_json(data_text)
            except:
                df = pd.read_csv(data_text)

        output_path = Path(output)

        if format == "csv":
            df.to_csv(output_path, index=False)
        elif format == "json":
            df.to_json(output_path, orient="records", indent=2)

        click.echo(f"Data exported successfully to: {output}")

    except Exception as e:
        click.echo(f"Error during export: {e}", err=True)
        sys.exit(1)


def output_results(results: list[SearchResult], output: Optional[str]) -> None:
    """Output search results to file or stdout.

    Args:
        results: List of search results to output
        output: Optional output file path
    """
    if not results:
        click.echo("No results found.")
        return

    result_dicts = [result.to_dict() for result in results]

    if output:
        output_path = Path(output)
        if output_path.suffix == ".json":
            with open(output_path, "w") as f:
                json.dump(result_dicts, f, indent=2)
        elif output_path.suffix == ".csv":
            df = pd.DataFrame(result_dicts)
            df.to_csv(output_path, index=False)
        else:
            with open(output_path, "w") as f:
                json.dump(result_dicts, f, indent=2)
        click.echo(f"\nResults saved to: {output}")
    else:
        click.echo(f"\nFound {len(results)} results:\n")
        for result in results:
            status = "✓" if result.found else "✗"
            click.echo(f"{status} {result.source}: {result.url or 'Not found'}")
            if result.found and result.data:
                click.echo(f"  Data: {result.data}")


if __name__ == "__main__":
    cli()
