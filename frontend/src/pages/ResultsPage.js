import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import ResultsView from '../components/ResultsView';
import GraphVisualization from '../components/GraphVisualization';
import ExportPanel from '../components/ExportPanel';
import { resultsAPI, graphAPI, exportAPI } from '../services/api';
import './ResultsPage.css';

function ResultsPage() {
  const { searchId } = useParams();
  const [results, setResults] = useState(null);
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('results');

  useEffect(() => {
    if (searchId) {
      fetchResults();
      fetchGraph();
    }
  }, [searchId]);

  const fetchResults = async () => {
    try {
      const data = await resultsAPI.getResults(searchId);
      setResults(data);
    } catch (err) {
      console.error('Error fetching results:', err);
      setError('Failed to fetch results');
    } finally {
      setLoading(false);
    }
  };

  const fetchGraph = async () => {
    try {
      const data = await graphAPI.getGraph(searchId);
      setGraphData(data);
    } catch (err) {
      console.error('Error fetching graph:', err);
    }
  };

  const handleExport = async (exportData) => {
    try {
      const response = await exportAPI.createExport(exportData);
      
      if (response.download_url) {
        window.location.href = exportAPI.downloadExport(response.export_id);
      }
    } catch (err) {
      console.error('Export error:', err);
      alert('Failed to create export. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="results-page">
        <div className="loading">
          <p>Loading results...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="results-page">
        <div className="error">
          <strong>Error:</strong> {error}
        </div>
      </div>
    );
  }

  return (
    <div className="results-page">
      <div className="results-header card">
        <h2>Search Results</h2>
        <div className="search-id-info">
          <span className="label">Search ID:</span>
          <code className="search-id">{searchId}</code>
        </div>
      </div>

      <div className="results-tabs">
        <button
          className={`tab-button ${activeTab === 'results' ? 'active' : ''}`}
          onClick={() => setActiveTab('results')}
        >
          Results
        </button>
        <button
          className={`tab-button ${activeTab === 'graph' ? 'active' : ''}`}
          onClick={() => setActiveTab('graph')}
        >
          Graph
        </button>
        <button
          className={`tab-button ${activeTab === 'export' ? 'active' : ''}`}
          onClick={() => setActiveTab('export')}
        >
          Export
        </button>
      </div>

      <div className="results-content">
        {activeTab === 'results' && <ResultsView results={results} />}
        {activeTab === 'graph' && <GraphVisualization graphData={graphData} />}
        {activeTab === 'export' && <ExportPanel searchId={searchId} onExport={handleExport} />}
      </div>
    </div>
  );
}

export default ResultsPage;
