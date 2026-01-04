# OSINT Dashboard - User Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Search Interface](#search-interface)
3. [Viewing Results](#viewing-results)
4. [Graph Visualization](#graph-visualization)
5. [Identity Profiles](#identity-profiles)
6. [Timeline Analysis](#timeline-analysis)
7. [Export & Reporting](#export--reporting)
8. [Workspaces](#workspaces)
9. [Settings](#settings)
10. [Keyboard Shortcuts](#keyboard-shortcuts)
11. [Tips & Best Practices](#tips--best-practices)

---

## Getting Started

### First Launch
When you first open the OSINT Dashboard, you'll see the search interface. This is your starting point for all investigations.

### Interface Overview
- **Header**: Logo, search bar, navigation menu, and user menu
- **Sidebar**: Quick actions, recent searches, saved searches, and workspaces
- **Main Area**: Primary content (search, results, graph, etc.)
- **Details Panel**: Identity details when a node is selected

---

## Search Interface

### Basic Search
1. Click in the search bar or press `/`
2. Enter your search term:
   - Username: `@username` or `username`
   - Email: `user@domain.com`
   - Phone: `(123) 456-7890` or `1234567890`
   - Name: `John Doe`
   - Domain: `example.com`
3. Press Enter or click "Search"

### Search Types
Select a specific search type for more targeted results:
- **All**: Searches across all data types
- **Username**: Social media handles and usernames
- **Email**: Email addresses
- **Phone**: Phone numbers
- **Name**: Person names
- **Domain**: Domain names and websites

### Advanced Filters
Click "Show Advanced Filters" to access:

**Confidence Threshold**
- Set minimum confidence level (0-100%)
- Higher values = more accurate results
- Lower values = more results

**Data Sources**
- Select specific platforms to search
- Twitter, LinkedIn, GitHub, Facebook, Instagram, Reddit
- Uncheck sources you want to exclude

**Date Range**
- Filter results by date
- Set start and end dates
- Useful for timeline analysis

### Autocomplete
- Type 2+ characters to see suggestions
- Click a suggestion to use it
- Based on previous searches and common patterns

### Search History
- View recent searches in the sidebar
- Click a previous search to repeat it
- Automatically saved (last 20 searches)

### Saved Searches
- Click the star icon to save a search
- Include filters and search type
- Access from sidebar or search interface

---

## Viewing Results

### Results Display
Results are organized into tabs:
- **All Results**: Everything found
- **Identities**: Person profiles and accounts
- **Profiles**: Social media profiles
- **Domains**: Domain information

### Result Cards
Each result shows:
- Profile picture or icon
- Name/username
- Source (platform)
- Timestamp
- Confidence score (color-coded)
- Description/preview
- "View Details" button

### Confidence Scores
- 🟢 Green (80-100%): High confidence
- 🟡 Yellow (50-79%): Medium confidence
- 🔴 Red (0-49%): Low confidence

### Sorting Options
- **Relevance**: Best matches first
- **Confidence**: Highest confidence first
- **Date**: Newest first

### Pagination
- Results per page: 10, 20, 50, or 100
- Use navigation buttons at bottom
- Shows current page and total results

### Actions
- **View Details**: Open full profile
- **Add to Workspace**: Save to current workspace
- **Export**: Export individual result

---

## Graph Visualization

### Overview
The graph shows relationships between identities, accounts, and data points.

### Node Types
- 🔵 **Identity**: Person profiles
- 🟢 **Email**: Email addresses
- 🟠 **Phone**: Phone numbers
- 🔴 **Address**: Physical addresses
- 🟣 **Domain**: Websites/domains
- 🟡 **Organization**: Companies
- 🔵 **Social Media**: Social accounts
- 🟣 **Username**: Usernames

### Edge Types
- **LINKED_TO**: General connection
- **MENTIONS**: One mentions another
- **POSTED_ON**: Content posted on platform
- **WORKS_FOR**: Employment relationship
- **LIVES_AT**: Residential address
- **OWNS**: Ownership
- **ASSOCIATES_WITH**: Known associate
- **REGISTERED_TO**: Domain registration
- **POSTED_BY**: Content authorship

### Controls

**Zoom**
- Mouse wheel to zoom
- + button to zoom in
- - button to zoom out

**Pan**
- Click and drag to move
- Arrow keys to pan

**Select Node**
- Click a node to select
- Details appear in right panel
- Connected nodes highlighted

**Layout Options**
- **Force-Directed**: Natural clustering
- **Hierarchical**: Tree-like structure
- **Circular**: Nodes in a circle

### Filters
Click the layers icon to filter:
- Filter by node type
- Filter by edge type
- Show/hide specific relationships

### Statistics
Bottom-right shows:
- Total nodes
- Total edges
- Network density

### Context Menu
Right-click a node for:
- View details
- Expand connections
- Hide node
- Copy ID

---

## Identity Profiles

### Profile Header
- Profile picture
- Primary name
- Confidence score
- Last updated date
- Data sources

### Profile Sections

**Basic Info**
- Name, email, phone
- Address
- Company, job title
- Date of birth

**Social Media**
- Platform name
- Username
- Profile URL
- Verification status
- Followers, following
- Bio

**Online Presence**
- Websites
- Blogs
- Public content
- GitHub repositories

**Employment**
- Company name
- Job title
- Start/end dates
- Current position indicator
- Location

**Education**
- Institution
- Degree
- Field of study
- Graduation date

**Relationships**
- Related people
- Relationship type
- Confidence level
- Description

**Activity**
- Recent actions
- Timeline events
- Platform activity

### Data Sources
- View all sources
- Source confidence
- Retrieved date
- Click to verify

---

## Timeline Analysis

### Timeline View
Chronological display of events and activities.

### Event Types
- 🟢 **Account Created**: Registration dates
- 🔵 **Post**: Content publication
- 🟡 **Profile Update**: Changes to profile
- 🟣 **Activity**: Other actions

### Filters
- Filter by event type
- Filter by date range
- Filter by platform
- Group by category

### Timeline Features
- Hover for details
- Click event to expand
- Color-coded by type
- Shows exact timestamps

### Export Timeline
- Export as image
- Export as CSV
- Export as JSON
- Include in reports

---

## Export & Reporting

### Export Formats

**JSON**
- Complete structured data
- Machine-readable
- Best for data processing

**CSV**
- Tabular data
- Excel-compatible
- Best for spreadsheets

**XLSX**
- Excel workbook
- Multiple sheets
- Formatted data

**PDF**
- Formatted report
- Includes graphs
- Printable

**HTML**
- Interactive report
- Self-contained
- Shareable

### Report Templates

**Standard Report**
- Basic information
- Social profiles
- Employment history
- Key findings

**Executive Summary**
- High-level overview
- Key metrics
- Critical information
- Minimal detail

**Detailed Analysis**
- Complete information
- All data points
- Network analysis
- Timeline

**Relationship Map**
- Focus on connections
- Network graph
- Relationship details

**Timeline Report**
- Chronological events
- Activity analysis
- Platform breakdown

### Export Options
- Include/exclude graph
- Include/exclude timeline
- Set confidence threshold
- Data source attribution
- Redaction options

### Batch Export
- Export multiple identities
- Scheduled exports
- Export history

---

## Workspaces

### What are Workspaces?
Workspaces help organize investigations. Each workspace can contain:
- Saved searches
- Search results
- Graph data
- Notes
- Tags

### Creating a Workspace
1. Click "New Workspace"
2. Enter workspace name
3. Add description (optional)
4. Click "Create"

### Using Workspaces
- Switch between workspaces
- Add searches to workspace
- Save results
- Add notes
- Tag for organization

### Workspace Features
- Multiple concurrent workspaces
- Import/export workspaces
- Share with team (future)
- Workspace history

---

## Settings

### Display Settings

**Theme**
- Light mode
- Dark mode
- Auto (system preference)

**Graph Layout**
- Force-directed (default)
- Hierarchical
- Circular

**Results Per Page**
- 10, 20, 50, or 100

### Data Settings

**Confidence Threshold**
- Default minimum confidence
- Applied to all searches

**Preferred Data Sources**
- Select default sources
- Platform preferences

**NSFW Content**
- Include/exclude adult content

### Advanced Settings

**API Timeout**
- Request timeout in milliseconds
- Default: 30000ms (30 seconds)

**Cache Settings**
- Enable/disable caching
- Clear cache

**Performance**
- Graph rendering options
- Virtual scrolling

---

## Keyboard Shortcuts

### Global
- `/` - Focus search bar
- `Esc` - Close modals
- `Ctrl+K` - Quick search
- `Ctrl+,` - Settings

### Navigation
- `Ctrl+1` - Search view
- `Ctrl+2` - Results view
- `Ctrl+3` - Graph view
- `Ctrl+4` - Timeline view
- `Ctrl+5` - Export view

### Graph
- `+` - Zoom in
- `-` - Zoom out
- `F` - Fit to screen
- `R` - Reset view
- Arrow keys - Pan

### Results
- `j` - Next result
- `k` - Previous result
- `Enter` - View details
- `Space` - Quick preview

---

## Tips & Best Practices

### Search Tips
1. **Start broad, then narrow**: Use "All" type first, then filter
2. **Use quotes**: Search exact phrases with quotes
3. **Multiple searches**: Combine different search types
4. **Check confidence**: Focus on high-confidence results
5. **Date filters**: Use for recent or historical data

### Investigation Workflow
1. Start with known identifier (email, username)
2. Review all results for accuracy
3. Visualize relationships in graph
4. Expand connected nodes
5. Build timeline of activity
6. Export findings for documentation

### Graph Best Practices
1. Use filters to reduce clutter
2. Focus on high-centrality nodes
3. Look for unexpected connections
4. Expand nodes gradually
5. Switch layouts for different views

### Performance Tips
1. Limit graph to 1000 nodes
2. Use filters to reduce data
3. Close unused tabs
4. Clear cache periodically
5. Use pagination for large result sets

### Data Quality
1. Verify multiple sources
2. Check confidence scores
3. Cross-reference information
4. Note data freshness
5. Document uncertainties

### Privacy & Ethics
1. Use responsibly
2. Verify before acting
3. Respect privacy laws
4. Document your process
5. Secure your findings

---

## Troubleshooting

### Common Issues

**No Results Found**
- Check spelling
- Try different search types
- Lower confidence threshold
- Expand date range

**Graph Not Loading**
- Check browser console
- Refresh page
- Reduce node count
- Try different layout

**Slow Performance**
- Close other tabs
- Reduce graph size
- Clear cache
- Disable physics simulation

**Export Failed**
- Check data size
- Try different format
- Verify permissions
- Check browser console

---

## Support

For additional help:
- Check FAQ
- View video tutorials
- Contact support
- Report issues on GitHub

## Updates

This dashboard is regularly updated with:
- New features
- Bug fixes
- Performance improvements
- Security patches

Check the changelog for recent updates.
