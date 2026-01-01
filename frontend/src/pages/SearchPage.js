import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import SearchBar from '../components/SearchBar';
import { searchAPI } from '../services/api';
import './SearchPage.css';

function SearchPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async (searchData) => {
    setLoading(true);
    setError(null);

    try {
      const response = await searchAPI.initiateSearch(searchData);
      
      if (response.search_id) {
        navigate(`/results/${response.search_id}`);
      } else {
        setError('Search initiated but no search ID received');
      }
    } catch (err) {
      console.error('Search error:', err);
      setError(err.response?.data?.error || err.message || 'Search failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="search-page">
      <div className="search-page-header">
        <h2>OSINT Search</h2>
        <p>
          Enter any identifier to begin comprehensive intelligence gathering across 
          surface web platforms.
        </p>
      </div>

      {error && (
        <div className="error">
          <strong>Error:</strong> {error}
        </div>
      )}

      <SearchBar onSearch={handleSearch} loading={loading} />

      <div className="search-tips card">
        <h3>Search Tips</h3>
        <ul>
          <li>
            <strong>Email:</strong> Search by email address to find associated accounts, 
            profiles, and online presence
          </li>
          <li>
            <strong>Username:</strong> Discover where a username is used across platforms
          </li>
          <li>
            <strong>Phone:</strong> Find profiles and content associated with phone numbers
          </li>
          <li>
            <strong>Name:</strong> Search for individuals by name to find public records 
            and online mentions
          </li>
          <li>
            <strong>Domain:</strong> Investigate domain ownership and associated identities
          </li>
        </ul>

        <div className="privacy-notice">
          <p>
            <strong>Privacy Notice:</strong> This platform only collects publicly available 
            information. All data is sourced from public websites and APIs. Use responsibly 
            and in accordance with applicable laws.
          </p>
        </div>
      </div>
    </div>
  );
}

export default SearchPage;
