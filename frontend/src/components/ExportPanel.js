import React, { useState } from 'react';
import './ExportPanel.css';

function ExportPanel({ searchId, onExport }) {
  const [exportFormat, setExportFormat] = useState('json');
  const [includeContent, setIncludeContent] = useState(true);
  const [includeRelationships, setIncludeRelationships] = useState(true);
  const [loading, setLoading] = useState(false);

  const handleExport = async () => {
    setLoading(true);
    try {
      await onExport({
        search_id: searchId,
        format: exportFormat,
        include_content: includeContent,
        include_relationships: includeRelationships,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="export-panel card">
      <h3>Export Results</h3>
      
      <div className="export-options">
        <div className="export-option-group">
          <label>Export Format:</label>
          <select
            className="input"
            value={exportFormat}
            onChange={(e) => setExportFormat(e.target.value)}
            disabled={loading}
          >
            <option value="json">JSON</option>
            <option value="csv">CSV</option>
            <option value="graphml">GraphML (for graph tools)</option>
          </select>
        </div>

        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={includeContent}
            onChange={(e) => setIncludeContent(e.target.checked)}
            disabled={loading}
          />
          <span>Include content items</span>
        </label>

        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={includeRelationships}
            onChange={(e) => setIncludeRelationships(e.target.checked)}
            disabled={loading}
          />
          <span>Include relationships</span>
        </label>
      </div>

      <button
        className="button export-button"
        onClick={handleExport}
        disabled={loading || !searchId}
      >
        {loading ? 'Preparing Export...' : 'Export Data'}
      </button>

      <div className="export-info">
        <p>
          Exports will include all collected data from the search operation.
          GraphML format is compatible with Gephi, Cytoscape, and other graph analysis tools.
        </p>
      </div>
    </div>
  );
}

export default ExportPanel;
