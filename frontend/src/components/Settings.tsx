import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Cog6ToothIcon,
  UserIcon,
  BellIcon,
  ShieldCheckIcon,
  EyeIcon,
  PaintBrushIcon,
  ChartBarIcon,
  GlobeAltIcon,
  ClockIcon,
  TrashIcon,
  KeyIcon,
  DevicePhoneMobileIcon,
  CloudIcon,
  DatabaseIcon,
  LockClosedIcon,
  CheckIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { useAppDispatch, useAppSelector } from '@/store';
import {
  selectUser,
  updateUser,
  updatePreferences,
} from '@/store/slices/authSlice';
import {
  selectTheme,
  selectPreferences,
  setTheme,
  updatePreferences as updateUIPreferences,
} from '@/store/slices/uiSlice';
import { UserRole } from '@/types';

interface SettingsProps {
  className?: string;
}

export const Settings: React.FC<SettingsProps> = ({ className = '' }) => {
  const dispatch = useAppDispatch();
  const user = useAppSelector(selectUser);
  const theme = useAppSelector(selectTheme);
  const uiPreferences = useAppSelector(selectPreferences);

  const [activeSection, setActiveSection] = useState('profile');
  const [hasChanges, setHasChanges] = useState(false);
  const [tempUser, setTempUser] = useState(user);
  const [tempPreferences, setTempPreferences] = useState(uiPreferences);

  const settingsSections = [
    {
      id: 'profile',
      label: 'Profile',
      icon: UserIcon,
      description: 'Manage your account information',
    },
    {
      id: 'preferences',
      label: 'Preferences',
      icon: Cog6ToothIcon,
      description: 'Customize your dashboard experience',
    },
    {
      id: 'notifications',
      label: 'Notifications',
      icon: BellIcon,
      description: 'Configure alerts and notifications',
    },
    {
      id: 'privacy',
      label: 'Privacy & Security',
      icon: ShieldCheckIcon,
      description: 'Privacy settings and security options',
    },
    {
      id: 'display',
      label: 'Display',
      icon: PaintBrushIcon,
      description: 'Theme, layout, and visual preferences',
    },
    {
      id: 'data',
      label: 'Data Management',
      icon: DatabaseIcon,
      description: 'Data retention and export settings',
    },
    {
      id: 'api',
      label: 'API & Integrations',
      icon: GlobeAltIcon,
      description: 'API keys and third-party integrations',
    },
    {
      id: 'advanced',
      label: 'Advanced',
      icon: Cog6ToothIcon,
      description: 'Advanced settings and diagnostics',
    },
  ];

  const handleSave = () => {
    if (tempUser && tempUser.id !== user?.id) {
      dispatch(updateUser(tempUser));
    }
    
    if (tempPreferences !== uiPreferences) {
      dispatch(updateUIPreferences(tempPreferences));
    }
    
    setHasChanges(false);
  };

  const handleReset = () => {
    setTempUser(user);
    setTempPreferences(uiPreferences);
    setHasChanges(false);
  };

  const updateTempUser = (updates: any) => {
    setTempUser(prev => ({ ...prev, ...updates }));
    setHasChanges(true);
  };

  const updateTempPreferences = (updates: any) => {
    setTempPreferences(prev => ({ ...prev, ...updates }));
    setHasChanges(true);
  };

  const renderProfileSection = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
          Profile Information
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Full Name
            </label>
            <input
              type="text"
              value={tempUser?.name || ''}
              onChange={(e) => updateTempUser({ name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Email Address
            </label>
            <input
              type="email"
              value={tempUser?.email || ''}
              onChange={(e) => updateTempUser({ email: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Role
            </label>
            <select
              value={tempUser?.role || UserRole.VIEWER}
              onChange={(e) => updateTempUser({ role: e.target.value as UserRole })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
              disabled
            >
              <option value={UserRole.ADMIN}>Administrator</option>
              <option value={UserRole.ANALYST}>Analyst</option>
              <option value={UserRole.VIEWER}>Viewer</option>
            </select>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Contact your administrator to change your role
            </p>
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
          Account Status
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div className="flex items-center space-x-2">
              <CheckIcon className="h-5 w-5 text-green-500" />
              <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                Account Active
              </span>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Last login: {user?.lastLogin ? new Date(user.lastLogin).toLocaleString() : 'Unknown'}
            </p>
          </div>
          <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div className="flex items-center space-x-2">
              <KeyIcon className="h-5 w-5 text-blue-500" />
              <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                API Access
              </span>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Rate limit: 1000 requests/hour
            </p>
          </div>
        </div>
      </div>
    </div>
  );

  const renderPreferencesSection = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
          Search Preferences
        </h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Default Confidence Threshold: {Math.round((tempUser?.preferences?.defaultConfidenceThreshold || 0.7) * 100)}%
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={tempUser?.preferences?.defaultConfidenceThreshold || 0.7}
              onChange={(e) => updateTempUser({
                preferences: {
                  ...tempUser?.preferences,
                  defaultConfidenceThreshold: parseFloat(e.target.value),
                }
              })}
              className="w-full"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Data Retention (days)
            </label>
            <input
              type="number"
              min="1"
              max="365"
              value={tempUser?.preferences?.dataRetentionDays || 30}
              onChange={(e) => updateTempUser({
                preferences: {
                  ...tempUser?.preferences,
                  dataRetentionDays: parseInt(e.target.value),
                }
              })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
            />
          </div>
          <div className="flex items-center">
            <input
              type="checkbox"
              checked={tempUser?.preferences?.includeNSFW || false}
              onChange={(e) => updateTempUser({
                preferences: {
                  ...tempUser?.preferences,
                  includeNSFW: e.target.checked,
                }
              })}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
              Include NSFW content in search results
            </span>
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
          Auto-save & Notifications
        </h3>
        <div className="space-y-4">
          <div className="flex items-center">
            <input
              type="checkbox"
              checked={tempUser?.preferences?.autoSave || false}
              onChange={(e) => updateTempUser({
                preferences: {
                  ...tempUser?.preferences,
                  autoSave: e.target.checked,
                }
              })}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
              Auto-save workspace changes
            </span>
          </div>
        </div>
      </div>
    </div>
  );

  const renderNotificationsSection = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
          Notification Preferences
        </h3>
        <div className="space-y-4">
          <div className="flex items-center">
            <input
              type="checkbox"
              checked={tempUser?.preferences?.notifications?.email || false}
              onChange={(e) => updateTempUser({
                preferences: {
                  ...tempUser?.preferences,
                  notifications: {
                    ...tempUser?.preferences?.notifications,
                    email: e.target.checked,
                  }
                }
              })}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
              Email notifications
            </span>
          </div>
          <div className="flex items-center">
            <input
              type="checkbox"
              checked={tempUser?.preferences?.notifications?.browser || false}
              onChange={(e) => updateTempUser({
                preferences: {
                  ...tempUser?.preferences,
                  notifications: {
                    ...tempUser?.preferences?.notifications,
                    browser: e.target.checked,
                  }
                }
              })}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
              Browser notifications
            </span>
          </div>
          <div className="flex items-center">
            <input
              type="checkbox"
              checked={tempUser?.preferences?.notifications?.desktop || false}
              onChange={(e) => updateTempUser({
                preferences: {
                  ...tempUser?.preferences,
                  notifications: {
                    ...tempUser?.preferences?.notifications,
                    desktop: e.target.checked,
                  }
                }
              })}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
              Desktop notifications
            </span>
          </div>
        </div>
      </div>
    </div>
  );

  const renderDisplaySection = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
          Theme
        </h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Color Scheme
            </label>
            <div className="grid grid-cols-3 gap-3">
              {[
                { value: 'light', label: 'Light', description: 'Clean and bright' },
                { value: 'dark', label: 'Dark', description: 'Easy on the eyes' },
                { value: 'auto', label: 'Auto', description: 'Follow system' },
              ].map((option) => (
                <button
                  key={option.value}
                  onClick={() => dispatch(setTheme(option.value as any))}
                  className={`p-3 border rounded-lg text-left ${
                    theme === option.value
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                >
                  <div className="font-medium text-gray-900 dark:text-gray-100">
                    {option.label}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {option.description}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
          Interface Preferences
        </h3>
        <div className="space-y-4">
          <div className="flex items-center">
            <input
              type="checkbox"
              checked={tempPreferences.compactMode || false}
              onChange={(e) => updateTempPreferences({ compactMode: e.target.checked })}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
              Compact mode (reduce spacing)
            </span>
          </div>
          <div className="flex items-center">
            <input
              type="checkbox"
              checked={tempPreferences.showConfidenceScores || false}
              onChange={(e) => updateTempPreferences({ showConfidenceScores: e.target.checked })}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
              Show confidence scores by default
            </span>
          </div>
          <div className="flex items-center">
            <input
              type="checkbox"
              checked={tempPreferences.graphAnimations || false}
              onChange={(e) => updateTempPreferences({ graphAnimations: e.target.checked })}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
              Enable graph animations
            </span>
          </div>
        </div>
      </div>
    </div>
  );

  const renderDataSection = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
          Data Management
        </h3>
        <div className="space-y-4">
          <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
            <div className="flex items-start space-x-3">
              <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mt-0.5" />
              <div>
                <h4 className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                  Data Retention Policy
                </h4>
                <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
                  Your data is retained for {tempUser?.preferences?.dataRetentionDays || 30} days according to your preferences.
                </p>
              </div>
            </div>
          </div>
          
          <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div>
              <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                Clear Search History
              </h4>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Remove all saved searches and history
              </p>
            </div>
            <button className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700">
              Clear History
            </button>
          </div>

          <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div>
              <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                Export All Data
              </h4>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Download all your data in JSON format
              </p>
            </div>
            <button className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
              Export Data
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  const renderAPISection = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
          API Configuration
        </h3>
        <div className="space-y-4">
          <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
            <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
              API Key
            </h4>
            <div className="flex items-center space-x-2">
              <input
                type="password"
                value="sk-...abc123"
                readOnly
                className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white font-mono text-sm"
              />
              <button className="px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
                Regenerate
              </button>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Keep your API key secure and don't share it publicly
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                Rate Limit
              </h4>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">1,000</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">requests per hour</p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                Usage This Hour
              </h4>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">247</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">requests used</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderAdvancedSection = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
          Advanced Settings
        </h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Graph Layout Algorithm
            </label>
            <select
              value={tempUser?.preferences?.defaultLayout || 'force-directed'}
              onChange={(e) => updateTempUser({
                preferences: {
                  ...tempUser?.preferences,
                  defaultLayout: e.target.value,
                }
              })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
            >
              <option value="force-directed">Force Directed</option>
              <option value="hierarchical">Hierarchical</option>
              <option value="circular">Circular</option>
            </select>
          </div>

          <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div>
              <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                Enable Debug Mode
              </h4>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Show detailed debug information
              </p>
            </div>
            <input
              type="checkbox"
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
          </div>

          <div className="p-4 border border-red-200 dark:border-red-800 rounded-lg">
            <div className="flex items-center space-x-3">
              <ExclamationTriangleIcon className="h-5 w-5 text-red-600 dark:text-red-400" />
              <div>
                <h4 className="text-sm font-medium text-red-800 dark:text-red-200">
                  Danger Zone
                </h4>
                <p className="text-sm text-red-700 dark:text-red-300">
                  These actions cannot be undone
                </p>
              </div>
            </div>
            <div className="mt-4 space-y-2">
              <button className="w-full px-3 py-2 text-sm bg-red-600 text-white rounded hover:bg-red-700">
                Delete Account
              </button>
              <button className="w-full px-3 py-2 text-sm border border-red-300 dark:border-red-700 text-red-600 dark:text-red-400 rounded hover:bg-red-50 dark:hover:bg-red-900/20">
                Reset All Settings
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderSection = () => {
    switch (activeSection) {
      case 'profile':
        return renderProfileSection();
      case 'preferences':
        return renderPreferencesSection();
      case 'notifications':
        return renderNotificationsSection();
      case 'display':
        return renderDisplaySection();
      case 'data':
        return renderDataSection();
      case 'api':
        return renderAPISection();
      case 'advanced':
        return renderAdvancedSection();
      default:
        return renderProfileSection();
    }
  };

  return (
    <div className={`h-full flex ${className}`}>
      {/* Sidebar */}
      <div className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 overflow-y-auto">
        <div className="p-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Settings
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Manage your account and preferences
          </p>
        </div>
        
        <nav className="px-4 pb-4">
          <div className="space-y-1">
            {settingsSections.map((section) => {
              const Icon = section.icon;
              return (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={`w-full flex items-start space-x-3 px-3 py-2 text-left rounded-lg transition-colors ${
                    activeSection === section.id
                      ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`}
                >
                  <Icon className="h-5 w-5 mt-0.5" />
                  <div>
                    <div className="font-medium">{section.label}</div>
                    <div className="text-xs opacity-75">{section.description}</div>
                  </div>
                </button>
              );
            })}
          </div>
        </nav>
      </div>

      {/* Main content */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto p-6">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeSection}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6"
            >
              {renderSection()}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>

      {/* Save/Cancel footer */}
      <div className="fixed bottom-0 left-64 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 p-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="text-sm text-gray-500 dark:text-gray-400">
            {hasChanges ? 'You have unsaved changes' : 'All changes saved'}
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={handleReset}
              disabled={!hasChanges}
              className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 disabled:opacity-50"
            >
              Reset
            </button>
            <button
              onClick={handleSave}
              disabled={!hasChanges}
              className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              Save Changes
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;