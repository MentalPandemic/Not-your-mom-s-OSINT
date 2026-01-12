import React, { useState, useMemo } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Timeline,
  DataSet,
  TimelineOptions,
} from 'vis-timeline/standalone';
import {
  CalendarIcon,
  ClockIcon,
  FunnelIcon,
  ArrowDownIcon,
  ArrowUpIcon,
  MagnifyingGlassIcon,
  EyeIcon,
  ShareIcon,
  DocumentArrowDownIcon,
  AdjustmentsHorizontalIcon,
  MapPinIcon,
  GlobeAltIcon,
  UserIcon,
  BuildingOfficeIcon,
  DevicePhoneMobileIcon,
  EnvelopeIcon,
} from '@heroicons/react/24/outline';
import { useAppDispatch, useAppSelector } from '@/store';
import {
  selectSearchResults,
  selectSelectedResult,
  setSelectedResult,
} from '@/store/slices/searchSlice';
import { setRightPanelOpen } from '@/store/slices/uiSlice';
import { TimelineEvent, EntityType } from '@/types';
import { formatDistanceToNow, format, parseISO } from 'date-fns';
import { debounce } from 'lodash';

interface TimelineViewProps {
  className?: string;
}

export const TimelineView: React.FC<TimelineViewProps> = ({ className = '' }) => {
  const dispatch = useAppDispatch();
  const searchResults = useAppSelector(selectSearchResults);
  const selectedResult = useAppSelector(selectSelectedResult);

  const [timeline, setTimeline] = useState<Timeline | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<TimelineEvent | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [eventFilters, setEventFilters] = useState({
    dateRange: {
      start: null as Date | null,
      end: null as Date | null,
    },
    eventTypes: [] as string[],
    sources: [] as string[],
    minConfidence: 0,
  });
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const containerRef = useRef<HTMLDivElement>(null);

  // Generate timeline events from search results
  const timelineEvents = useMemo((): TimelineEvent[] => {
    if (!searchResults?.results) return [];

    const events: TimelineEvent[] = [];

    searchResults.results.forEach((result) => {
      const entity = result.entity;

      // Add entity creation/update events
      events.push({
        id: `${entity.id}-created`,
        entityId: entity.id,
        type: 'entity_created',
        title: `${entity.type} discovered`,
        description: `New ${entity.type} found with confidence ${(entity.confidence * 100).toFixed(0)}%`,
        date: new Date(entity.createdAt),
        source: 'OSINT Dashboard',
        confidence: entity.confidence,
        metadata: {
          entityType: entity.type,
          confidence: entity.confidence,
          sources: entity.sources,
        },
      });

      // Add entity update event if updated
      if (entity.updatedAt !== entity.createdAt) {
        events.push({
          id: `${entity.id}-updated`,
          entityId: entity.id,
          type: 'entity_updated',
          title: `${entity.type} updated`,
          description: `Data updated for ${entity.type}`,
          date: new Date(entity.updatedAt),
          source: 'OSINT Dashboard',
          confidence: entity.confidence,
          metadata: {
            entityType: entity.type,
            confidence: entity.confidence,
          },
        });
      }

      // Add timeline events based on entity type
      switch (entity.type) {
        case EntityType.IDENTITY:
          // Simulate social media events
          events.push({
            id: `${entity.id}-social-1`,
            entityId: entity.id,
            type: 'social_activity',
            title: 'Social Media Activity',
            description: 'Recent social media posts detected',
            date: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000), // Random date in last 30 days
            source: 'Social Media',
            confidence: 0.8 + Math.random() * 0.2,
            metadata: {
              platform: 'Twitter',
              activity: 'posts',
            },
          });

          events.push({
            id: `${entity.id}-location-1`,
            entityId: entity.id,
            type: 'location_activity',
            title: 'Location Check-in',
            description: 'Geographic location detected',
            date: new Date(Date.now() - Math.random() * 60 * 24 * 60 * 60 * 1000), // Random date in last 60 days
            source: 'Location Services',
            confidence: 0.7 + Math.random() * 0.3,
            metadata: {
              location: 'New York, NY',
              coordinates: { lat: 40.7128, lng: -74.0060 },
            },
          });
          break;

        case EntityType.DOMAIN:
          events.push({
            id: `${entity.id}-registered`,
            entityId: entity.id,
            type: 'domain_registered',
            title: 'Domain Registered',
            description: 'Domain registration date',
            date: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000), // Random date in last year
            source: 'Domain Registry',
            confidence: 0.95,
            metadata: {
              registrar: 'Example Registrar',
            },
          });

          events.push({
            id: `${entity.id}-ssl`,
            entityId: entity.id,
            type: 'ssl_renewal',
            title: 'SSL Certificate Renewal',
            description: 'SSL certificate was renewed',
            date: new Date(Date.now() - Math.random() * 90 * 24 * 60 * 60 * 1000), // Random date in last 90 days
            source: 'SSL Monitoring',
            confidence: 0.9,
            metadata: {
              certificateAuthority: 'Let\'s Encrypt',
            },
          });
          break;

        case EntityType.EMAIL:
          events.push({
            id: `${entity.id}-breach`,
            entityId: entity.id,
            type: 'data_breach',
            title: 'Data Breach',
            description: 'Email appeared in known data breach',
            date: new Date(Date.now() - Math.random() * 180 * 24 * 60 * 60 * 1000), // Random date in last 6 months
            source: 'Breach Database',
            confidence: 0.85,
            metadata: {
              breachName: 'Example Breach 2023',
              dataTypes: ['email', 'password'],
            },
          });
          break;
      }
    });

    // Filter events based on search term and filters
    let filteredEvents = events.filter((event) => {
      // Search filter
      if (searchTerm && !event.title.toLowerCase().includes(searchTerm.toLowerCase()) &&
          !event.description.toLowerCase().includes(searchTerm.toLowerCase())) {
        return false;
      }

      // Date range filter
      if (eventFilters.dateRange.start && event.date < eventFilters.dateRange.start) {
        return false;
      }
      if (eventFilters.dateRange.end && event.date > eventFilters.dateRange.end) {
        return false;
      }

      // Event type filter
      if (eventFilters.eventTypes.length > 0 && !eventFilters.eventTypes.includes(event.type)) {
        return false;
      }

      // Source filter
      if (eventFilters.sources.length > 0 && !eventFilters.sources.includes(event.source)) {
        return false;
      }

      // Confidence filter
      if (event.confidence < eventFilters.minConfidence) {
        return false;
      }

      return true;
    });

    // Sort events
    filteredEvents.sort((a, b) => {
      const comparison = a.date.getTime() - b.date.getTime();
      return sortOrder === 'asc' ? comparison : -comparison;
    });

    return filteredEvents;
  }, [searchResults, searchTerm, eventFilters, sortOrder]);

  // Get unique event types and sources for filters
  const eventTypes = useMemo(() => {
    return [...new Set(timelineEvents.map(event => event.type))];
  }, [timelineEvents]);

  const sources = useMemo(() => {
    return [...new Set(timelineEvents.map(event => event.source))];
  }, [timelineEvents]);

  // Initialize timeline
  React.useEffect(() => {
    if (!containerRef.current) return;

    const items = new DataSet(
      timelineEvents.map(event => ({
        id: event.id,
        content: `
          <div class="timeline-event" data-event-id="${event.id}">
            <div class="flex items-center space-x-2">
              ${getEventIcon(event.type)}
              <span class="text-sm font-medium">${event.title}</span>
            </div>
            <div class="text-xs text-gray-500 mt-1">
              ${format(event.date, 'MMM dd, yyyy HH:mm')} • ${event.source}
            </div>
          </div>
        `,
        start: event.date,
        title: event.description,
        className: `timeline-event-${event.type} confidence-${Math.round(event.confidence * 100)}`,
        style: `border-left: 4px solid ${getEventColor(event.type)};`,
      }))
    );

    const options: TimelineOptions = {
      start: timelineEvents.length > 0 ? timelineEvents[0].date : new Date(),
      end: timelineEvents.length > 0 ? timelineEvents[timelineEvents.length - 1].date : new Date(),
      editable: false,
      selectable: true,
      multiselect: false,
      zoomable: true,
      moveable: true,
      stack: true,
      showMajorLabels: true,
      showCurrentTime: true,
      showWeekScale: false,
      orientation: 'both',
      type: 'box',
      minHeight: '400px',
      maxHeight: '600px',
      margin: {
        item: 10,
        axis: 20,
      },
      tooltip: {
        followMouse: true,
      },
      template: (item: any, data: any, element: HTMLElement) => {
        const event = timelineEvents.find(e => e.id === item.id);
        if (event) {
          element.innerHTML = `
            <div class="p-3 bg-white dark:bg-gray-800 rounded-lg shadow-lg border max-w-sm">
              <div class="flex items-center space-x-2 mb-2">
                ${getEventIcon(event.type)}
                <h3 class="font-medium text-gray-900 dark:text-gray-100">${event.title}</h3>
              </div>
              <p class="text-sm text-gray-600 dark:text-gray-400 mb-2">${event.description}</p>
              <div class="flex items-center justify-between text-xs text-gray-500">
                <span>${format(event.date, 'MMM dd, yyyy HH:mm')}</span>
                <span class="px-2 py-1 rounded-full bg-gray-100 dark:bg-gray-700">
                  ${Math.round(event.confidence * 100)}% confidence
                </span>
              </div>
              <div class="mt-2 text-xs text-gray-500">
                Source: ${event.source}
              </div>
            </div>
          `;
        }
        return element;
      },
    };

    const newTimeline = new Timeline(containerRef.current, items, options);

    // Event handlers
    newTimeline.on('select', (properties) => {
      if (properties.items.length > 0) {
        const selectedEvent = timelineEvents.find(event => event.id === properties.items[0]);
        if (selectedEvent) {
          setSelectedEvent(selectedEvent);
        }
      }
    });

    newTimeline.on('doubleClick', (properties) => {
      if (properties.item) {
        const event = timelineEvents.find(e => e.id === properties.item);
        if (event) {
          // Open event details in right panel
          dispatch(setRightPanelOpen(true));
        }
      }
    });

    setTimeline(newTimeline);

    return () => {
      newTimeline.destroy();
    };
  }, [timelineEvents, dispatch]);

  // Get event icon
  const getEventIcon = (eventType: string) => {
    const iconClass = "h-4 w-4";
    switch (eventType) {
      case 'social_activity':
        return `<svg class="${iconClass}" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clip-rule="evenodd"></path></svg>`;
      case 'location_activity':
        return `<svg class="${iconClass}" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd"></path></svg>`;
      case 'domain_registered':
      case 'ssl_renewal':
        return `<svg class="${iconClass}" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M4.083 9h1.946c.089-1.546.383-2.97.837-4.118A6.004 6.004 0 004.083 9zM10 2a8 8 0 100 16 8 8 0 000-16zm0 2c-.076 0-.232.032-.465.262-.238.234-.497.623-.737 1.182-.389.907-.673 2.142-.766 3.556h3.936c-.093-1.414-.377-2.649-.766-3.556-.24-.56-.5-.948-.737-1.182C10.232 4.032 10.076 4 10 4zm3.971 5c-.089-1.546-.383-2.97-.837-4.118A6.004 6.004 0 0115.917 9h-1.946zm-2.003 2H8.032c.093 1.414.377 2.649.766 3.556.24.56.5.948.737 1.182.233.23.389.262.465.262.076 0 .232-.032.465-.262.238-.234.498-.623.737-1.182.389-.907.673-2.142.766-3.556zm1.166 4.118c.454-1.147.748-2.572.837-4.118h1.946a6.004 6.004 0 01-2.783 4.118zm-6.268 0C6.412 13.97 6.118 12.546 6.03 11H4.083a6.004 6.004 0 002.783 4.118z" clip-rule="evenodd"></path></svg>`;
      case 'data_breach':
        return `<svg class="${iconClass}" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 8a6 6 0 01-7.743 5.743L10 14l-1 1-1 1H6v2H2v-4l4.257-4.257A6 6 0 1118 8zm-6-4a1 1 0 100 2 2 2 0 012 2 1 1 0 102 0 4 4 0 00-4-4z" clip-rule="evenodd"></path></svg>`;
      case 'entity_created':
        return `<svg class="${iconClass}" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd"></path></svg>`;
      case 'entity_updated':
        return `<svg class="${iconClass}" fill="currentColor" viewBox="0 0 20 20"><path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"></path></svg>`;
      default:
        return `<svg class="${iconClass}" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"></path></svg>`;
    }
  };

  // Get event color
  const getEventColor = (eventType: string) => {
    const colorMap: Record<string, string> = {
      social_activity: '#EC4899',
      location_activity: '#10B981',
      domain_registered: '#F59E0B',
      ssl_renewal: '#3B82F6',
      data_breach: '#EF4444',
      entity_created: '#8B5CF6',
      entity_updated: '#06B6D4',
    };
    return colorMap[eventType] || '#6B7280';
  };

  // Handle filter changes
  const updateEventFilters = (updates: Partial<typeof eventFilters>) => {
    setEventFilters(prev => ({ ...prev, ...updates }));
  };

  const handleExportTimeline = () => {
    // Export timeline as image or data
    if (timeline) {
      const canvas = containerRef.current?.querySelector('canvas');
      if (canvas) {
        const link = document.createElement('a');
        link.download = 'timeline.png';
        link.href = canvas.toDataURL();
        link.click();
      }
    }
  };

  if (!searchResults) {
    return (
      <div className={`flex items-center justify-center h-full ${className}`}>
        <div className="text-center">
          <CalendarIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-gray-100">No timeline data</h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Search for entities to view their timeline of activities
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={`h-full flex flex-col ${className}`}>
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Timeline Analysis
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {timelineEvents.length} events • {sources.length} sources
            </p>
          </div>

          <div className="flex items-center space-x-2">
            {/* Search */}
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search events..."
                className="pl-10 pr-4 py-2 w-64 text-sm border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
              />
            </div>

            {/* Sort order */}
            <button
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              className="flex items-center space-x-1 px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
            >
              {sortOrder === 'asc' ? <ArrowUpIcon className="h-4 w-4" /> : <ArrowDownIcon className="h-4 w-4" />}
              <span>{sortOrder === 'asc' ? 'Oldest First' : 'Newest First'}</span>
            </button>

            {/* Filters */}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center space-x-1 px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
            >
              <FunnelIcon className="h-4 w-4" />
              <span>Filters</span>
            </button>

            {/* Export */}
            <button
              onClick={handleExportTimeline}
              className="flex items-center space-x-1 px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
            >
              <DocumentArrowDownIcon className="h-4 w-4" />
              <span>Export</span>
            </button>
          </div>
        </div>

        {/* Filters panel */}
        <AnimatePresence>
          {showFilters && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-4 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg"
            >
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Date range */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Date Range
                  </label>
                  <div className="space-y-2">
                    <input
                      type="date"
                      value={eventFilters.dateRange.start?.toISOString().split('T')[0] || ''}
                      onChange={(e) => updateEventFilters({
                        dateRange: {
                          ...eventFilters.dateRange,
                          start: e.target.value ? new Date(e.target.value) : null,
                        },
                      })}
                      className="w-full text-sm border border-gray-300 dark:border-gray-600 rounded px-2 py-1 dark:bg-gray-700 dark:text-white"
                    />
                    <input
                      type="date"
                      value={eventFilters.dateRange.end?.toISOString().split('T')[0] || ''}
                      onChange={(e) => updateEventFilters({
                        dateRange: {
                          ...eventFilters.dateRange,
                          end: e.target.value ? new Date(e.target.value) : null,
                        },
                      })}
                      className="w-full text-sm border border-gray-300 dark:border-gray-600 rounded px-2 py-1 dark:bg-gray-700 dark:text-white"
                    />
                  </div>
                </div>

                {/* Event types */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Event Types
                  </label>
                  <div className="space-y-1 max-h-32 overflow-y-auto">
                    {eventTypes.map((type) => (
                      <label key={type} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={eventFilters.eventTypes.includes(type)}
                          onChange={(e) => {
                            const newTypes = e.target.checked
                              ? [...eventFilters.eventTypes, type]
                              : eventFilters.eventTypes.filter(t => t !== type);
                            updateEventFilters({ eventTypes: newTypes });
                          }}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="ml-2 text-sm text-gray-600 dark:text-gray-400 capitalize">
                          {type.replace('_', ' ')}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Sources */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Sources
                  </label>
                  <div className="space-y-1 max-h-32 overflow-y-auto">
                    {sources.map((source) => (
                      <label key={source} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={eventFilters.sources.includes(source)}
                          onChange={(e) => {
                            const newSources = e.target.checked
                              ? [...eventFilters.sources, source]
                              : eventFilters.sources.filter(s => s !== source);
                            updateEventFilters({ sources: newSources });
                          }}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">
                          {source}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Confidence threshold */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Min Confidence: {Math.round(eventFilters.minConfidence * 100)}%
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={eventFilters.minConfidence}
                    onChange={(e) => updateEventFilters({ minConfidence: parseFloat(e.target.value) })}
                    className="w-full"
                  />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Timeline */}
      <div className="flex-1 overflow-hidden">
        <div 
          ref={containerRef} 
          className="w-full h-full bg-white dark:bg-gray-800"
        />
      </div>

      {/* Selected event details */}
      <AnimatePresence>
        {selectedEvent && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 p-4"
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-3">
                <div className="p-2 rounded-lg" style={{ backgroundColor: getEventColor(selectedEvent.type) + '20' }}>
                  <div dangerouslySetInnerHTML={{ __html: getEventIcon(selectedEvent.type) }} />
                </div>
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-100">
                    {selectedEvent.title}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    {selectedEvent.description}
                  </p>
                  <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                    <span className="flex items-center space-x-1">
                      <ClockIcon className="h-3 w-3" />
                      <span>{format(selectedEvent.date, 'MMM dd, yyyy HH:mm')}</span>
                    </span>
                    <span>Source: {selectedEvent.source}</span>
                    <span>Confidence: {Math.round(selectedEvent.confidence * 100)}%</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setSelectedEvent(null)}
                  className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  ×
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default TimelineView;