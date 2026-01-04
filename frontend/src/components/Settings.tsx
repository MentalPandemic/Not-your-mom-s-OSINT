import React, { useState } from 'react';
import { FiX, FiSave } from 'react-icons/fi';
import { useAppSelector } from '../hooks/useAppSelector';
import { useAppDispatch } from '../hooks/useAppDispatch';
import {
  setPreferences,
  setTheme,
  setConfidenceThreshold,
  setGraphLayout,
  setResultsPerPage,
  toggleNSFW,
} from '../store/preferencesSlice';
import clsx from 'clsx';
import toast from 'react-hot-toast';

interface SettingsProps {
  onClose: () => void;
}

const Settings: React.FC<SettingsProps> = ({ onClose }) => {
  const dispatch = useAppDispatch();
  const preferences = useAppSelector(state => state.preferences);
  const [activeTab, setActiveTab] = useState<'display' | 'data' | 'advanced'>('display');

  const handleSave = () => {
    toast.success('Settings saved successfully');
    onClose();
  };

  const tabs = [
    { id: 'display', label: 'Display' },
    { id: 'data', label: 'Data' },
    { id: 'advanced', label: 'Advanced' },
  ];

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-dark-700">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Settings</h2>
        <button
          onClick={onClose}
          className="p-2 hover:bg-gray-100 dark:hover:bg-dark-700 rounded-lg transition-colors"
        >
          <FiX size={24} />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 dark:border-dark-700 px-6">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={clsx(
              'px-4 py-3 font-medium transition-colors relative',
              activeTab === tab.id
                ? 'text-primary-600 dark:text-primary-400'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            )}
          >
            {tab.label}
            {activeTab === tab.id && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-600" />
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="p-6 space-y-6 max-h-[60vh] overflow-y-auto">
        {activeTab === 'display' && (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Theme
              </label>
              <div className="grid grid-cols-3 gap-3">
                {(['light', 'dark', 'auto'] as const).map((theme) => (
                  <button
                    key={theme}
                    onClick={() => dispatch(setTheme(theme))}
                    className={clsx(
                      'px-4 py-3 rounded-lg border-2 transition-all capitalize',
                      preferences.theme === theme
                        ? 'border-primary-600 bg-primary-50 dark:bg-primary-900/20'
                        : 'border-gray-200 dark:border-dark-600 hover:border-gray-300 dark:hover:border-dark-500'
                    )}
                  >
                    {theme}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Graph Layout
              </label>
              <div className="space-y-2">
                {(['force-directed', 'hierarchical', 'circular'] as const).map((layout) => (
                  <label key={layout} className="flex items-center space-x-3">
                    <input
                      type="radio"
                      checked={preferences.graphLayout === layout}
                      onChange={() => dispatch(setGraphLayout(layout))}
                      className="text-primary-600 focus:ring-primary-500"
                    />
                    <span className="text-gray-700 dark:text-gray-300 capitalize">
                      {layout.replace('-', ' ')}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Results Per Page
              </label>
              <select
                value={preferences.resultsPerPage}
                onChange={(e) => dispatch(setResultsPerPage(parseInt(e.target.value)))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-lg bg-white dark:bg-dark-700 text-gray-900 dark:text-white"
              >
                <option value="10">10</option>
                <option value="20">20</option>
                <option value="50">50</option>
                <option value="100">100</option>
              </select>
            </div>
          </>
        )}

        {activeTab === 'data' && (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Default Confidence Threshold: {Math.round(preferences.defaultConfidenceThreshold * 100)}%
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={preferences.defaultConfidenceThreshold * 100}
                onChange={(e) => dispatch(setConfidenceThreshold(parseInt(e.target.value) / 100))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
                <span>0%</span>
                <span>50%</span>
                <span>100%</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Preferred Data Sources
              </label>
              <div className="grid grid-cols-2 gap-3">
                {[
                  'Twitter',
                  'LinkedIn',
                  'GitHub',
                  'Facebook',
                  'Instagram',
                  'Reddit',
                  'People Search',
                  'Domain Records',
                ].map((source) => (
                  <label key={source} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      defaultChecked
                      className="rounded text-primary-600 focus:ring-primary-500"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">{source}</span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Include NSFW Content
                </span>
                <button
                  onClick={() => dispatch(toggleNSFW())}
                  className={clsx(
                    'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                    preferences.includeNSFW ? 'bg-primary-600' : 'bg-gray-300 dark:bg-dark-600'
                  )}
                >
                  <span
                    className={clsx(
                      'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                      preferences.includeNSFW ? 'translate-x-6' : 'translate-x-1'
                    )}
                  />
                </button>
              </label>
            </div>
          </>
        )}

        {activeTab === 'advanced' && (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                API Timeout (ms)
              </label>
              <input
                type="number"
                value={preferences.apiTimeout}
                onChange={(e) =>
                  dispatch(setPreferences({ apiTimeout: parseInt(e.target.value) }))
                }
                min="1000"
                max="120000"
                step="1000"
                className="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-lg bg-white dark:bg-dark-700 text-gray-900 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Cache Settings
              </label>
              <div className="space-y-3">
                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    defaultChecked
                    className="rounded text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-gray-700 dark:text-gray-300">
                    Enable result caching
                  </span>
                </label>
                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    defaultChecked
                    className="rounded text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-gray-700 dark:text-gray-300">
                    Cache graph data
                  </span>
                </label>
              </div>
            </div>

            <div>
              <button className="w-full px-4 py-2 text-red-600 dark:text-red-400 border border-red-600 dark:border-red-400 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors">
                Clear All Cache
              </button>
            </div>

            <div>
              <button className="w-full px-4 py-2 text-gray-600 dark:text-gray-400 border border-gray-300 dark:border-dark-600 rounded-lg hover:bg-gray-50 dark:hover:bg-dark-700 transition-colors">
                Reset to Defaults
              </button>
            </div>
          </>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-200 dark:border-dark-700">
        <button
          onClick={onClose}
          className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-700 rounded-lg transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={handleSave}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex items-center space-x-2"
        >
          <FiSave size={16} />
          <span>Save Changes</span>
        </button>
      </div>
    </div>
  );
};

export default Settings;
