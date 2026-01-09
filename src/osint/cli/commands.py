from __future__ import annotations

import csv
import json
import logging
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
    Post,
    QueryResult,
    QueryStatus,
    Relationship,
    RelationshipType,
    SocialPlatform,
    SocialProfile,
)
from osint.core.profile_analyzer import ProfileAnalyzer
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


@click.command("profile")
@click.option("--username", "-u", type=str, required=True, help="Username to profile.")
@click.option(
    "--platform",
    "-p",
    type=click.Choice(["twitter", "facebook", "linkedin", "instagram", "all"], case_sensitive=False),
    default="twitter",
    show_default=True,
    help="Social media platform.",
)
@click.option(
    "--details",
    type=click.Choice(["basic", "standard", "full"], case_sensitive=False),
    default="standard",
    show_default=True,
    help="Detail level for profile data.",
)
@click.option("--limit", type=int, default=50, show_default=True, help="Number of posts to fetch.")
@click.option("--include-posts", is_flag=True, default=True, help="Include post analysis.")
@click.option("--include-followers", is_flag=True, default=False, help="Include follower analysis.")
@click.option("--sentiment", is_flag=True, default=False, help="Analyze post sentiment.")
@click.option("--engagement", is_flag=True, default=False, help="Calculate engagement metrics.")
@click.option(
    "--export",
    type=click.Choice(["json", "csv", "html"], case_sensitive=False),
    default=None,
    help="Export format.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output file path.",
)
def profile_cmd(
    username: str,
    platform: str,
    details: str,
    limit: int,
    include_posts: bool,
    include_followers: bool,
    sentiment: bool,
    engagement: bool,
    export: str | None,
    output: Path | None,
) -> None:
    """Get social media profile information."""
    config = read_config()
    analyzer = ProfileAnalyzer()

    platforms_to_check = [platform] if platform != "all" else ["twitter", "facebook", "linkedin", "instagram"]
    profiles: dict[str, SocialProfile] = {}

    for plat in platforms_to_check:
        try:
            social_profile = _fetch_social_profile(
                config,
                plat,
                username,
                details,
                limit if include_posts else 0,
                include_followers,
                sentiment,
                engagement,
            )
            if social_profile:
                profiles[plat] = social_profile
        except Exception as e:
            click.echo(f"Error fetching {plat} profile: {e}", err=True)

    if not profiles:
        click.echo(f"No profiles found for username: {username}")
        return

    click.echo(f"\nFound {len(profiles)} profile(s) for '{username}':")
    click.echo("=" * 70)

    for plat, prof in profiles.items():
        click.echo(f"\n[{plat.upper()}]")
        click.echo(f"  Name: {prof.display_name}")
        click.echo(f"  Username: {prof.username}")
        click.echo(f"  Bio: {prof.bio[:100]}..." if len(prof.bio) > 100 else f"  Bio: {prof.bio}")
        click.echo(f"  Followers: {prof.follower_count:,}")
        click.echo(f"  Following: {prof.following_count:,}")
        click.echo(f"  Posts: {prof.post_count:,}")
        click.echo(f"  Verified: {'Yes' if prof.verified else 'No'}")
        click.echo(f"  Profile URL: {prof.profile_url}")

        if include_posts and prof.posts:
            click.echo(f"\n  Recent Posts ({len(prof.posts)}):")
            for i, post in enumerate(prof.posts[:5], 1):
                preview = post.text[:80] + "..." if len(post.text) > 80 else post.text
                click.echo(f"    {i}. {preview}")
                if sentiment:
                    sent_label = "Positive" if post.sentiment > 0 else "Negative" if post.sentiment < 0 else "Neutral"
                    click.echo(f"       Sentiment: {sent_label} ({post.sentiment:.2f})")

        if engagement and prof.engagement_metrics:
            em = prof.engagement_metrics
            click.echo(f"\n  Engagement Metrics:")
            click.echo(f"    Avg Engagement Rate: {em.avg_engagement_rate:.2f}%")
            click.echo(f"    Total Engagement: {em.total_engagement:,}")
            click.echo(f"    Post Frequency: {em.post_frequency:.2f} posts/day")

    if sentiment and any(p.posts for p in profiles.values()):
        click.echo(f"\n\nSentiment Analysis:")
        for plat, prof in profiles.items():
            if prof.posts:
                sentiment_result = analyzer.analyze_sentiment(prof.posts)
                click.echo(f"\n  {plat.upper()}:")
                click.echo(f"    Average Sentiment: {sentiment_result.avg_sentiment:.2f}")
                click.echo(f"    Positive: {sentiment_result.positive_count}")
                click.echo(f"    Negative: {sentiment_result.negative_count}")
                click.echo(f"    Neutral: {sentiment_result.neutral_count}")

    if export and output:
        _export_profile_data(profiles, export, output)
        click.echo(f"\nExport saved to: {output}")


def _fetch_social_profile(
    config: dict[str, Any],
    platform: str,
    username: str,
    details: str,
    post_limit: int,
    include_followers: bool,
    analyze_sentiment: bool,
    calculate_engagement: bool,
) -> SocialProfile | None:
    """Fetch profile from a specific social media platform."""
    social_config = config.get("social_media", {}).get(platform, {})

    if not social_config.get("enabled", False):
        click.echo(f"{platform.title()} is not enabled in config. Skipping.", err=True)
        return None

    try:
        if platform == "twitter":
            from osint.sources.twitter_source import TwitterSource

            source = TwitterSource(social_config)
        elif platform == "facebook":
            from osint.sources.facebook_source import FacebookSource

            source = FacebookSource(social_config)
        elif platform == "linkedin":
            from osint.sources.linkedin_source import LinkedInSource

            source = LinkedInSource(social_config)
        elif platform == "instagram":
            from osint.sources.instagram_source import InstagramSource

            source = InstagramSource(social_config)
        else:
            return None

        if not source.validate_credentials():
            raise RuntimeError(f"Invalid credentials for {platform}")

        profile = source.get_profile(username)

        if post_limit > 0:
            profile.posts = source.get_posts(profile.user_id, limit=post_limit)

        if calculate_engagement and profile.posts:
            profile.engagement_metrics = source.get_engagement_metrics(profile, profile.posts)

        return profile

    except Exception as e:
        logger.error(f"Error fetching {platform} profile: {e}")
        return None


def _export_profile_data(
    profiles: dict[str, SocialProfile],
    format_type: str,
    output: Path,
) -> None:
    """Export profile data to file."""
    output.parent.mkdir(parents=True, exist_ok=True)

    if format_type == "json":
        data = {plat: prof.to_dict() for plat, prof in profiles.items()}
        output.write_text(json.dumps(data, indent=2), encoding="utf-8")

    elif format_type == "csv":
        import csv

        with output.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["platform", "username", "display_name", "followers", "following", "posts", "verified"])

            for plat, prof in profiles.items():
                writer.writerow([
                    plat,
                    prof.username,
                    prof.display_name,
                    prof.follower_count,
                    prof.following_count,
                    prof.post_count,
                    prof.verified,
                ])

    elif format_type == "html":
        html_content = _generate_html_report(profiles)
        output.write_text(html_content, encoding="utf-8")


def _generate_html_report(profiles: dict[str, SocialProfile]) -> str:
    """Generate HTML report for profiles."""
    lines = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        "  <title>OSINT Profile Report</title>",
        "  <style>",
        "    body { font-family: Arial, sans-serif; margin: 20px; }",
        "    .profile { border: 1px solid #ccc; padding: 20px; margin-bottom: 20px; border-radius: 5px; }",
        "    .platform { font-size: 24px; font-weight: bold; color: #333; margin-bottom: 10px; }",
        "    .stat { margin: 5px 0; }",
        "    .label { font-weight: bold; }",
        "  </style>",
        "</head>",
        "<body>",
        "  <h1>OSINT Profile Report</h1>",
        "  <p>Generated on: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "</p>",
    ]

    for plat, prof in profiles.items():
        lines.extend([
            f"  <div class='profile'>",
            f"    <div class='platform'>{plat.upper()}</div>",
            f"    <div class='stat'><span class='label'>Name:</span> {prof.display_name}</div>",
            f"    <div class='stat'><span class='label'>Username:</span> {prof.username}</div>",
            f"    <div class='stat'><span class='label'>Bio:</span> {prof.bio}</div>",
            f"    <div class='stat'><span class='label'>Followers:</span> {prof.follower_count:,}</div>",
            f"    <div class='stat'><span class='label'>Following:</span> {prof.following_count:,}</div>",
            f"    <div class='stat'><span class='label'>Posts:</span> {prof.post_count:,}</div>",
            f"    <div class='stat'><span class='label'>Verified:</span> {'Yes' if prof.verified else 'No'}</div>",
            f"    <div class='stat'><span class='label'>Profile URL:</span> <a href='{prof.profile_url}'>{prof.profile_url}</a></div>",
            "  </div>",
        ])

    lines.extend(["</body>", "</html>"])
    return "\n".join(lines)


@click.command("posts")
@click.option("--username", "-u", type=str, required=True, help="Username.")
@click.option(
    "--platform",
    "-p",
    type=click.Choice(["twitter", "facebook", "linkedin", "instagram"], case_sensitive=False),
    default="twitter",
    show_default=True,
    help="Social media platform.",
)
@click.option("--limit", type=int, default=100, show_default=True, help="Number of posts to fetch.")
@click.option("--sentiment", is_flag=True, default=False, help="Analyze post sentiment.")
@click.option("--hashtags", is_flag=True, default=False, help="Extract and show hashtags.")
@click.option(
    "--export",
    type=click.Choice(["json", "csv"], case_sensitive=False),
    default=None,
    help="Export format.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output file path.",
)
def posts_cmd(
    username: str,
    platform: str,
    limit: int,
    sentiment: bool,
    hashtags: bool,
    export: str | None,
    output: Path | None,
) -> None:
    """Get and analyze posts from a social media profile."""
    config = read_config()
    social_config = config.get("social_media", {}).get(platform, {})

    try:
        profile = _fetch_social_profile(
            config,
            platform,
            username,
            "full",
            limit,
            False,
            sentiment,
            False,
        )

        if not profile or not profile.posts:
            click.echo(f"No posts found for {username} on {platform}")
            return

        click.echo(f"\nPosts from {username} on {platform}:")
        click.echo("=" * 70)

        for i, post in enumerate(profile.posts[:50], 1):
            click.echo(f"\n{i}. {post.timestamp.strftime('%Y-%m-%d %H:%M') if post.timestamp else 'Unknown date'}")
            click.echo(f"   {post.text[:200]}..." if len(post.text) > 200 else f"   {post.text}")
            click.echo(f"   Engagement: {post.likes} likes, {post.shares} shares, {post.comments} comments")

            if sentiment:
                sent_label = "Positive" if post.sentiment > 0 else "Negative" if post.sentiment < 0 else "Neutral"
                click.echo(f"   Sentiment: {sent_label} ({post.sentiment:.2f})")

            if hashtags and post.hashtags:
                click.echo(f"   Hashtags: {', '.join(post.hashtags)}")

        if export and output:
            _export_posts_data(profile.posts, export, output)
            click.echo(f"\nPosts exported to: {output}")

    except Exception as e:
        click.echo(f"Error fetching posts: {e}", err=True)


def _export_posts_data(posts: list[Post], format_type: str, output: Path) -> None:
    """Export posts data to file."""
    output.parent.mkdir(parents=True, exist_ok=True)

    if format_type == "json":
        data = [p.to_dict() for p in posts]
        output.write_text(json.dumps(data, indent=2), encoding="utf-8")

    elif format_type == "csv":
        import csv

        with output.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "platform", "timestamp", "text", "likes", "shares", "comments", "sentiment"])

            for post in posts:
                writer.writerow([
                    post.id,
                    post.platform.value,
                    post.timestamp.isoformat() if post.timestamp else "",
                    post.text[:500],
                    post.likes,
                    post.shares,
                    post.comments,
                    post.sentiment,
                ])


@click.command("followers")
@click.option("--username", "-u", type=str, required=True, help="Username.")
@click.option(
    "--platform",
    "-p",
    type=click.Choice(["twitter", "linkedin", "instagram"], case_sensitive=False),
    default="twitter",
    show_default=True,
    help="Social media platform.",
)
@click.option("--limit", type=int, default=100, show_default=True, help="Number of followers to fetch.")
@click.option(
    "--export",
    type=click.Choice(["json", "csv"], case_sensitive=False),
    default=None,
    help="Export format.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output file path.",
)
def followers_cmd(
    username: str,
    platform: str,
    limit: int,
    export: str | None,
    output: Path | None,
) -> None:
    """Get followers from a social media profile."""
    config = read_config()
    social_config = config.get("social_media", {}).get(platform, {})

    try:
        if platform == "facebook":
            click.echo("Facebook doesn't provide public follower lists for personal profiles.", err=True)
            return

        profile = _fetch_social_profile(config, platform, username, "basic", 0, False, False, False)

        if not profile:
            click.echo(f"Profile not found for {username} on {platform}")
            return

        if platform == "twitter":
            from osint.sources.twitter_source import TwitterSource
            source = TwitterSource(social_config)
        elif platform == "linkedin":
            from osint.sources.linkedin_source import LinkedInSource
            source = LinkedInSource(social_config)
        elif platform == "instagram":
            from osint.sources.instagram_source import InstagramSource
            source = InstagramSource(social_config)
        else:
            return

        followers = source.get_followers(profile.user_id, limit=limit)

        if not followers:
            click.echo(f"No followers found for {username} on {platform}")
            return

        click.echo(f"\nFollowers of {username} on {platform} (showing {len(followers)}):")
        click.echo("=" * 70)

        for i, follower in enumerate(followers, 1):
            click.echo(f"{i}. {follower.display_name} (@{follower.username})")
            if follower.profile_url:
                click.echo(f"   URL: {follower.profile_url}")

        if export and output:
            _export_followers_data(followers, export, output)
            click.echo(f"\nFollowers exported to: {output}")

    except Exception as e:
        click.echo(f"Error fetching followers: {e}", err=True)


def _export_followers_data(followers: list, format_type: str, output: Path) -> None:
    """Export followers data to file."""
    output.parent.mkdir(parents=True, exist_ok=True)

    if format_type == "json":
        data = [f.to_dict() for f in followers]
        output.write_text(json.dumps(data, indent=2), encoding="utf-8")

    elif format_type == "csv":
        import csv

        with output.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "username", "display_name", "profile_url"])

            for follower in followers:
                writer.writerow([
                    follower.id,
                    follower.username,
                    follower.display_name,
                    follower.profile_url or "",
                ])


@click.command("analyze")
@click.option("--username", "-u", type=str, required=True, help="Username to analyze.")
@click.option(
    "--platform",
    "-p",
    type=click.Choice(["twitter", "facebook", "linkedin", "instagram", "all"], case_sensitive=False),
    default="twitter",
    show_default=True,
    help="Social media platform.",
)
@click.option("--limit", type=int, default=100, show_default=True, help="Number of posts to analyze.")
@click.option(
    "--export",
    type=click.Choice(["json", "html"], case_sensitive=False),
    default=None,
    help="Export format.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output file path.",
)
def analyze_cmd(
    username: str,
    platform: str,
    limit: int,
    export: str | None,
    output: Path | None,
) -> None:
    """Perform comprehensive analysis of a social media profile."""
    config = read_config()
    analyzer = ProfileAnalyzer()

    platforms_to_check = [platform] if platform != "all" else ["twitter", "facebook", "linkedin", "instagram"]

    all_analyses: dict[str, dict[str, Any]] = {}

    for plat in platforms_to_check:
        try:
            profile = _fetch_social_profile(
                config,
                plat,
                username,
                "full",
                limit,
                False,
                True,
                True,
            )

            if not profile:
                continue

            analysis = analyzer.analyze_profile(profile)
            all_analyses[plat] = analysis

            click.echo(f"\n{'='*70}")
            click.echo(f"ANALYSIS: {plat.upper()} - @{username}")
            click.echo(f"{'='*70}")

            if analysis.get("engagement"):
                eng = analysis["engagement"]
                click.echo(f"\nEngagement Metrics:")
                click.echo(f"  Avg Engagement Rate: {eng.avg_engagement_rate:.2f}%")
                click.echo(f"  Total Engagement: {eng.total_engagement:,}")
                click.echo(f"  Post Frequency: {eng.post_frequency:.2f} posts/day")

            if analysis.get("sentiment"):
                sent = analysis["sentiment"]
                click.echo(f"\nSentiment Analysis:")
                click.echo(f"  Average Sentiment: {sent.avg_sentiment:.2f}")
                click.echo(f"  Positive Posts: {sent.positive_count}")
                click.echo(f"  Negative Posts: {sent.negative_count}")
                click.echo(f"  Neutral Posts: {sent.neutral_count}")

            if analysis.get("activity"):
                act = analysis["activity"]
                click.echo(f"\nActivity Patterns:")
                click.echo(f"  Avg Posts/Day: {act.avg_posts_per_day:.2f}")
                click.echo(f"  Most Active Hour: {act.most_active_hour}:00")
                click.echo(f"  Most Active Day: {act.most_active_day}")

            if analysis.get("hashtags"):
                tags = analysis["hashtags"]
                click.echo(f"\nHashtag Usage:")
                click.echo(f"  Unique Hashtags: {tags['total_unique_hashtags']}")
                click.echo(f"  Avg Hashtags/Post: {tags['avg_hashtags_per_post']:.2f}")
                if tags["top_hashtags"]:
                    click.echo(f"  Top Hashtags:")
                    for tag_info in tags["top_hashtags"][:5]:
                        click.echo(f"    - #{tag_info['tag']}: {tag_info['count']} uses")

            if analysis.get("influence"):
                inf = analysis["influence"]
                click.echo(f"\nInfluence Score:")
                click.echo(f"  Score: {inf.normalized_score:.1f}/100")
                click.echo(f"  Rank: {inf.rank}")
                click.echo(f"  Factors:")
                for factor, value in inf.factors.items():
                    click.echo(f"    {factor}: {value:.1f}")

            if analysis.get("bot_detection"):
                bot = analysis["bot_detection"]
                if bot.is_bot:
                    click.echo(f"\n⚠️  BOT DETECTED (Confidence: {bot.confidence:.0f}%)")
                    click.echo(f"  Indicators:")
                    for indicator in bot.indicators:
                        click.echo(f"    - {indicator}")
                else:
                    click.echo(f"\n✓ No strong bot indicators (Confidence: {bot.confidence:.0f}%)")

        except Exception as e:
            click.echo(f"Error analyzing {plat} profile: {e}", err=True)

    if not all_analyses:
        click.echo(f"No profiles found for username: {username}")
        return

    if export and output:
        _export_analysis_data(all_analyses, export, output)
        click.echo(f"\nAnalysis exported to: {output}")


def _export_analysis_data(analyses: dict[str, dict[str, Any]], format_type: str, output: Path) -> None:
    """Export analysis data to file."""
    output.parent.mkdir(parents=True, exist_ok=True)

    if format_type == "json":
        serializable_analyses = {}
        for plat, analysis in analyses.items():
            serializable_analyses[plat] = {
                key: (value.to_dict() if hasattr(value, "to_dict") else value)
                for key, value in analysis.items()
            }
        output.write_text(json.dumps(serializable_analyses, indent=2), encoding="utf-8")

    elif format_type == "html":
        lines = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "  <title>OSINT Analysis Report</title>",
            "  <style>",
            "    body { font-family: Arial, sans-serif; margin: 20px; }",
            "    .section { margin-bottom: 30px; }",
            "    .platform { font-size: 28px; font-weight: bold; color: #333; }",
            "    .metric { margin: 10px 0; }",
            "    .value { font-weight: bold; }",
            "    .bot-warning { background-color: #ffcccc; padding: 10px; border-radius: 5px; }",
            "  </style>",
            "</head>",
            "<body>",
            "  <h1>OSINT Analysis Report</h1>",
            "  <p>Generated on: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "</p>",
        ]

        for plat, analysis in analyses.items():
            lines.extend([
                "  <div class='section'>",
                f"    <div class='platform'>{plat.upper()}</div>",
            ])

            if analysis.get("engagement"):
                eng = analysis["engagement"]
                lines.extend([
                    "    <h3>Engagement</h3>",
                    f"    <div class='metric'>Avg Engagement Rate: <span class='value'>{eng.avg_engagement_rate:.2f}%</span></div>",
                    f"    <div class='metric'>Total Engagement: <span class='value'>{eng.total_engagement:,}</span></div>",
                ])

            if analysis.get("sentiment"):
                sent = analysis["sentiment"]
                lines.extend([
                    "    <h3>Sentiment</h3>",
                    f"    <div class='metric'>Average: <span class='value'>{sent.avg_sentiment:.2f}</span></div>",
                    f"    <div class='metric'>Positive: <span class='value'>{sent.positive_count}</span></div>",
                ])

            if analysis.get("bot_detection") and analysis["bot_detection"].is_bot:
                bot = analysis["bot_detection"]
                lines.extend([
                    f"    <div class='bot-warning'>",
                    f"      <strong>⚠️ BOT DETECTED</strong> (Confidence: {bot.confidence:.0f}%)",
                    "    </div>",
                ])

            lines.append("  </div>")

        lines.extend(["</body>", "</html>"])
        output.write_text("\n".join(lines), encoding="utf-8")


@click.command("compare")
@click.option("--usernames", type=str, required=True, help="Comma-separated usernames to compare.")
@click.option(
    "--platform",
    "-p",
    type=click.Choice(["twitter", "facebook", "linkedin", "instagram"], case_sensitive=False),
    default="twitter",
    show_default=True,
    help="Social media platform.",
)
def compare_cmd(usernames: str, platform: str) -> None:
    """Compare multiple users on the same platform."""
    config = read_config()

    username_list = [u.strip() for u in usernames.split(",")]
    if len(username_list) < 2:
        raise click.ClickException("Need at least 2 usernames to compare")

    profiles: list[SocialProfile] = []

    for username in username_list:
        try:
            profile = _fetch_social_profile(
                config,
                platform,
                username,
                "standard",
                10,
                False,
                False,
                True,
            )
            if profile:
                profiles.append(profile)
        except Exception as e:
            click.echo(f"Error fetching profile for {username}: {e}", err=True)

    if len(profiles) < 2:
        raise click.ClickException("Need at least 2 profiles to compare")

    analyzer = ProfileAnalyzer()
    comparison = analyzer.compare_profiles(profiles)

    click.echo(f"\n{'='*70}")
    click.echo(f"COMPARISON: {platform.upper()}")
    click.echo(f"{'='*70}")

    click.echo(f"\nFollowers:")
    for metric in sorted(comparison["metrics"]["followers"], key=lambda x: x["count"], reverse=True):
        click.echo(f"  {metric['username']}: {metric['count']:,}")

    click.echo(f"\nPosts:")
    for metric in sorted(comparison["metrics"]["posts"], key=lambda x: x["count"], reverse=True):
        click.echo(f"  {metric['username']}: {metric['count']:,}")

    click.echo(f"\nEngagement Rates:")
    for metric in sorted(comparison["metrics"]["engagement_rates"], key=lambda x: x["rate"], reverse=True):
        click.echo(f"  {metric['username']}: {metric['rate']:.2f}%")

    click.echo(f"\n🏆 Most Influential: {comparison['most_engaging']['username']}")

    if comparison.get("highest_followers"):
        click.echo(f"👥 Most Followers: {comparison['highest_followers']['username']}")

