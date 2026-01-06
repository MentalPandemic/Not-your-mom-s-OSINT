"""CLI command definitions for the OSINT tool."""

import click
from pathlib import Path
from ..core.aggregator import Aggregator


@click.group()
@click.version_option(version="0.1.0", prog_name="osint")
@click.pass_context
def main(ctx):
    """Not-your-mom's-OSINT: Comprehensive open-source intelligence aggregation platform."""
    ctx.ensure_object(dict)
    ctx.obj["aggregator"] = Aggregator()


@main.command()
@click.option("--username", "-u", required=True, help="Username to search for")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--format", "-f", type=click.Choice(["json", "csv"]), default="json", help="Output format")
@click.pass_context
def search(ctx, username, output, format):
    """Search for a username across all configured sources."""
    click.echo(f"Searching for username: {username}")
    
    aggregator = ctx.obj["aggregator"]
    
    try:
        results = aggregator.search_username(username)
        
        if output:
            message = aggregator.export_results(results, format, output)
            click.echo(message)
        else:
            click.echo(results.to_json())
        
        found_count = len(results.get_found())
        click.echo(f"Search completed. Found {found_count} results across {len(results)} sources.")
        
    except Exception as e:
        click.echo(f"Error during search: {e}", err=True)
        raise click.ClickException(str(e))


@main.command()
@click.option("--data", "-d", required=True, type=click.Path(exists=True), help="Data file to correlate")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--format", "-f", type=click.Choice(["json", "csv"]), default="json", help="Output format")
@click.pass_context
def correlate(ctx, data, output, format):
    """Correlate findings from a data file."""
    click.echo(f"Correlating data from: {data}")
    
    aggregator = ctx.obj["aggregator"]
    
    try:
        results = aggregator.correlate_findings(data)
        
        if output:
            message = aggregator.export_results(results, format, output)
            click.echo(message)
        else:
            click.echo(results.to_json())
        
        click.echo(f"Correlation completed. Processed {len(results)} result sets.")
        
    except Exception as e:
        click.echo(f"Error during correlation: {e}", err=True)
        raise click.ClickException(str(e))


@main.command()
@click.option("--format", "-f", type=click.Choice(["json", "csv"]), required=True, help="Export format")
@click.option("--input", "-i", type=click.Path(exists=True), help="Input file from previous search")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--username", "-u", help="Username to search and export (alternative to --input)")
@click.pass_context
def export(ctx, format, input, output, username):
    """Export results in specified format."""
    
    aggregator = ctx.obj["aggregator"]
    
    try:
        if input:
            # Load results from input file
            from ..core.result import ResultSet
            import json
            
            with open(input, 'r') as f:
                data = json.load(f)
            
            # Create ResultSet from loaded data
            results = ResultSet()
            # Note: Full deserialization would be implemented here
            # For now, create a mock result
            click.echo(f"Loaded data from {input}")
            
        elif username:
            # Search and export
            click.echo(f"Searching and exporting username: {username}")
            results = aggregator.search_username(username)
        else:
            raise click.ClickException("Either --input or --username must be specified")
        
        if output:
            message = aggregator.export_results(results, format, output)
            click.echo(message)
        else:
            # Print to stdout
            if format == "json":
                click.echo(results.to_json())
            elif format == "csv":
                click.echo(results.to_dataframe().to_csv(index=False))
        
        click.echo(f"Export completed in {format.upper()} format.")
        
    except Exception as e:
        click.echo(f"Error during export: {e}", err=True)
        raise click.ClickException(str(e))


@main.command()
@click.pass_context
def info(ctx):
    """Show information about configured sources."""
    aggregator = ctx.obj["aggregator"]
    
    click.echo("OSINT Aggregator Information")
    click.echo("=" * 30)
    
    stats = aggregator.get_stats()
    
    click.echo(f"Sources configured: {stats['sources_configured']}")
    click.echo(f"Sources enabled: {stats['sources_enabled']}")
    
    click.echo("\nEnabled Sources:")
    for source_name in stats['source_names']:
        click.echo(f"  - {source_name}")
    
    # Show Sherlock platforms if available
    for source in aggregator.get_sources():
        if source.get_name() == "sherlock":
            try:
                platforms = source.get_supported_platforms()
                click.echo(f"\nSherlock supports {len(platforms)} platforms")
                click.echo("Top platforms:")
                for platform in platforms[:10]:
                    click.echo(f"  - {platform}")
                if len(platforms) > 10:
                    click.echo(f"  ... and {len(platforms) - 10} more")
            except:
                pass


@main.command()
@click.pass_context
def config(ctx):
    """Show current configuration."""
    from ..utils.config import get_cached_config
    
    config = get_cached_config()
    click.echo("Current Configuration:")
    click.echo("=" * 30)
    
    # Show sources configuration
    if 'sources' in config:
        click.echo("\nSources:")
        for source_name, source_config in config['sources'].items():
            enabled = source_config.get('enabled', True)
            status = "✓" if enabled else "✗"
            click.echo(f"  {status} {source_name}")
    
    # Show output configuration
    if 'output' in config:
        click.echo("\nOutput:")
        for key, value in config['output'].items():
            click.echo(f"  {key}: {value}")
    
    # Show requests configuration
    if 'requests' in config:
        click.echo("\nRequests:")
        for key, value in config['requests'].items():
            click.echo(f"  {key}: {value}")


if __name__ == "__main__":
    main()