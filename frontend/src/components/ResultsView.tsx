import React, { useState } from 'react';
import { FiUser, FiGlobe, FiClock, FiFilter, FiChevronLeft, FiChevronRight } from 'react-icons/fi';
import { useAppSelector } from '../hooks/useAppSelector';
import { useAppDispatch } from '../hooks/useAppDispatch';
import { setPage, setPageSize } from '../store/searchSlice';
import { setActiveTab } from '../store/uiSlice';
import { formatConfidence, formatRelativeTime, truncateText } from '../utils/formatters';
import { SearchResult } from '../types';
import clsx from 'clsx';

const ResultsView: React.FC = () => {
  const dispatch = useAppDispatch();
  const { results, total, page, pageSize, query, loading } = useAppSelector(state => state.search);
  const { activeTab } = useAppSelector(state => state.ui);
  const [sortBy, setSortBy] = useState<'relevance' | 'confidence' | 'date'>('relevance');

  const tabs = [
    { id: 'all', label: 'All Results', count: total },
    { id: 'identities', label: 'Identities', count: results.filter(r => r.type === 'identity').length },
    { id: 'profiles', label: 'Profiles', count: results.filter(r => r.type === 'profile').length },
    { id: 'domains', label: 'Domains', count: results.filter(r => r.type === 'domain').length },
  ];

  const filteredResults = activeTab === 'all' 
    ? results 
    : results.filter(r => r.type === activeTab.slice(0, -1) || (activeTab === 'identities' && r.type === 'identity'));

  const sortedResults = [...filteredResults].sort((a, b) => {
    switch (sortBy) {
      case 'confidence':
        return b.confidence - a.confidence;
      case 'date':
        return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
      default:
        return 0;
    }
  });

  const totalPages = Math.ceil(total / pageSize);

  const getSourceIcon = (source: string) => {
    switch (source.toLowerCase()) {
      case 'twitter':
      case 'linkedin':
      case 'facebook':
      case 'instagram':
        return <FiUser className="text-blue-500" />;
      case 'github':
        return <FiUser className="text-gray-700" />;
      default:
        return <FiGlobe className="text-gray-500" />;
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100 dark:bg-green-900';
    if (confidence >= 0.5) return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900';
    return 'text-red-600 bg-red-100 dark:bg-red-900';
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Search Results for "{query.query}"
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Found {total} result{total !== 1 ? 's' : ''} across multiple sources
        </p>
      </div>

      {/* Tabs */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex space-x-2 border-b border-gray-200 dark:border-dark-600">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => dispatch(setActiveTab(tab.id))}
              className={clsx(
                'px-4 py-2 font-medium transition-colors relative',
                activeTab === tab.id
                  ? 'text-primary-600 dark:text-primary-400'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              )}
            >
              {tab.label} ({tab.count})
              {activeTab === tab.id && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-600"></div>
              )}
            </button>
          ))}
        </div>

        {/* Sort Options */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <FiFilter className="text-gray-500" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-lg bg-white dark:bg-dark-700 text-gray-900 dark:text-white text-sm"
            >
              <option value="relevance">Sort by Relevance</option>
              <option value="confidence">Sort by Confidence</option>
              <option value="date">Sort by Date</option>
            </select>
          </div>

          <select
            value={pageSize}
            onChange={(e) => dispatch(setPageSize(parseInt(e.target.value)))}
            className="px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-lg bg-white dark:bg-dark-700 text-gray-900 dark:text-white text-sm"
          >
            <option value="10">10 per page</option>
            <option value="20">20 per page</option>
            <option value="50">50 per page</option>
            <option value="100">100 per page</option>
          </select>
        </div>
      </div>

      {/* Results Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      ) : sortedResults.length === 0 ? (
        <div className="text-center py-20">
          <p className="text-gray-600 dark:text-gray-400 text-lg">No results found</p>
        </div>
      ) : (
        <>
          <div className="space-y-4 mb-6">
            {sortedResults.map((result) => (
              <ResultCard key={result.id} result={result} />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, total)} of {total} results
              </p>
              
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => dispatch(setPage(page - 1))}
                  disabled={page === 1}
                  className={clsx(
                    'p-2 rounded-lg',
                    page === 1
                      ? 'text-gray-400 cursor-not-allowed'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-700'
                  )}
                >
                  <FiChevronLeft />
                </button>

                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  const pageNum = i + 1;
                  return (
                    <button
                      key={pageNum}
                      onClick={() => dispatch(setPage(pageNum))}
                      className={clsx(
                        'px-3 py-1 rounded-lg',
                        page === pageNum
                          ? 'bg-primary-600 text-white'
                          : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-700'
                      )}
                    >
                      {pageNum}
                    </button>
                  );
                })}

                <button
                  onClick={() => dispatch(setPage(page + 1))}
                  disabled={page === totalPages}
                  className={clsx(
                    'p-2 rounded-lg',
                    page === totalPages
                      ? 'text-gray-400 cursor-not-allowed'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-700'
                  )}
                >
                  <FiChevronRight />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

const ResultCard: React.FC<{ result: SearchResult }> = ({ result }) => {
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100 dark:bg-green-900 dark:text-green-400';
    if (confidence >= 0.5) return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900 dark:text-yellow-400';
    return 'text-red-600 bg-red-100 dark:bg-red-900 dark:text-red-400';
  };

  return (
    <div className="bg-white dark:bg-dark-800 rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center">
            <FiUser className="text-primary-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              {result.title}
            </h3>
            <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
              <span>{result.source.name}</span>
              <span>•</span>
              <span className="flex items-center">
                <FiClock className="mr-1" size={12} />
                {formatRelativeTime(result.timestamp)}
              </span>
            </div>
          </div>
        </div>

        <span className={clsx('px-3 py-1 rounded-full text-xs font-medium', getConfidenceColor(result.confidence))}>
          {formatConfidence(result.confidence)}
        </span>
      </div>

      <p className="text-gray-700 dark:text-gray-300 mb-4">
        {truncateText(result.description, 200)}
      </p>

      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-600 dark:text-gray-400 capitalize">
          Type: {result.type}
        </span>
        <button className="px-4 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
          View Details
        </button>
      </div>
    </div>
  );
};

export default ResultsView;
