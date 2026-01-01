import React from 'react';
import './ResultsView.css';

function ResultsView({ results }) {
  if (!results) {
    return (
      <div className="results-view card">
        <p>No results to display</p>
      </div>
    );
  }

  const { identities, attributes, relationships, content } = results;

  return (
    <div className="results-view">
      <div className="results-summary card">
        <h2>Search Results Summary</h2>
        <div className="summary-stats">
          <div className="stat-item">
            <span className="stat-value">{identities?.length || 0}</span>
            <span className="stat-label">Identities</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{attributes?.length || 0}</span>
            <span className="stat-label">Attributes</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{relationships?.length || 0}</span>
            <span className="stat-label">Relationships</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{content?.length || 0}</span>
            <span className="stat-label">Content Items</span>
          </div>
        </div>
      </div>

      {identities && identities.length > 0 && (
        <div className="identities-section card">
          <h3>Discovered Identities</h3>
          <div className="identities-list">
            {identities.map((identity) => (
              <div key={identity.id} className="identity-item">
                <div className="identity-header">
                  <span className="identity-name">{identity.name}</span>
                  <span className="identity-type">{identity.type}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {content && content.length > 0 && (
        <div className="content-section card">
          <h3>Discovered Content</h3>
          <div className="content-list">
            {content.map((item) => (
              <div key={item.id} className="content-item">
                <div className="content-header">
                  <span className="content-type">{item.content_type}</span>
                  <span className="content-source">{item.source}</span>
                </div>
                {item.text && (
                  <p className="content-text">{item.text.substring(0, 200)}...</p>
                )}
                {item.url && (
                  <a href={item.url} target="_blank" rel="noopener noreferrer" className="content-link">
                    View Source
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {relationships && relationships.length > 0 && (
        <div className="relationships-section card">
          <h3>Discovered Relationships</h3>
          <div className="relationships-list">
            {relationships.map((rel) => (
              <div key={rel.id} className="relationship-item">
                <span className="relationship-type">{rel.relationship_type}</span>
                <span className="relationship-strength">Strength: {rel.strength}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default ResultsView;
