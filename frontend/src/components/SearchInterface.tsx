import React, { useState, useCallback } from 'react';
import { FiSearch, FiFilter, FiClock, FiStar } from 'react-icons/fi';
import { useAppSelector } from '../hooks/useAppSelector';
import { useAppDispatch } from '../hooks/useAppDispatch';
import { setQuery, setFilters, setResults, setLoading, setError, addSavedSearch } from '../store/searchSlice';
import { setActiveView } from '../store/uiSlice';
import { osintApi } from '../api/osintApi';
import { useDebounce } from '../hooks/useDebounce';
import { SearchQuery } from '../types';
import clsx from 'clsx';

const SearchInterface: React.FC = () => {
  const dispatch = useAppDispatch();
  const { query, history, savedSearches, loading } = useAppSelector(state => state.search);
  const [searchInput, setSearchInput] = useState(query.query);
  const [searchType, setSearchType] = useState<SearchQuery['type']>('all');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  
  const debouncedSearch = useDebounce(searchInput, 300);

  const handleSearch = useCallback(async () => {
    if (!searchInput.trim()) return;

    const searchQuery: SearchQuery = {
      query: searchInput,
      type: searchType,
      filters: query.filters,
    };

    dispatch(setQuery(searchQuery));
    dispatch(setLoading(true));
    dispatch(setError(null));

    try {
      const results = await osintApi.search.execute(searchQuery);
      dispatch(setResults({ results: results.data, total: results.total }));
      dispatch(setActiveView('results'));
    } catch (error: any) {
      dispatch(setError(error.message));
    } finally {
      dispatch(setLoading(false));
    }
  }, [searchInput, searchType, query.filters, dispatch]);

  const handleInputChange = async (value: string) => {
    setSearchInput(value);
    if (value.length > 2) {
      const sugg = await osintApi.search.getSuggestions(value);
      setSuggestions(sugg);
      setShowSuggestions(true);
    } else {
      setShowSuggestions(false);
    }
  };

  const handleSaveSearch = () => {
    const searchQuery: SearchQuery = {
      query: searchInput,
      type: searchType,
      filters: query.filters,
    };
    dispatch(addSavedSearch(searchQuery));
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
          Open Source Intelligence Search
        </h2>
        <p className="text-lg text-gray-600 dark:text-gray-400">
          Search across multiple data sources to discover connections and insights
        </p>
      </div>

      {/* Main Search */}
      <div className="bg-white dark:bg-dark-800 rounded-lg shadow-lg p-6 mb-6">
        <div className="flex space-x-2 mb-4">
          <div className="flex-1 relative">
            <div className="absolute left-3 top-1/2 transform -translate-y-1/2">
              <FiSearch className="text-gray-400" size={20} />
            </div>
            <input
              type="text"
              value={searchInput}
              onChange={(e) => handleInputChange(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Enter username, email, phone, name, or domain..."
              className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-dark-600 rounded-lg bg-white dark:bg-dark-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
            
            {/* Suggestions Dropdown */}
            {showSuggestions && suggestions.length > 0 && (
              <div className="absolute z-10 w-full mt-1 bg-white dark:bg-dark-700 border border-gray-200 dark:border-dark-600 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                {suggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => {
                      setSearchInput(suggestion);
                      setShowSuggestions(false);
                    }}
                    className="w-full px-4 py-2 text-left hover:bg-gray-100 dark:hover:bg-dark-600 transition-colors"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            )}
          </div>
          
          <button
            onClick={handleSearch}
            disabled={loading || !searchInput.trim()}
            className={clsx(
              'px-6 py-3 rounded-lg font-medium transition-colors',
              loading || !searchInput.trim()
                ? 'bg-gray-300 dark:bg-dark-600 cursor-not-allowed'
                : 'bg-primary-600 hover:bg-primary-700 text-white'
            )}
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>

        {/* Search Type Selector */}
        <div className="flex flex-wrap gap-2 mb-4">
          {(['all', 'username', 'email', 'phone', 'name', 'domain'] as const).map((type) => (
            <button
              key={type}
              onClick={() => setSearchType(type)}
              className={clsx(
                'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                searchType === type
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 dark:bg-dark-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-dark-600'
              )}
            >
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </button>
          ))}
        </div>

        {/* Advanced Filters Toggle */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center space-x-2 text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300"
          >
            <FiFilter size={16} />
            <span>{showAdvanced ? 'Hide' : 'Show'} Advanced Filters</span>
          </button>
          
          <button
            onClick={handleSaveSearch}
            className="flex items-center space-x-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
          >
            <FiStar size={16} />
            <span>Save Search</span>
          </button>
        </div>

        {/* Advanced Filters Panel */}
        {showAdvanced && (
          <div className="mt-6 pt-6 border-t border-gray-200 dark:border-dark-600 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Confidence Threshold
              </label>
              <input
                type="range"
                min="0"
                max="100"
                defaultValue="50"
                className="w-full"
                onChange={(e) => dispatch(setFilters({ 
                  ...query.filters, 
                  confidenceThreshold: parseInt(e.target.value) / 100 
                }))}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Data Sources
              </label>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {['Twitter', 'LinkedIn', 'GitHub', 'Facebook', 'Instagram', 'Reddit'].map((source) => (
                  <label key={source} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      className="rounded text-primary-600 focus:ring-primary-500"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">{source}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Start Date
                </label>
                <input
                  type="date"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-lg bg-white dark:bg-dark-700 text-gray-900 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  End Date
                </label>
                <input
                  type="date"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-lg bg-white dark:bg-dark-700 text-gray-900 dark:text-white"
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Search History */}
      {history.length > 0 && (
        <div className="bg-white dark:bg-dark-800 rounded-lg shadow p-6 mb-6">
          <div className="flex items-center space-x-2 mb-4">
            <FiClock className="text-gray-600 dark:text-gray-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Recent Searches</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {history.slice(0, 10).map((item, index) => (
              <button
                key={index}
                onClick={() => setSearchInput(item)}
                className="px-3 py-1 bg-gray-100 dark:bg-dark-700 text-gray-700 dark:text-gray-300 rounded-full text-sm hover:bg-gray-200 dark:hover:bg-dark-600 transition-colors"
              >
                {item}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Saved Searches */}
      {savedSearches.length > 0 && (
        <div className="bg-white dark:bg-dark-800 rounded-lg shadow p-6">
          <div className="flex items-center space-x-2 mb-4">
            <FiStar className="text-yellow-500" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Saved Searches</h3>
          </div>
          <div className="space-y-2">
            {savedSearches.map((saved, index) => (
              <button
                key={index}
                onClick={() => {
                  setSearchInput(saved.query);
                  setSearchType(saved.type);
                  dispatch(setFilters(saved.filters));
                }}
                className="w-full text-left px-4 py-3 bg-gray-50 dark:bg-dark-700 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-600 transition-colors"
              >
                <div className="font-medium text-gray-900 dark:text-white">{saved.query}</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Type: {saved.type}</div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SearchInterface;
