import React, { useState, useMemo } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MagnifyingGlassIcon,
  AdjustmentsHorizontalIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  FunnelIcon,
  EyeIcon,
  BookmarkIcon,
  ShareIcon,
  DocumentArrowDownIcon,
  ChartBarIcon,
  UserIcon,
  GlobeAltIcon,
  BuildingOfficeIcon,
  CalendarIcon,
  MapPinIcon,
  LinkIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';
import { useAppDispatch, useAppSelector } from '@/store';
import {
  selectSearchResults,
  selectSelectedResult,
  selectFilters,
  selectSortBy,
  selectSortOrder,
  selectResultsPerPage,
  selectCurrentPage,
  setSelectedResult,
  setCurrentPage,
  setSortBy,
  setSortOrder,
  setResultsPerPage,
} from '@/store/slices/searchSlice';
import { selectRightPanelOpen, setRightPanelOpen } from '@/store/slices/uiSlice';
import { EntitySearchResult, EntityType, RelationshipType } from '@/types';
import { formatDistanceToNow } from 'date-fns';

interface ResultsViewProps {
  className?: string;
}

export const ResultsView: React.FC<ResultsViewProps> = ({ className = '' }) => {
  const dispatch = useAppDispatch();
  const searchResults = useAppSelector(selectSearchResults);
  const selectedResult = useAppSelector(selectSelectedResult);
  const filters = useAppSelector(selectFilters);
  const sortBy = useAppSelector(selectSortBy);
  const sortOrder = useAppSelector(selectSortOrder);
  const resultsPerPage = useAppSelector(selectResultsPerPage);
  const currentPage = useAppSelector(selectCurrentPage);
  const rightPanelOpen = useAppSelector(selectRightPanelOpen);

  const [activeTab, setActiveTab] = useState<'all' | 'identities' | 'profiles' | 'domains' | 'timeline'>('all');
  const [showFilters, setShowFilters] = useState(false);
  const [hoveredResult, setHoveredResult] = useState<string | null>(null);

  // Filter and sort results
  const filteredAndSortedResults = useMemo(() => {
    if (!searchResults?.results) return [];

    let filtered = searchResults.results.filter(result => {
      // Apply confidence threshold
      if (result.entity.confidence < filters.confidenceThreshold) {
        return false;
      }

      // Apply tab filter
      if (activeTab !== 'all') {
        switch (activeTab) {
          case 'identities':
            return result.entity.type === EntityType.IDENTITY || result.entity.type === EntityType.SOCIAL;
          case 'profiles':
            return result.entity.type === EntityType.IDENTITY;
          case 'domains':
            return result.entity.type === EntityType.DOMAIN;
          case 'timeline':
            return result.entity.type === EntityType.IDENTITY; // Assuming timeline data is linked to identities
          default:
            return true;
        }
      }

      return true;
    });

    // Sort results
    filtered.sort((a, b) => {
      let comparison = 0;
      
      switch (sortBy) {
        case 'relevance':
          comparison = b.relevanceScore - a.relevanceScore;
          break;
        case 'confidence':
          comparison = b.entity.confidence - a.entity.confidence;
          break;
        case 'date':
          comparison = new Date(b.entity.updatedAt).getTime() - new Date(a.entity.updatedAt).getTime();
          break;
        case 'name':
          comparison = a.preview.localeCompare(b.preview);
          break;
        default:
          comparison = 0;
      }

      return sortOrder === 'asc' ? -comparison : comparison;
    });

    return filtered;
  }, [searchResults, filters, sortBy, sortOrder, activeTab]);

  // Paginate results
  const paginatedResults = useMemo(() => {
    const startIndex = (currentPage - 1) * resultsPerPage;
    return filteredAndSortedResults.slice(startIndex, startIndex + resultsPerPage);
  }, [filteredAndSortedResults, currentPage, resultsPerPage]);

  const totalPages = Math.ceil(filteredAndSortedResults.length / resultsPerPage);

  // Get entity type icon
  const getEntityIcon = (type: EntityType) => {
    switch (type) {
      case EntityType.IDENTITY:
      case EntityType.SOCIAL:
        return UserIcon;
      case EntityType.EMAIL:
        return '📧';
      case EntityType.PHONE:
        return '📱';
      case EntityType.DOMAIN:
        return GlobeAltIcon;
      case EntityType.ORGANIZATION:
        return BuildingOfficeIcon;
      case EntityType.ADDRESS:
        return MapPinIcon;
      default:
        return MagnifyingGlassIcon;
    }
  };

  // Get entity type color
  const getEntityColor = (type: EntityType) => {
    switch (type) {
      case EntityType.IDENTITY:
        return 'text-blue-600 bg-blue-50';
      case EntityType.EMAIL:
        return 'text-purple-600 bg-purple-50';
      case EntityType.PHONE:
        return 'text-cyan-600 bg-cyan-50';
      case EntityType.DOMAIN:
        return 'text-amber-600 bg-amber-50';
      case EntityType.ORGANIZATION:
        return 'text-red-600 bg-red-50';
      case EntityType.ADDRESS:
        return 'text-green-600 bg-green-50';
      case EntityType.SOCIAL:
        return 'text-pink-600 bg-pink-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  // Render confidence score
  const renderConfidenceScore = (confidence: number) => {
    const percentage = Math.round(confidence * 100);
    let colorClass = '';
    
    if (confidence >= 0.8) {
      colorClass = 'text-green-600 bg-green-100';
    } else if (confidence >= 0.6) {
      colorClass = 'text-yellow-600 bg-yellow-100';
    } else {
      colorClass = 'text-red-600 bg-red-100';
    }

    return (
      <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${colorClass}`}>
        <CheckCircleIcon className="h-3 w-3 mr-1" />
        {percentage}%
      </div>
    );
  };

  // Handle result selection
  const handleResultSelect = (result: EntitySearchResult) => {
    dispatch(setSelectedResult(result));
    if (!rightPanelOpen) {
      dispatch(setRightPanelOpen(true));
    }
  };

  // Handle sort change
  const handleSortChange = (newSortBy: typeof sortBy) => {
    if (sortBy === newSortBy) {
      dispatch(setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc'));
    } else {
      dispatch(setSortBy(newSortBy));
      dispatch(setSortOrder('desc'));
    }
  };

  if (!searchResults) {
    return (
      <div className={`flex items-center justify-center h-full ${className}`}>
        <div className="text-center">
          <MagnifyingGlassIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-gray-100">No search results</h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Start by searching for a name, email, domain, or other identifier
          </p>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'all', label: 'All Results', count: filteredAndSortedResults.length },
    { id: 'identities', label: 'Identities', count: filteredAndSortedResults.filter(r => r.entity.type === EntityType.IDENTITY || r.entity.type === EntityType.SOCIAL).length },
    { id: 'profiles', label: 'Profiles', count: filteredAndSortedResults.filter(r => r.entity.type === EntityType.IDENTITY).length },
    { id: 'domains', label: 'Domains', count: filteredAndSortedResults.filter(r => r.entity.type === EntityType.DOMAIN).length },
    { id: 'timeline', label: 'Timeline', count: filteredAndSortedResults.filter(r => r.entity.type === EntityType.IDENTITY).length },
  ];

  return (
    <div className={`h-full flex flex-col ${className}`}>
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Search Results
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {filteredAndSortedResults.length} of {searchResults.results.length} results
              {searchResults.executionTime && ` • ${searchResults.executionTime}ms`}
            </p>
          </div>

          <div className="flex items-center space-x-2">
            {/* Sort controls */}
            <div className="flex items-center space-x-1">
              <span className="text-sm text-gray-500 dark:text-gray-400">Sort by:</span>
              {(['relevance', 'confidence', 'date', 'name'] as const).map((sortType) => (
                <button
                  key={sortType}
                  onClick={() => handleSortChange(sortType)}
                  className={`flex items-center px-2 py-1 text-sm rounded ${
                    sortBy === sortType
                      ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <span className="capitalize">{sortType}</span>
                  {sortBy === sortType && (
                    sortOrder === 'asc' ? <ArrowUpIcon className="h-3 w-3 ml-1" /> : <ArrowDownIcon className="h-3 w-3 ml-1" />
                  )}
                </button>
              ))}
            </div>

            {/* Results per page */}
            <select
              value={resultsPerPage}
              onChange={(e) => dispatch(setResultsPerPage(Number(e.target.value)))}
              className="text-sm border border-gray-300 dark:border-gray-600 rounded px-2 py-1 dark:bg-gray-700 dark:text-gray-100"
            >
              <option value={25}>25 per page</option>
              <option value={50}>50 per page</option>
              <option value={100}>100 per page</option>
            </select>

            {/* Filter toggle */}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center px-3 py-1 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
            >
              <FunnelIcon className="h-4 w-4 mr-1" />
              Filters
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="mt-4 border-b border-gray-200 dark:border-gray-700">
          <nav className="flex space-x-8 overflow-x-auto">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as typeof activeTab)}
                className={`py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                {tab.label}
                {tab.count > 0 && (
                  <span className="ml-2 py-0.5 px-2 rounded-full text-xs bg-gray-100 dark:bg-gray-700">
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Results list */}
      <div className="flex-1 overflow-y-auto">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="divide-y divide-gray-200 dark:divide-gray-700"
          >
            {paginatedResults.map((result, index) => {
              const Icon = getEntityIcon(result.entity.type);
              const isSelected = selectedResult?.entity.id === result.entity.id;
              const isHovered = hoveredResult === result.entity.id;

              return (
                <motion.div
                  key={result.entity.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  onMouseEnter={() => setHoveredResult(result.entity.id)}
                  onMouseLeave={() => setHoveredResult(null)}
                  className={`p-6 hover:bg-gray-50 dark:hover:bg-gray-800/50 cursor-pointer transition-colors ${
                    isSelected ? 'bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500' : ''
                  }`}
                  onClick={() => handleResultSelect(result)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-4 flex-1">
                      {/* Entity icon */}
                      <div className={`p-2 rounded-lg ${getEntityColor(result.entity.type)}`}>
                        {typeof Icon === 'string' ? (
                          <span className="text-lg">{Icon}</span>
                        ) : (
                          <Icon className="h-5 w-5" />
                        )}
                      </div>

                      {/* Entity details */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2 mb-1">
                          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 truncate">
                            {result.preview}
                          </h3>
                          {renderConfidenceScore(result.entity.confidence)}
                        </div>

                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                          {result.matchReasons.join(', ')}
                        </p>

                        {/* Entity metadata */}
                        <div className="flex items-center space-x-4 text-sm text-gray-500 dark:text-gray-400">
                          <span className="capitalize">{result.entity.type}</span>
                          <span>•</span>
                          <span>Updated {formatDistanceToNow(new Date(result.entity.updatedAt), { addSuffix: true })}</span>
                          {result.entity.sources.length > 0 && (
                            <>
                              <span>•</span>
                              <span>{result.entity.sources.length} source{result.entity.sources.length !== 1 ? 's' : ''}</span>
                            </>
                          )}
                        </div>

                        {/* Match reasons highlights */}
                        {result.matchReasons.length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-1">
                            {result.matchReasons.slice(0, 3).map((reason, idx) => (
                              <span
                                key={idx}
                                className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                              >
                                {reason}
                              </span>
                            ))}
                            {result.matchReasons.length > 3 && (
                              <span className="text-xs text-gray-500 dark:text-gray-400">
                                +{result.matchReasons.length - 3} more
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center space-x-2 ml-4">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          // Add to workspace functionality
                        }}
                        className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                        title="Add to workspace"
                      >
                        <BookmarkIcon className="h-4 w-4" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          // Share functionality
                        }}
                        className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                        title="Share result"
                      >
                        <ShareIcon className="h-4 w-4" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          // View details functionality
                        }}
                        className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                        title="View details"
                      >
                        <EyeIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </div>

                  {/* Expanded preview on hover/selection */}
                  <AnimatePresence>
                    {(isHovered || isSelected) && result.relatedEntities && result.relatedEntities.length > 0 && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700"
                      >
                        <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
                          <LinkIcon className="h-4 w-4" />
                          <span>Related entities:</span>
                          <span className="font-medium">{result.relatedEntities.length} connected</span>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              );
            })}
          </motion.div>
        </AnimatePresence>

        {/* Empty state */}
        {filteredAndSortedResults.length === 0 && (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <MagnifyingGlassIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-gray-100">No results found</h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Try adjusting your filters or search terms
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-700 dark:text-gray-300">
              Showing {(currentPage - 1) * resultsPerPage + 1} to{' '}
              {Math.min(currentPage * resultsPerPage, filteredAndSortedResults.length)} of{' '}
              {filteredAndSortedResults.length} results
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => dispatch(setCurrentPage(Math.max(1, currentPage - 1)))}
                disabled={currentPage === 1}
                className="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <span className="px-3 py-1 text-sm bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded">
                {currentPage} of {totalPages}
              </span>
              <button
                onClick={() => dispatch(setCurrentPage(Math.min(totalPages, currentPage + 1)))}
                disabled={currentPage === totalPages}
                className="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ResultsView;