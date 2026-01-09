# OSINT Correlation Engine

The correlation engine is the heart of the Not-your-mom's-OSINT platform. It analyzes findings from all sources and identifies connections, relationships, and patterns between entities.

## Features

- **Entity Recognition**: Automatically identifies unique entities (people, accounts, emails, domains, IPs) from search results
- **Relationship Detection**: Finds connections between entities using multiple correlation algorithms
- **Confidence Scoring**: Calculates confidence scores (0-100%) for each correlation
- **Graph Building**: Builds relationship graphs for visualization and analysis
- **Pattern Detection**: Identifies suspicious patterns and clusters of related entities

## CLI Commands

### correlate

Correlate findings and identify relationships.

```bash
# Correlate search results from a JSON file
osint correlate --search-results results.json

# Correlate findings for a specific username
osint correlate --username john_doe

# Correlate specific entities
osint correlate --entities entity1,entity2,entity3

# Generate reports
osint correlate --search-results results.json --report html --output report.html
```

**Options:**
- `--search-results PATH` - File with search results to correlate (JSON format)
- `--username TEXT` - Correlate findings for a specific username
- `--entities TEXT` - Specific entities to correlate (comma-separated IDs)
- `--report [text|json|html]` - Report format (default: text)
- `--output PATH` - Output file path for report

### graph

Explore and export relationship graphs.

```bash
# Show overall graph statistics
osint graph

# Explore relationships from a specific entity
osint graph --entity entity_id --depth 2

# Export graph data
osint graph --export graphml --output network.graphml
osint graph --export json --output network.json

# Filter by confidence
osint graph --min-confidence 75
```

**Options:**
- `--entity TEXT` - Entity ID to start exploration from
- `--depth INTEGER` - How many relationship hops to follow (default: 2)
- `--export [json|graphml|gexf]` - Export format for graph data
- `--output PATH` - Output file path for graph export
- `--min-confidence FLOAT` - Minimum confidence threshold (default: 0.0)

### relationships

Query and display relationships with filtering.

```bash
# Show all relationships
osint relationships

# Filter by type
osint relationships --type same_person

# Filter by confidence
osint relationships --min-confidence 80

# Show relationships for a specific entity
osint relationships --entity entity_id

# Limit results
osint relationships --limit 50
```

**Options:**
- `--type [same_person|related|potential|suspicious]` - Filter by relationship type
- `--min-confidence FLOAT` - Minimum confidence threshold (default: 0.0)
- `--entity TEXT` - Show relationships for a specific entity
- `--limit INTEGER` - Maximum number of relationships to show (default: 20)

## Correlation Algorithms

### Username Correlation

Identifies connections between accounts based on usernames:
- **Exact matches**: Same username across platforms
- **Fuzzy matching**: Similar usernames using Levenshtein distance
- **Pattern variations**: Common patterns (john_doe vs johndoe, johndoe99 vs johndoe)

### Email Correlation

Connects entities based on email addresses:
- **Exact matches**: Same email across accounts
- **Pattern analysis**: Email patterns (firstname.lastname@domain)
- **Domain ownership**: Accounts sharing email domains

### Metadata Correlation

Finds connections through profile metadata:
- **Bio/description**: Similar text in profiles
- **Location**: Same or related locations
- **Display name**: Identical or similar names
- **Website**: Same website links

### Network Correlation

Identifies relationships through network information:
- **IP addresses**: Exact matches and subnet relationships
- **Domains**: Same domains and subdomain relationships
- **Similar domains**: Potential typosquatting detection

### Temporal Correlation

Finds patterns in timing:
- **Account creation**: Accounts created around the same time
- **Activity patterns**: Overlapping activity times
- **Timezone patterns**: Similar posting schedules

## Relationship Types

- **same_person**: High confidence that entities represent the same person
- **related**: Entities are likely connected (e.g., family, colleagues)
- **potential**: Possible connection, requires further investigation
- **suspicious**: Unusual patterns that may indicate fraudulent accounts

## Confidence Scoring

Confidence scores (0-100%) are calculated based on:

1. **Attribute Matches** (30%): Number of matching attributes
2. **Source Quality** (20%): Reliability of data sources
3. **Temporal Consistency** (20%): Consistency over time
4. **Uniqueness Factor** (30%): How unique the matching attributes are

**Confidence Levels:**
- **80-100%**: High confidence - Very likely to be accurate
- **50-79%**: Medium confidence - Reasonably likely
- **0-49%**: Low confidence - Requires verification

## Report Formats

### Text Report

Human-readable summary with:
- Entity breakdown by type
- Key relationships with evidence
- Cluster information
- Confidence distribution

### JSON Report

Structured data with all entities, relationships, and clusters. Useful for programmatic analysis.

### HTML Report

Interactive web-based report with:
- Visual statistics cards
- Formatted tables for entities and relationships
- Color-coded confidence levels
- Responsive design

## Graph Exports

### JSON

Node-link format compatible with D3.js and other visualization libraries.

### GraphML

Format for Gephi and other graph analysis tools.

### GEXF

Format for Gephi graph visualization and analysis.

## Usage Examples

### Example 1: Correlate Search Results

```bash
# Search for a username
osint search --username john_doe --export json --output results.json

# Correlate the results
osint correlate --search-results results.json --report html --output report.html
```

### Example 2: Explore Entity Network

```bash
# Correlate results first
osint correlate --username john_doe

# Explore relationships
osint graph --entity account_twitter_john_doe --depth 3

# Export the graph for visualization
osint graph --export graphml --output network.graphml
```

### Example 3: Find High-Confidence Connections

```bash
# Find same-person relationships with high confidence
osint relationships --type same_person --min-confidence 85

# Or using the graph command
osint graph --min-confidence 85
```

### Example 4: Cluster Analysis

```bash
# Run correlation
osint correlate --search-results results.json

# Export full graph
osint graph --export json --output network.json

# Load into Gephi for advanced visualization and cluster detection
```

## Performance

The correlation engine is designed to handle large datasets:
- Tested with 1000+ entities
- Efficient graph algorithms using NetworkX
- O(n²) correlation complexity (typical for pairwise comparisons)

## Advanced Topics

### Saving and Loading

Correlation data can be persisted for later analysis:

```bash
# Correlate results (data is stored in memory)
osint correlate --search-results results.json

# Export correlation data
osint graph --export json --output correlation_data.json

# Load in a new session (via API, not CLI yet)
```

### Incremental Updates

The correlation engine supports adding new data incrementally:

```python
from osint.core.correlation import CorrelationEngine

engine = CorrelationEngine()

# First batch
results1 = load_results("batch1.json")
engine.process_query_results(results1)

# Second batch (adds to existing data)
results2 = load_results("batch2.json")
engine.process_query_results(results2)
```

### Custom Confidence Weights

Adjust confidence scoring weights in the configuration:

```python
from osint.core.scoring import ConfidenceScoring

scoring = ConfidenceScoring(
    attribute_weight=0.4,      # Increase emphasis on attributes
    source_quality_weight=0.1,   # Decrease emphasis on sources
    temporal_consistency_weight=0.2,
    uniqueness_weight=0.3,
)
```

## Architecture

```
src/osint/core/
├── correlation.py       # Main correlation engine
├── models.py           # Data models (Entity, Relationship, etc.)
├── graph.py            # Graph management with NetworkX
├── scoring.py          # Confidence scoring system
├── reports.py          # Report generation
└── algorithms/
    ├── username.py      # Username correlation
    ├── email.py        # Email correlation
    ├── metadata.py     # Metadata correlation
    ├── network.py      # Network correlation
    └── temporal.py     # Temporal correlation
```

## Limitations

- Correlation is probabilistic and may produce false positives
- Quality depends on data completeness from source platforms
- Some algorithms (fuzzy matching) may miss variations
- IP correlations are limited by available geolocation data

## Future Enhancements

- Machine learning-based correlation
- Multi-language support for metadata analysis
- Real-time correlation updates
- Web-based visualization interface
- Integration with external graph databases (Neo4j)
