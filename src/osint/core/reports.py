from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from osint.core.models import CorrelationResult, Entity, Relationship


class ReportGenerator:
    """Generate correlation reports in various formats."""

    def generate_text_report(self, result: CorrelationResult) -> str:
        """Generate a human-readable text report."""
        lines: list[str] = []

        lines.append("=" * 70)
        lines.append("OSINT CORRELATION REPORT")
        lines.append("=" * 70)
        lines.append("")

        # Summary section
        lines.append("SUMMARY")
        lines.append("-" * 70)
        lines.append(result.summary)
        lines.append("")

        # Entity breakdown
        lines.append("ENTITY BREAKDOWN")
        lines.append("-" * 70)

        entity_types: dict[str, list[Entity]] = {}
        for entity in result.entities:
            entity_type = entity.type.value
            if entity_type not in entity_types:
                entity_types[entity_type] = []
            entity_types[entity_type].append(entity)

        for entity_type, entities in sorted(entity_types.items()):
            lines.append(f"\n{entity_type.upper()} ({len(entities)})")
            for entity in entities[:20]:  # Limit to 20 per type
                lines.append(f"  - {entity.name} (ID: {entity.id[:16]}...)")
                if entity.sources:
                    lines.append(f"    Sources: {', '.join(entity.sources[:3])}")

            if len(entities) > 20:
                lines.append(f"  ... and {len(entities) - 20} more")

        # Relationships section
        lines.append("\n")
        lines.append("KEY RELATIONSHIPS")
        lines.append("-" * 70)

        # Sort by confidence and show top 30
        top_relationships = sorted(
            result.relationships, key=lambda r: r.confidence, reverse=True
        )[:30]

        for rel in top_relationships:
            entity_a = self._get_entity_name(rel.entity_a, result.entities)
            entity_b = self._get_entity_name(rel.entity_b, result.entities)
            lines.append(f"\n{entity_a} <-> {entity_b}")
            lines.append(f"  Type: {rel.type.value}")
            lines.append(f"  Confidence: {rel.confidence:.1f}%")
            if rel.evidence:
                lines.append(f"  Evidence:")
                for ev in rel.evidence[:3]:
                    lines.append(f"    - {ev}")

        if len(result.relationships) > 30:
            lines.append(f"\n... and {len(result.relationships) - 30} more relationships")

        # Clusters section
        if result.clusters:
            lines.append("\n")
            lines.append("IDENTIFIED CLUSTERS")
            lines.append("-" * 70)

            for i, cluster in enumerate(result.clusters[:10], 1):
                lines.append(f"\nCluster {i} (confidence: {cluster.confidence:.1f}%)")
                lines.append(f"  Size: {len(cluster.entities)} entities")
                representative = self._get_entity_name(
                    cluster.representative, result.entities
                )
                lines.append(f"  Representative: {representative}")

            if len(result.clusters) > 10:
                lines.append(f"\n... and {len(result.clusters) - 10} more clusters")

        # Confidence distribution
        lines.append("\n")
        lines.append("CONFIDENCE DISTRIBUTION")
        lines.append("-" * 70)

        high_conf = sum(1 for r in result.relationships if r.confidence >= 80)
        med_conf = sum(
            1 for r in result.relationships if 50 <= r.confidence < 80
        )
        low_conf = sum(1 for r in result.relationships if r.confidence < 50)

        if result.relationships:
            total = len(result.relationships)
            lines.append(f"High confidence (80-100%): {high_conf} ({high_conf/total:.1%})")
            lines.append(f"Medium confidence (50-79%): {med_conf} ({med_conf/total:.1%})")
            lines.append(f"Low confidence (0-49%): {low_conf} ({low_conf/total:.1%})")
        else:
            lines.append("No relationships found.")

        lines.append("\n")
        lines.append("=" * 70)
        lines.append("END OF REPORT")
        lines.append("=" * 70)

        return "\n".join(lines)

    def generate_json_report(self, result: CorrelationResult) -> str:
        """Generate a structured JSON report."""
        return json.dumps(result.to_dict(), indent=2)

    def generate_html_report(self, result: CorrelationResult) -> str:
        """Generate an interactive HTML report with visualization."""
        html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OSINT Correlation Report</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        h2 {
            color: #34495e;
            margin-top: 30px;
            margin-bottom: 15px;
            padding-bottom: 5px;
            border-bottom: 2px solid #ecf0f1;
        }
        h3 {
            color: #7f8c8d;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        .summary {
            background: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            white-space: pre-line;
        }
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 5px;
            text-align: center;
        }
        .stat-card .value {
            font-size: 2em;
            font-weight: bold;
        }
        .stat-card .label {
            font-size: 0.9em;
            opacity: 0.9;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background: #34495e;
            color: white;
            font-weight: 600;
        }
        tr:hover {
            background: #f8f9fa;
        }
        .confidence-high {
            color: #27ae60;
            font-weight: bold;
        }
        .confidence-medium {
            color: #f39c12;
            font-weight: bold;
        }
        .confidence-low {
            color: #e74c3c;
            font-weight: bold;
        }
        .badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.85em;
            font-weight: 600;
        }
        .badge-person { background: #3498db; color: white; }
        .badge-account { background: #2ecc71; color: white; }
        .badge-email { background: #9b59b6; color: white; }
        .badge-phone { background: #e67e22; color: white; }
        .badge-domain { background: #1abc9c; color: white; }
        .badge-ip { background: #e74c3c; color: white; }
        .evidence-list {
            list-style: none;
            padding-left: 0;
        }
        .evidence-list li {
            padding: 5px 0;
            padding-left: 20px;
            position: relative;
        }
        .evidence-list li:before {
            content: "•";
            position: absolute;
            left: 0;
            color: #3498db;
            font-weight: bold;
        }
        .cluster-card {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 15px;
            margin: 10px 0;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ecf0f1;
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>OSINT Correlation Report</h1>

        <div class="stat-grid">
            <div class="stat-card">
                <div class="value">{len(result.entities)}</div>
                <div class="label">Entities</div>
            </div>
            <div class="stat-card">
                <div class="value">{len(result.relationships)}</div>
                <div class="label">Relationships</div>
            </div>
            <div class="stat-card">
                <div class="value">{len(result.clusters)}</div>
                <div class="label">Clusters</div>
            </div>
            <div class="stat-card">
                <div class="value">{result.confidence_average:.1f}%</div>
                <div class="label">Avg Confidence</div>
            </div>
        </div>

        <h2>Summary</h2>
        <div class="summary">{result.summary}</div>

        <h2>Entities by Type</h2>
"""

        # Group entities by type
        entity_types: dict[str, list[Entity]] = {}
        for entity in result.entities:
            entity_type = entity.type.value
            if entity_type not in entity_types:
                entity_types[entity_type] = []
            entity_types[entity_type].append(entity)

        for entity_type, entities in sorted(entity_types.items()):
            html += f"<h3>{entity_type.upper()} ({len(entities)})</h3>\n"
            html += "<table>\n"
            html += "<tr><th>Name</th><th>Sources</th></tr>\n"

            for entity in entities[:50]:
                sources = ", ".join(entity.sources[:3])
                html += f'<tr><td>{entity.name}</td><td>{sources}</td></tr>\n'

            html += "</table>\n"

            if len(entities) > 50:
                html += f"<p>... and {len(entities) - 50} more entities</p>\n"

        # Add relationships section
        html += '<h2>Key Relationships</h2>\n'

        top_relationships = sorted(
            result.relationships, key=lambda r: r.confidence, reverse=True
        )[:50]

        html += '<table>\n'
        html += "<tr><th>Entity A</th><th>Entity B</th><th>Type</th><th>Confidence</th><th>Evidence</th></tr>\n"

        for rel in top_relationships:
            entity_a = self._get_entity_name(rel.entity_a, result.entities)
            entity_b = self._get_entity_name(rel.entity_b, result.entities)

            conf_class = "confidence-high" if rel.confidence >= 80 else "confidence-medium" if rel.confidence >= 50 else "confidence-low"
            evidence_str = "; ".join(rel.evidence[:2])

            html += f'<tr>\n'
            html += f'<td>{entity_a}</td>\n'
            html += f'<td>{entity_b}</td>\n'
            html += f'<td><span class="badge">{rel.type.value}</span></td>\n'
            html += f'<td class="{conf_class}">{rel.confidence:.1f}%</td>\n'
            html += f'<td>{evidence_str}</td>\n'
            html += f'</tr>\n'

        html += "</table>\n"

        if len(result.relationships) > 50:
            html += f"<p>... and {len(result.relationships) - 50} more relationships</p>\n"

        # Add clusters section
        if result.clusters:
            html += '<h2>Identified Clusters</h2>\n'

            for i, cluster in enumerate(result.clusters[:10], 1):
                representative = self._get_entity_name(cluster.representative, result.entities)
                html += f'<div class="cluster-card">\n'
                html += f'<h3>Cluster {i} - Confidence: {cluster.confidence:.1f}%</h3>\n'
                html += f'<p><strong>Size:</strong> {len(cluster.entities)} entities</p>\n'
                html += f'<p><strong>Representative:</strong> {representative}</p>\n'
                html += f'<p><strong>Entities:</strong></p>\n'
                html += '<ul class="evidence-list">\n'

                for entity_id in cluster.entities[:10]:
                    entity_name = self._get_entity_name(entity_id, result.entities)
                    html += f'<li>{entity_name}</li>\n'

                html += '</ul>\n'

                if len(cluster.entities) > 10:
                    html += f'<p>... and {len(cluster.entities) - 10} more entities</p>\n'

                html += '</div>\n'

        # Add confidence distribution
        html += '<h2>Confidence Distribution</h2>\n'

        high_conf = sum(1 for r in result.relationships if r.confidence >= 80)
        med_conf = sum(1 for r in result.relationships if 50 <= r.confidence < 80)
        low_conf = sum(1 for r in result.relationships if r.confidence < 50)

        if result.relationships:
            total = len(result.relationships)
            html += '<table>\n'
            html += '<tr><th>Range</th><th>Count</th><th>Percentage</th></tr>\n'
            html += f'<tr><td>High (80-100%)</td><td>{high_conf}</td><td>{high_conf/total:.1%}</td></tr>\n'
            html += f'<tr><td>Medium (50-79%)</td><td>{med_conf}</td><td>{med_conf/total:.1%}</td></tr>\n'
            html += f'<tr><td>Low (0-49%)</td><td>{low_conf}</td><td>{low_conf/total:.1%}</td></tr>\n'
            html += '</table>\n'
        else:
            html += '<p>No relationships found.</p>\n'

        html += """
        <div class="footer">
            <p>Generated by Not-your-mom's OSINT Correlation Engine</p>
        </div>
    </div>
</body>
</html>
"""
        return html

    def _get_entity_name(self, entity_id: str, entities: list[Entity]) -> str:
        """Get entity name by ID."""
        for entity in entities:
            if entity.id == entity_id:
                return entity.name
        return f"Unknown ({entity_id[:16]}...)"

    def save_report(
        self, result: CorrelationResult, format: str, output_path: Path
    ) -> None:
        """Save report to file."""
        if format == "json":
            content = self.generate_json_report(result)
        elif format == "html":
            content = self.generate_html_report(result)
        else:
            content = self.generate_text_report(result)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
