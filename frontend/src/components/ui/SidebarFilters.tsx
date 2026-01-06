import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  FunnelIcon,
  AdjustmentsHorizontalIcon,
  XMarkIcon,
  CheckIcon,
} from '@heroicons/react/24/outline';
import { useAppDispatch, useAppSelector } from '@/store';
import { updateFilters, resetFilters } from '@/store/slices/searchSlice';
import { EntityType, RelationshipType } from '@/types';

export const SidebarFilters: React.FC = () => {
  const dispatch = useAppDispatch();
  const filters = useAppSelector((state) => state.search.filters);
  const [isExpanded, setIsExpanded] = useState(true);

  const dataSources = [
    'Social Media',
    'People Search', 
    'Domain Records',
    'Public Records',
    'GitHub',
    'LinkedIn',
    'Twitter',
    'Facebook',
    'Instagram',
  ];

  const entityTypes = Object.values(EntityType);
  const relationshipTypes = Object.values(RelationshipType);

  const handleDataSourceToggle = (source: string) => {
    const currentSources = filters.dataSources || [];
    const updatedSources = currentSources.includes(source)
      ? currentSources.filter(s => s !== source)
      : [...currentSources, source];
    
    dispatch(updateFilters({ dataSources: updatedSources }));
  };

  const handleEntityTypeToggle = (type: EntityType) => {
    const currentTypes = filters.excludeTypes || [];
    const updatedTypes = currentTypes.includes(type)
      ? currentTypes.filter(t => t !== type)
      : [...currentTypes, type];
    
    dispatch(updateFilters({ excludeTypes: updatedTypes }));
  };

  const handleRelationshipTypeToggle = (type: RelationshipType) => {
    const currentTypes = filters.relationshipTypes || [];
    const updatedTypes = currentTypes.includes(type)
      ? currentTypes.filter(t => t !== type)
      : [...currentTypes, type];
    
    dispatch(updateFilters({ relationshipTypes: updatedTypes }));
  };

  const hasActiveFilters = () => {
    return (
      (filters.dataSources && filters.dataSources.length > 0) ||
      (filters.excludeTypes && filters.excludeTypes.length > 0) ||
      (filters.relationshipTypes && filters.relationshipTypes.length > 0) ||
      filters.confidenceThreshold > 0.7 ||
      !filters.includeNSFW
    );
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Filters
        </h3>
        <div className="flex items-center space-x-2">
          {hasActiveFilters() && (
            <button
              onClick={() => dispatch(resetFilters())}
              className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800"
            >
              Clear all
            </button>
          )}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 text-gray-400 hover:text-gray-600"
          >
            <AdjustmentsHorizontalIcon className="h-4 w-4" />
          </button>
        </div>
      </div>

      {isExpanded && (
        <>
          {/* Confidence Threshold */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Minimum Confidence: {Math.round(filters.confidenceThreshold * 100)}%
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={filters.confidenceThreshold}
              onChange={(e) => dispatch(updateFilters({ 
                confidenceThreshold: parseFloat(e.target.value) 
              }))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>0%</span>
              <span>50%</span>
              <span>100%</span>
            </div>
          </div>

          {/* Data Sources */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">
              Data Sources
            </h4>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {dataSources.map((source) => (
                <label key={source} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={filters.dataSources?.includes(source) || false}
                    onChange={() => handleDataSourceToggle(source)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                    {source}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Entity Types */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">
              Entity Types
            </h4>
            <div className="space-y-2">
              {entityTypes.map((type) => (
                <label key={type} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={!filters.excludeTypes?.includes(type)}
                    onChange={() => handleEntityTypeToggle(type)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700 dark:text-gray-300 capitalize">
                    {type.replace('_', ' ')}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Relationship Types */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">
              Relationship Types
            </h4>
            <div className="space-y-2 max-h-32 overflow-y-auto">
              {relationshipTypes.slice(0, 10).map((type) => (
                <label key={type} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={filters.relationshipTypes?.includes(type) || false}
                    onChange={() => handleRelationshipTypeToggle(type)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-xs text-gray-700 dark:text-gray-300">
                    {type.replace(/_/g, ' ')}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Content Filter */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">
              Content
            </h4>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={filters.includeNSFW}
                onChange={(e) => dispatch(updateFilters({ includeNSFW: e.target.checked }))}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                Include NSFW content
              </span>
            </label>
          </div>

          {/* Quick Actions */}
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
            <h4 className="text-sm font-medium text-blue-800 dark:text-blue-200 mb-3">
              Quick Filters
            </h4>
            <div className="space-y-2">
              <button
                onClick={() => dispatch(updateFilters({ confidenceThreshold: 0.9 }))}
                className="w-full text-left px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-blue-200 dark:border-blue-700 rounded hover:bg-blue-50 dark:hover:bg-blue-900/30"
              >
                High confidence only (90%+)
              </button>
              <button
                onClick={() => dispatch(updateFilters({ 
                  dataSources: ['Social Media', 'LinkedIn', 'Twitter'],
                  confidenceThreshold: 0.8
                }))}
                className="w-full text-left px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-blue-200 dark:border-blue-700 rounded hover:bg-blue-50 dark:hover:bg-blue-900/30"
              >
                Social media profiles
              </button>
              <button
                onClick={() => dispatch(updateFilters({ 
                  excludeTypes: [EntityType.EMAIL, EntityType.PHONE],
                  confidenceThreshold: 0.7
                }))}
                className="w-full text-left px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-blue-200 dark:border-blue-700 rounded hover:bg-blue-50 dark:hover:bg-blue-900/30"
              >
                Exclude contact info
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};