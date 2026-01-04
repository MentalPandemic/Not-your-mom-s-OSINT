import React, { useState, useEffect } from 'react';
import { FiCalendar, FiFilter, FiDownload } from 'react-icons/fi';
import { useAppSelector } from '../hooks/useAppSelector';
import { formatDate } from '../utils/formatters';
import { TimelineEvent } from '../types';
import clsx from 'clsx';

const TimelineView: React.FC = () => {
  const { selectedNode } = useAppSelector(state => state.graph);
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [filteredEvents, setFilteredEvents] = useState<TimelineEvent[]>([]);
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [dateRange, setDateRange] = useState({ start: '', end: '' });

  useEffect(() => {
    if (selectedNode) {
      const mockEvents: TimelineEvent[] = [
        {
          id: '1',
          timestamp: '2023-01-15T10:00:00Z',
          type: 'account_created',
          platform: 'Twitter',
          description: 'Account created on Twitter',
        },
        {
          id: '2',
          timestamp: '2023-03-22T14:30:00Z',
          type: 'post',
          platform: 'LinkedIn',
          description: 'Posted about new job position',
        },
        {
          id: '3',
          timestamp: '2023-06-10T09:15:00Z',
          type: 'profile_update',
          platform: 'GitHub',
          description: 'Updated GitHub profile',
        },
      ];
      setEvents(mockEvents);
      setFilteredEvents(mockEvents);
    }
  }, [selectedNode]);

  useEffect(() => {
    let filtered = events;
    
    if (selectedTypes.length > 0) {
      filtered = filtered.filter(e => selectedTypes.includes(e.type));
    }
    
    if (dateRange.start) {
      filtered = filtered.filter(e => new Date(e.timestamp) >= new Date(dateRange.start));
    }
    
    if (dateRange.end) {
      filtered = filtered.filter(e => new Date(e.timestamp) <= new Date(dateRange.end));
    }
    
    setFilteredEvents(filtered);
  }, [selectedTypes, dateRange, events]);

  const eventTypes = Array.from(new Set(events.map(e => e.type)));

  const getEventColor = (type: string) => {
    switch (type) {
      case 'account_created':
        return 'bg-green-500';
      case 'post':
        return 'bg-blue-500';
      case 'profile_update':
        return 'bg-yellow-500';
      case 'activity':
        return 'bg-purple-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Activity Timeline
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Chronological view of all activities and events
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-dark-800 rounded-lg shadow p-4 mb-6">
        <div className="flex items-center space-x-4 mb-4">
          <FiFilter className="text-gray-600 dark:text-gray-400" />
          <h3 className="font-semibold text-gray-900 dark:text-white">Filters</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Event Types
            </label>
            <div className="space-y-2">
              {eventTypes.map((type) => (
                <label key={type} className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={selectedTypes.includes(type)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedTypes([...selectedTypes, type]);
                      } else {
                        setSelectedTypes(selectedTypes.filter(t => t !== type));
                      }
                    }}
                    className="rounded text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300 capitalize">
                    {type.replace('_', ' ')}
                  </span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Start Date
            </label>
            <input
              type="date"
              value={dateRange.start}
              onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-lg bg-white dark:bg-dark-700 text-gray-900 dark:text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              End Date
            </label>
            <input
              type="date"
              value={dateRange.end}
              onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-lg bg-white dark:bg-dark-700 text-gray-900 dark:text-white"
            />
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div className="bg-white dark:bg-dark-800 rounded-lg shadow p-6">
        {filteredEvents.length > 0 ? (
          <div className="space-y-6">
            {filteredEvents.map((event, index) => (
              <div key={event.id} className="flex">
                <div className="flex flex-col items-center mr-4">
                  <div className={clsx('w-4 h-4 rounded-full', getEventColor(event.type))} />
                  {index < filteredEvents.length - 1 && (
                    <div className="w-0.5 h-full bg-gray-300 dark:bg-dark-600 mt-2" />
                  )}
                </div>

                <div className="flex-1 pb-6">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">
                        {event.description}
                      </p>
                      {event.platform && (
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {event.platform}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                      <FiCalendar className="mr-1" size={14} />
                      {formatDate(event.timestamp)}
                    </div>
                  </div>
                  
                  <span className={clsx(
                    'inline-block px-2 py-1 text-xs rounded-full capitalize',
                    'bg-gray-100 dark:bg-dark-700 text-gray-700 dark:text-gray-300'
                  )}>
                    {event.type.replace('_', ' ')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-600 dark:text-gray-400">No events to display</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default TimelineView;
