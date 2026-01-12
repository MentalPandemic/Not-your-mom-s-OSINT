import React, { useState, useRef, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { 
  MagnifyingGlassIcon, 
  AdjustmentsHorizontalIcon,
  ClockIcon,
  BookmarkIcon,
  XMarkIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppDispatch, useAppSelector } from '@/store';
import {
  selectCurrentQuery,
  selectIsSearching,
  selectSearchResults,
  selectSuggestions,
  selectRecentQueries,
  selectSavedSearches,
  selectFilters,
  setCurrentQuery,
  setIsSearching,
  setSearchResults,
  setSearchError,
  addToSavedSearches,
  updateFilters,
  setSuggestions,
  generateSuggestions,
} from '@/store/slices/searchSlice';
import { SearchQuery, SearchFilters, QueryType } from '@/types';
import { searchAPI } from '@/api/search';
import { debounce } from 'lodash';

interface SearchInterfaceProps {
  compact?: boolean;
  className?: string;
}

export const SearchInterface: React.FC<SearchInterfaceProps> = ({ 
  compact = false, 
  className = '' 
}) => {
  const dispatch = useAppDispatch();
  const currentQuery = useAppSelector(selectCurrentQuery);
  const isSearching = useAppSelector(selectIsSearching);
  const searchResults = useAppSelector(selectSearchResults);
  const suggestions = useAppSelector(selectSuggestions);
  const recentQueries = useAppSelector(selectRecentQueries);
  const savedSearches = useAppSelector(selectSavedSearches);
  const filters = useAppSelector(selectFilters);

  const [query, setQuery] = useState('');
  const [queryType, setQueryType] = useState<QueryType>(QueryType.NAME);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [inputFocused, setInputFocused] = useState(false);

  const inputRef = useRef<HTMLInputElement>(null);
  const searchRef = useRef<HTMLDivElement>(null);

  // Debounced suggestion generation
  const debouncedSuggestions = React.useCallback(
    debounce((searchTerm: string) => {
      if (searchTerm.trim()) {
        dispatch(generateSuggestions(searchTerm));
      } else {
        dispatch(setSuggestions([]));
      }
    }, 300),
    [dispatch]
  );

  // Handle input change
  const handleInputChange = (value: string) => {
    setQuery(value);
    if (value.trim()) {
      debouncedSuggestions(value);
      setShowSuggestions(true);
      setShowHistory(false);
    } else {
      setShowSuggestions(false);
      setShowHistory(inputFocused);
    }
  };

  // Perform search
  const performSearch = async (searchQuery: string, searchType: QueryType, searchFilters?: Partial<SearchFilters>) => {
    if (!searchQuery.trim()) return;

    dispatch(setIsSearching(true));

    try {
      const searchRequest: SearchQuery = {
        id: `search-${Date.now()}`,
        query: searchQuery,
        queryType: searchType,
        filters: { ...filters, ...searchFilters },
        createdAt: new Date(),
        isSaved: false,
      };

      dispatch(setCurrentQuery(searchRequest));

      const response = await searchAPI.search({
        query: searchQuery,
        queryType: searchType,
        filters: searchRequest.filters,
      });

      const searchResults = {
        query: searchRequest,
        results: response.results,
        totalCount: response.total,
        executionTime: response.executionTime,
        timestamp: new Date(),
        sources: response.sources,
      };

      dispatch(setSearchResults(searchResults));
      setShowSuggestions(false);
      setShowHistory(false);

    } catch (error) {
      dispatch(setSearchError(error instanceof Error ? error.message : 'Search failed'));
    } finally {
      dispatch(setIsSearching(false));
    }
  };

  // Handle search submission
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      performSearch(query, queryType);
    }
  };

  // Handle suggestion selection
  const handleSuggestionSelect = (suggestion: string) => {
    setQuery(suggestion);
    setShowSuggestions(false);
    performSearch(suggestion, queryType);
  };

  // Handle query type detection
  const detectQueryType = (input: string): QueryType => {
    if (input.includes('@') && input.includes('.')) return QueryType.EMAIL;
    if (/^\+?[\d\s\-\(\)]+$/.test(input)) return QueryType.PHONE;
    if (input.startsWith('@')) return QueryType.USERNAME;
    if (input.includes('.') && !input.includes(' ')) return QueryType.DOMAIN;
    if (input.includes(',') || input.split(' ').length > 1) return QueryType.NAME;
    return QueryType.NAME;
  };

  // Update query type when input changes
  useEffect(() => {
    const detectedType = detectQueryType(query);
    if (detectedType !== queryType) {
      setQueryType(detectedType);
    }
  }, [query, queryType]);

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
        setShowHistory(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const queryTypes = [
    { value: QueryType.NAME, label: 'Name', icon: '👤' },
    { value: QueryType.EMAIL, label: 'Email', icon: '📧' },
    { value: QueryType.PHONE, label: 'Phone', icon: '📱' },
    { value: QueryType.USERNAME, label: 'Username', icon: '@' },
    { value: QueryType.DOMAIN, label: 'Domain', icon: '🌐' },
    { value: QueryType.ADDRESS, label: 'Address', icon: '📍' },
  ];

  if (compact) {
    return (
      <div className={`relative ${className}`} ref={searchRef}>
        <form onSubmit={handleSearch} className="relative">
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => handleInputChange(e.target.value)}
              onFocus={() => {
                setInputFocused(true);
                setShowHistory(recentQueries.length > 0);
              }}
              onBlur={() => setInputFocused(false)}
              placeholder="Search names, emails, domains..."
              className="w-full pl-10 pr-12 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
            {isSearching && (
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
              </div>
            )}
          </div>
        </form>

        {/* Compact suggestions dropdown */}
        <AnimatePresence>
          {showSuggestions && suggestions.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-50 max-h-60 overflow-y-auto"
            >
              {suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestionSelect(suggestion)}
                  className="w-full px-4 py-2 text-left hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center space-x-2"
                >
                  <SparklesIcon className="h-4 w-4 text-gray-400" />
                  <span className="text-sm">{suggestion}</span>
                </button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`} ref={searchRef}>
      {/* Main search interface */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <form onSubmit={handleSearch} className="space-y-4">
          {/* Search input */}
          <div className="relative">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-6 w-6 text-gray-400" />
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => handleInputChange(e.target.value)}
                onFocus={() => {
                  setInputFocused(true);
                  setShowHistory(recentQueries.length > 0);
                }}
                onBlur={() => setInputFocused(false)}
                placeholder="Enter name, email, phone, domain, or username..."
                className="w-full pl-12 pr-4 py-4 text-lg border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:placeholder-gray-400"
              />
              {isSearching && (
                <div className="absolute right-4 top-1/2 transform -translate-y-1/2">
                  <div className="animate-spin h-6 w-6 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                </div>
              )}
            </div>

            {/* Query type selector */}
            <div className="mt-3 flex flex-wrap gap-2">
              {queryTypes.map((type) => (
                <button
                  key={type.value}
                  type="button"
                  onClick={() => setQueryType(type.value)}
                  className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                    queryType === type.value
                      ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                  }`}
                >
                  <span className="mr-1">{type.icon}</span>
                  {type.label}
                </button>
              ))}
            </div>
          </div>

          {/* Search actions */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex items-center space-x-2 px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
              >
                <AdjustmentsHorizontalIcon className="h-4 w-4" />
                <span>Advanced Search</span>
              </button>
              
              {recentQueries.length > 0 && (
                <button
                  type="button"
                  onClick={() => setShowHistory(!showHistory)}
                  className="flex items-center space-x-2 px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
                >
                  <ClockIcon className="h-4 w-4" />
                  <span>Recent ({recentQueries.length})</span>
                </button>
              )}
            </div>

            <button
              type="submit"
              disabled={!query.trim() || isSearching}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              {isSearching ? (
                <>
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                  <span>Searching...</span>
                </>
              ) : (
                <>
                  <MagnifyingGlassIcon className="h-4 w-4" />
                  <span>Search</span>
                </>
              )}
            </button>
          </div>
        </form>

        {/* Advanced search panel */}
        <AnimatePresence>
          {showAdvanced && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-6 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg"
            >
              <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-4">
                Advanced Search Filters
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* Data sources */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Data Sources
                  </label>
                  <div className="space-y-2">
                    {['Social Media', 'People Search', 'Domain', 'Public Records', 'GitHub'].map((source) => (
                      <label key={source} className="flex items-center">
                        <input type="checkbox" className="rounded border-gray-300" />
                        <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">{source}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Confidence threshold */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Min Confidence: {(filters.confidenceThreshold * 100).toFixed(0)}%
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={filters.confidenceThreshold}
                    onChange={(e) => dispatch(updateFilters({ confidenceThreshold: parseFloat(e.target.value) }))}
                    className="w-full"
                  />
                </div>

                {/* Include NSFW */}
                <div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={filters.includeNSFW}
                      onChange={(e) => dispatch(updateFilters({ includeNSFW: e.target.checked }))}
                      className="rounded border-gray-300"
                    />
                    <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">
                      Include NSFW content
                    </span>
                  </label>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Suggestions and history dropdown */}
      <AnimatePresence>
        {(showSuggestions || showHistory) && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg"
          >
            {showHistory && recentQueries.length > 0 && (
              <div className="p-4">
                <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">
                  Recent Searches
                </h4>
                <div className="space-y-2">
                  {recentQueries.slice(0, 10).map((recentQuery, index) => (
                    <button
                      key={index}
                      onClick={() => handleSuggestionSelect(recentQuery)}
                      className="w-full text-left px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 rounded flex items-center space-x-2"
                    >
                      <ClockIcon className="h-4 w-4" />
                      <span>{recentQuery}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {showSuggestions && suggestions.length > 0 && (
              <div className="p-4 border-t border-gray-200 dark:border-gray-700">
                <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">
                  Suggestions
                </h4>
                <div className="space-y-2">
                  {suggestions.map((suggestion, index) => (
                    <button
                      key={index}
                      onClick={() => handleSuggestionSelect(suggestion)}
                      className="w-full text-left px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 rounded flex items-center space-x-2"
                    >
                      <SparklesIcon className="h-4 w-4" />
                      <span>{suggestion}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {showHistory && savedSearches.length > 0 && (
              <div className="p-4 border-t border-gray-200 dark:border-gray-700">
                <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">
                  Saved Searches
                </h4>
                <div className="space-y-2">
                  {savedSearches.map((savedSearch) => (
                    <button
                      key={savedSearch.id}
                      onClick={() => handleSuggestionSelect(savedSearch.query)}
                      className="w-full text-left px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 rounded flex items-center space-x-2"
                    >
                      <BookmarkIcon className="h-4 w-4" />
                      <span>{savedSearch.query}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default SearchInterface;