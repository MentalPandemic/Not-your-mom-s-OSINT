import React from 'react';
import './GraphVisualization.css';

function GraphVisualization({ graphData }) {
  if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
    return (
      <div className="graph-visualization card">
        <h3>Relationship Graph</h3>
        <div className="graph-placeholder">
          <p>No graph data available</p>
          <p className="graph-info">
            Once data is collected, this will display a visual representation of 
            relationships between identities, profiles, and content.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="graph-visualization card">
      <h3>Relationship Graph</h3>
      <div className="graph-stats">
        <span>{graphData.total_nodes} nodes</span>
        <span>{graphData.total_edges} connections</span>
      </div>
      <div className="graph-container">
        <div className="graph-placeholder">
          <p>Graph visualization will be implemented in Phase 1 tasks</p>
          <p className="graph-info">
            This will use react-force-graph or d3.js to display interactive 
            network graphs showing connections between entities.
          </p>
        </div>
      </div>
    </div>
  );
}

export default GraphVisualization;
