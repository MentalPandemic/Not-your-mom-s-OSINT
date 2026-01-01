import React, { useState } from 'react';
import './SearchBar.css';

function SearchBar({ onSearch, loading }) {
  const [query, setQuery] = useState('');
  const [deepSearch, setDeepSearch] = useState(false);
  const [includeAdultSites, setIncludeAdultSites] = useState(true);
  const [includePersonals, setIncludePersonals] = useState(true);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch({
        query: query.trim(),
        deep_search: deepSearch,
        include_adult_sites: includeAdultSites,
        include_personals: includePersonals,
      });
    }
  };

  return (
    <div className="search-bar-container card">
      <h2>Search OSINT Data</h2>
      <form onSubmit={handleSubmit}>
        <div className="search-input-group">
          <input
            type="text"
            className="input search-input"
            placeholder="Enter email, username, phone number, name, or domain..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={loading}
          />
          <button type="submit" className="button search-button" disabled={loading}>
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>

        <div className="search-options">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={deepSearch}
              onChange={(e) => setDeepSearch(e.target.checked)}
              disabled={loading}
            />
            <span>Deep Search (slower, more comprehensive)</span>
          </label>

          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={includeAdultSites}
              onChange={(e) => setIncludeAdultSites(e.target.checked)}
              disabled={loading}
            />
            <span>Include Adult/NSFW Sites</span>
          </label>

          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={includePersonals}
              onChange={(e) => setIncludePersonals(e.target.checked)}
              disabled={loading}
            />
            <span>Include Personals/Classified Sites</span>
          </label>
        </div>

        <div className="search-info">
          <p>
            <strong>Phase 1 Data Sources:</strong> Social media platforms, public databases, 
            WHOIS/DNS, adult content sites (Pornhub, xHamster, Fetlife, OnlyFans, etc.), 
            personals/classified sites (Skipthegames, Bedpage, Craigslist, Doublelist, etc.), 
            and hundreds of other platforms.
          </p>
        </div>
      </form>
    </div>
  );
}

export default SearchBar;
