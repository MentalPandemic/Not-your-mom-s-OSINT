"""
CLI commands for Not-your-mom's-OSINT.

This module provides the command-line interface using Click framework.
"""

import json
import sys
from pathlib import Path

import click

from osint.core.aggregator import OSINTAggregator
from osint.sources.sherlock_source import SherlockSource


@click.group()
@click.version_option(version="0.1.0", prog_name="osint")
def main():
    """Not Your Mom's OSINT - A comprehensive OSINT aggregation platform."""
    pass


@main.command()
@click.option("--username", "-u", required=True, help="Username to search for")
@click.option("--output", "-o", type=click.Path(), help="Output file for results")
@click.option("--format", "-f", type=click.Choice(["json", "csv"]), default="json",
              help="Output format (default: json)")
def search(username, output, format):
    """Search for a username across OSINT sources."""
    click.echo(f"Searching for username: {username}")
    
    aggregator = OSINTAggregator()
    aggregator.add_source(SherlockSource())
    
    try:
        result = aggregator.search_username(username)
        
        if output:
            export_result(result, output, format)
            click.echo(f"Results saved to: {output}")
        else:
            # Print to console
            if format == "json":
                click.echo(json.dumps(result.to_dict(), indent=2))
            elif format == "csv":
                # Simple CSV output without pandas
                if result.found_accounts:
                    import csv
                    from io import StringIO
                    
                    output = StringIO()
                    fieldnames = ["platform", "username", "url", "found", "timestamp"]
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for account in result.found_accounts:
                        row = account.to_dict()
                        row.pop("additional_data", None)
                        writer.writerow(row)
                    
                    click.echo(output.getvalue())
                else:
                    click.echo("No results to display")
        
        click.echo(f"Search completed. Found {len(result.found_accounts)} accounts.")
        
    except Exception as e:
        click.echo(f"Error during search: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option("--data", "-d", required=True, type=click.Path(exists=True),
              help="Input data file (JSON or CSV)")
@click.option("--output", "-o", type=click.Path(), help="Output file for correlation results")
def correlate(data, output):
    """Correlate findings from OSINT data."""
    click.echo(f"Correlating data from: {data}")
    
    try:
        # Load data
        file_path = Path(data)
        if file_path.suffix.lower() == ".json":
            with open(file_path, "r") as f:
                data_content = json.load(f)
        elif file_path.suffix.lower() == ".csv":
            import csv
            with open(file_path, "r", newline="") as f:
                reader = csv.DictReader(f)
                data_content = list(reader)
        else:
            click.echo("Unsupported file format. Use JSON or CSV.", err=True)
            sys.exit(1)
        
        aggregator = OSINTAggregator()
        correlated = aggregator.correlate_findings(data_content)
        
        if output:
            export_result(correlated, output, "json")
            click.echo(f"Correlation results saved to: {output}")
        else:
            click.echo(json.dumps(correlated.to_dict(), indent=2))
        
        click.echo("Correlation completed.")
        
    except Exception as e:
        click.echo(f"Error during correlation: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option("--input", "-i", type=click.Path(exists=True),
              help="Input file to export (JSON format)")
@click.option("--format", "-f", type=click.Choice(["csv", "json"]), required=True,
              help="Export format")
@click.option("--output", "-o", type=click.Path(), required=True,
              help="Output file path")
def export(input, format, output):
    """Export OSINT results to different formats."""
    click.echo(f"Exporting to {format}: {output}")
    
    try:
        if not input:
            # Read from stdin
            import sys
            data_content = json.load(sys.stdin)
        else:
            with open(input, "r") as f:
                data_content = json.load(f)
        
        export_result(data_content, output, format)
        click.echo(f"Export completed: {output}")
        
    except Exception as e:
        click.echo(f"Error during export: {e}", err=True)
        sys.exit(1)


def export_result(data, output_path, format_type):
    """Export result data to specified format."""
    output_path = Path(output_path)
    
    if isinstance(data, dict):
        result_dict = data
    else:
        result_dict = data.to_dict() if hasattr(data, "to_dict") else data
    
    if format_type == "json":
        with open(output_path, "w") as f:
            json.dump(result_dict, f, indent=2)
    elif format_type == "csv":
        # Convert to DataFrame for CSV export
        if "found_accounts" in result_dict:
            df = pd.DataFrame(result_dict["found_accounts"])
        else:
            df = pd.DataFrame([result_dict])
        df.to_csv(output_path, index=False)
    else:
        raise ValueError(f"Unsupported format: {format_type}")


if __name__ == "__main__":
    main()
