from __future__ import annotations

import csv
import json
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import click

from osint.core.aggregator import Aggregator
from osint.core.correlation import CorrelationEngine
from osint.core.datasource import normalize_list
from osint.core.graph import RelationshipGraph
from osint.core.models import (
    CorrelationResult,
    QueryResult,
    QueryStatus,
    Relationship,
    RelationshipType,
)
from osint.utils.config import resolve_results_dir
from osint.utils.config_manager import read_config


def _utc_ts() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_csv(path: Path, results: list[QueryResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "username",
                "platform_name",
                "profile_url",
                "status",
                "response_time",
                "metadata",
            ],
        )
        writer.writeheader()
        for r in results:
            writer.writerow(
                {
                    "username": r.username,
                    "platform_name": r.platform_name,
                    "profile_url": r.profile_url or "",
                    "status": r.status.value,
                    "response_time": r.response_time if r.response_time is not None else "",
                    "metadata": json.dumps(r.metadata, sort_keys=True),
                }
            )


def _resolve_output_paths(
    *,
    export: str,
    output: Path | None,
    results_dir: Path,
) -> dict[str, Path]:
    ts = _utc_ts()

    if output is None:
        base = results_dir / f"sherlock_search_{ts}"
    else:
        base = output

    paths: dict[str, Path] = {}

    if export in {"json", "both"}:
        json_path = base
        if json_path.suffix.lower() != ".json":
            json_path = json_path.with_suffix(".json")
        paths["json"] = json_path

    if export in {"csv", "both"}:
        csv_path = base
        if csv_path.suffix.lower() != ".csv":
            csv_path = csv_path.with_suffix(".csv")
        paths["csv"] = csv_path

    return paths


def _human_summary(results: list[QueryResult]) -> str:
    found = [r for r in results if r.status == QueryStatus.FOUND]
    errors = [r for r in results if r.status == QueryStatus.ERROR]

    lines: list[str] = []
    lines.append(f"Total results: {len(results)}")
    lines.append(f"Found: {len(found)}")
    lines.append(f"Errors: {len(errors)}")

    if found:
        lines.append("")
        lines.append("Found profiles:")
        for r in found:
            lines.append(f"  - {r.username} @ {r.platform_name}: {r.profile_url}")

    if errors:
        lines.append("")
        lines.append("Errors:")
        for r in errors[:10]:
            err = r.metadata.get("error") if isinstance(r.metadata, dict) else None
            lines.append(f"  - {r.username} @ {r.platform_name}: {err or 'error'}")

        if len(errors) > 10:
            lines.append(f"  ... and {len(errors) - 10} more")

    return "\n".join(lines)


@click.command("search")
@click.option(
    "--username",
    "-u",
    multiple=True,
    required=True,
    help="Username(s) to search. Can be repeated or comma-separated.",
)
@click.option(
    "--source",
    type=click.Choice(["all", "sherlock"], case_sensitive=False),
    default="all",
    show_default=True,
    help="Source to use.",
)
@click.option("--category", type=str, default=None, help="Filter by site category/tag.")
@click.option("--sites", type=str, default=None, help="Comma-separated list of specific sites.")
@click.option("--timeout", type=float, default=None, help="Request timeout in seconds.")
@click.option(
    "--threads",
    type=int,
    default=None,
    help="Number of concurrent threads (max: 100).",
)
@click.option(
    "--export",
    type=click.Choice(["json", "csv", "both"], case_sensitive=False),
    default=None,
    help="Export format.",
)
@click.option(
    "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Output file path (extension optional).",
)
@click.option("--browser", is_flag=True, default=False, help="Open found profiles in browser.")
@click.option("--no-nsfw", is_flag=True, default=False, help="Exclude NSFW sites from search.")
def search(
    username: tuple[str, ...],
    source: str,
    category: str | None,
    sites: str | None,
    timeout: float | None,
    threads: int | None,
    export: str | None,
    output: Path | None,
    browser: bool,
    no_nsfw: bool,
) -> None:
    config = read_config()

    usernames = normalize_list(username)
    if not usernames:
        raise click.ClickException("At least one --username is required")

    sites_list = normalize_list(sites)

    export = (export or str(config.get("output_format") or "json")).lower()
    if export not in {"json", "csv", "both"}:
        export = "json"

    results_dir = resolve_results_dir(str(config.get("results_path") or "./results"))

    if source.lower() == "all" and not bool(config.get("sherlock_enabled")):
        click.echo(
            "Warning: Sherlock is not enabled in your config. Running Sherlock anyway. "
            "Run 'osint setup' to enable it permanently.",
            err=True,
        )

    agg = Aggregator(config)

    progress_total = None
    progress_bar = None

    def progress_callback(done: int, total: int) -> None:
        nonlocal progress_total, progress_bar

        if progress_bar is None:
            progress_total = total
            progress_bar = click.progressbar(length=total, label="Searching")
            progress_bar.__enter__()

        if progress_total and total != progress_total:
            progress_total = total

        if progress_bar is not None:
            progress_bar.update(1)

    try:
        try:
            result = agg.search_usernames(
                usernames,
                sources=[source],
                category=category,
                sites=sites_list or None,
                timeout=timeout,
                threads=threads,
                no_nsfw=no_nsfw,
                progress_callback=progress_callback,
            )
        finally:
            if progress_bar is not None:
                progress_bar.__exit__(None, None, None)
    except Exception as e:
        try:
            from osint.sources.sherlock_source import SherlockUnavailableError

            if isinstance(e, SherlockUnavailableError):
                raise click.ClickException(str(e)) from e
        except Exception:
            pass

        if isinstance(e, ValueError):
            raise click.ClickException(str(e)) from e

        raise

    results = result.results

    click.echo(_human_summary(results))

    output_paths = _resolve_output_paths(export=export, output=output, results_dir=results_dir)

    payload = {
        "source": "sherlock",
        "usernames": usernames,
        "category": category,
        "sites": sites_list or None,
        "no_nsfw": no_nsfw,
        "results": [r.to_dict() for r in results],
        "stats": {
            "total": result.stats.total,
            "found": result.stats.found,
            "not_found": result.stats.not_found,
            "error": result.stats.error,
        },
    }

    if "json" in output_paths:
        _write_json(output_paths["json"], payload)
        click.echo(f"Saved JSON results to: {output_paths['json']}")

    if "csv" in output_paths:
        _write_csv(output_paths["csv"], results)
        click.echo(f"Saved CSV results to: {output_paths['csv']}")

    if browser:
        for r in results:
            if r.status == QueryStatus.FOUND and r.profile_url:
                webbrowser.open(r.profile_url)


@click.command("correlate")
@click.option(
    "--search-results",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="File with search results to correlate (JSON format).",
)
@click.option(
    "--username",
    "-u",
    type=str,
    default=None,
    help="Correlate findings for a specific username.",
)
@click.option(
    "--entities",
    type=str,
    default=None,
    help="Specific entities to correlate (comma-separated IDs).",
)
@click.option(
    "--report",
    type=click.Choice(["text", "json", "html"], case_sensitive=False),
    default="text",
    show_default=True,
    help="Report format.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output file path for report.",
)
def correlate(
    search_results: Path | None,
    username: str | None,
    entities: str | None,
    report: str,
    output: Path | None,
) -> None:
    """Correlate findings and identify relationships."""
    config = read_config()
    engine = CorrelationEngine(config)

    # Process based on input type
    if search_results:
        click.echo(f"Loading search results from {search_results}...")
        with search_results.open() as f:
            data = json.load(f)

        # Convert JSON data back to QueryResult objects
        results_data = data.get("results", [])
        results = [
            QueryResult(
                username=r["username"],
                platform_name=r["platform_name"],
                profile_url=r.get("profile_url"),
                status=QueryStatus(r["status"]),
                response_time=r.get("response_time"),
                metadata=r.get("metadata", {}),
            )
            for r in results_data
        ]

        click.echo(f"Processing {len(results)} results...")
        correlation_result = engine.process_query_results(results)

    elif username:
        click.echo(f"Correlating findings for username: {username}...")
        correlation_result = engine.correlate_username(username)

    elif entities:
        entity_ids = [e.strip() for e in entities.split(",")]
        click.echo(f"Correlating {len(entity_ids)} entities...")
        correlation_result = engine.correlate_entities(entity_ids)

    else:
        raise click.ClickException(
            "Must provide one of: --search-results, --username, or --entities"
        )

    # Display summary
    click.echo("\n" + correlation_result.summary)

    # Generate and save report
    report_content = engine.generate_report(format=report)

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report_content, encoding="utf-8")
        click.echo(f"\nReport saved to: {output}")
    else:
        click.echo("\n" + report_content)


@click.command("graph")
@click.option(
    "--entity",
    type=str,
    default=None,
    help="Entity ID to start exploration from.",
)
@click.option(
    "--depth",
    type=int,
    default=2,
    show_default=True,
    help="How many relationship hops to follow.",
)
@click.option(
    "--export",
    type=click.Choice(["json", "graphml", "gexf"], case_sensitive=False),
    default=None,
    help="Export format for graph data.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output file path for graph export.",
)
@click.option(
    "--min-confidence",
    type=float,
    default=0.0,
    show_default=True,
    help="Minimum confidence threshold (0-100).",
)
def graph(
    entity: str | None,
    depth: int,
    export: str | None,
    output: Path | None,
    min_confidence: float,
) -> None:
    """Explore and export relationship graphs."""
    config = read_config()
    engine = CorrelationEngine(config)

    if entity:
        # Explore from specific entity
        click.echo(f"Exploring relationships from entity: {entity}")
        graph_obj = engine.get_graph()

        neighbors = graph_obj.get_entity_neighbors(entity)

        if not neighbors:
            click.echo("No relationships found for this entity.")
            return

        click.echo(f"\nFound {len(neighbors)} direct relationships:")
        for neighbor_id, relationship in neighbors:
            neighbor = graph_obj.get_entity(neighbor_id)
            if neighbor:
                click.echo(
                    f"  - {neighbor.name} ({neighbor.type.value}) - {relationship.type.value} - {relationship.confidence:.1f}%"
                )
                if relationship.evidence:
                    for evidence in relationship.evidence[:2]:
                        click.echo(f"      Evidence: {evidence}")

        # Find paths to other entities
        if depth > 1:
            all_entities = [e.id for e in engine._entities.values()]
            for other_id in all_entities:
                if other_id != entity and other_id not in [n[0] for n in neighbors]:
                    path = graph_obj.get_path(entity, other_id)
                    if path and len(path) <= depth + 1:
                        click.echo(f"\nPath to {other_id}: {' -> '.join(path)}")

    else:
        # Show overall graph statistics
        graph_obj = engine.get_graph()
        stats = graph_obj.get_statistics()

        click.echo("Graph Statistics:")
        click.echo(f"  Entities (nodes): {stats['num_nodes']}")
        click.echo(f"  Relationships (edges): {stats['num_edges']}")
        click.echo(f"  Connected components: {stats['num_connected_components']}")
        click.echo(f"  Average degree: {stats['average_degree']:.2f}")
        click.echo(f"  Density: {stats['density']:.4f}")

        if stats.get("avg_confidence"):
            click.echo(f"  Avg confidence: {stats['avg_confidence']:.1f}%")

        # Show central entities
        central = graph_obj.find_central_entities(top_n=5)
        if central:
            click.echo("\nMost connected entities:")
            for entity_id, centrality in central:
                ent = graph_obj.get_entity(entity_id)
                name = ent.name if ent else entity_id
                click.echo(f"  - {name}: {centrality:.3f}")

        # Show clusters
        clusters = graph_obj.find_clusters(min_confidence=min_confidence)
        if clusters:
            click.echo(f"\nFound {len(clusters)} clusters (min confidence: {min_confidence}%):")
            for i, cluster in enumerate(clusters[:5], 1):
                click.echo(f"  {i}. {len(cluster)} entities")

    # Export graph
    if export and output:
        graph_obj = engine.get_graph()

        if export == "json":
            graph_obj.export_json(output)
        elif export == "graphml":
            graph_obj.export_graphml(output)
        elif export == "gexf":
            graph_obj.export_gexf(output)

        click.echo(f"\nGraph exported to: {output}")


@click.command("relationships")
@click.option(
    "--type",
    "rel_type",
    type=click.Choice(
        ["same_person", "related", "potential", "suspicious"], case_sensitive=False
    ),
    default=None,
    help="Filter by relationship type.",
)
@click.option(
    "--min-confidence",
    type=float,
    default=0.0,
    show_default=True,
    help="Minimum confidence threshold (0-100).",
)
@click.option(
    "--entity",
    type=str,
    default=None,
    help="Show relationships for a specific entity.",
)
@click.option(
    "--limit",
    type=int,
    default=20,
    show_default=True,
    help="Maximum number of relationships to show.",
)
def relationships(
    rel_type: str | None,
    min_confidence: float,
    entity: str | None,
    limit: int,
) -> None:
    """Query and display relationships."""
    config = read_config()
    engine = CorrelationEngine(config)

    # Build filter
    relationship_type = RelationshipType(rel_type) if rel_type else None

    # Get filtered relationships
    filtered_rels = engine.get_relationships(
        entity_id=entity, rel_type=relationship_type, min_confidence=min_confidence
    )

    if not filtered_rels:
        click.echo("No relationships found matching the criteria.")
        return

    # Sort by confidence and limit
    filtered_rels = sorted(filtered_rels, key=lambda r: r.confidence, reverse=True)[
        :limit
    ]

    # Display relationships
    click.echo(f"\nFound {len(filtered_rels)} relationships:")
    click.echo("=" * 70)

    for rel in filtered_rels:
        entity_a = engine._entities.get(rel.entity_a)
        entity_b = engine._entities.get(rel.entity_b)

        name_a = entity_a.name if entity_a else rel.entity_a[:16] + "..."
        name_b = entity_b.name if entity_b else rel.entity_b[:16] + "..."

        click.echo(f"\n{name_a} <-> {name_b}")
        click.echo(f"  Type: {rel.type.value}")
        click.echo(f"  Confidence: {rel.confidence:.1f}%")

        if entity_a:
            click.echo(f"  Entity A: {entity_a.type.value} ({entity_a.name})")
        if entity_b:
            click.echo(f"  Entity B: {entity_b.type.value} ({entity_b.name})")

        if rel.evidence:
            click.echo(f"  Evidence:")
            for evidence in rel.evidence[:3]:
                click.echo(f"    - {evidence}")

        if rel.metadata:
            click.echo(f"  Metadata: {json.dumps(rel.metadata, indent=6)}")

    if len(filtered_rels) == limit:
        click.echo(f"\n... (showing first {limit} of {len(engine.get_relationships(entity_id=entity, rel_type=relationship_type, min_confidence=min_confidence))} total)")
