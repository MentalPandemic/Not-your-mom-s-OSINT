import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MagnifyingGlassIcon,
  ChartBarIcon,
  MapIcon,
  DocumentArrowDownIcon,
  Cog6ToothIcon,
  UserIcon,
  BellIcon,
  Bars3Icon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import { 
  SearchInterface, 
  ResultsView, 
  GraphVisualization,
  TimelineView,
  ExportPanel,
  Settings,
  Workspace
} from './index';
import { 
  useAppDispatch, 
  useAppSelector 
} from '@/store';
import { 
  selectActiveView, 
  selectSidebarCollapsed,
  selectNotifications,
  selectTheme,
  setActiveView,
  toggleSidebar,
  addNotification,
  closeAllModals,
} from '@/store/slices/uiSlice';
import { selectUser } from '@/store/slices/authSlice';
import { 
  SidebarFilters,
  UserMenu,
  NotificationPanel,
  Breadcrumbs,
  LoadingOverlay,
  ErrorBoundary
} from '../ui';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';

interface DashboardProps {
  className?: string;
}

export const Dashboard: React.FC<DashboardProps> = ({ className = '' }) => {
  const dispatch = useAppDispatch();
  const activeView = useAppSelector(selectActiveView);
  const sidebarCollapsed = useAppSelector(selectSidebarCollapsed);
  const notifications = useAppSelector(selectNotifications);
  const theme = useAppSelector(selectTheme);
  const user = useAppSelector(selectUser);

  // Apply theme to document
  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else if (theme === 'light') {
      root.classList.remove('dark');
    } else {
      // Auto theme - follow system preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      if (prefersDark) {
        root.classList.add('dark');
      } else {
        root.classList.remove('dark');
      }
    }
  }, [theme]);

  // Setup keyboard shortcuts
  useKeyboardShortcuts();

  // Handle navigation
  const handleNavigation = (view: typeof activeView) => {
    dispatch(setActiveView(view));
    dispatch(addNotification({
      type: 'info',
      title: `Switched to ${view} view`,
      duration: 2000,
    }));
  };

  const navigationItems = [
    {
      id: 'search',
      label: 'Search',
      icon: MagnifyingGlassIcon,
      description: 'Search OSINT data sources',
    },
    {
      id: 'results',
      label: 'Results',
      icon: ChartBarIcon,
      description: 'View search results',
    },
    {
      id: 'graph',
      label: 'Graph',
      icon: ChartBarIcon,
      description: 'Interactive network visualization',
    },
    {
      id: 'timeline',
      label: 'Timeline',
      icon: MapIcon,
      description: 'Chronological analysis',
    },
    {
      id: 'export',
      label: 'Export',
      icon: DocumentArrowDownIcon,
      description: 'Export data and reports',
    },
    {
      id: 'settings',
      label: 'Settings',
      icon: Cog6ToothIcon,
      description: 'Application settings',
    },
  ] as const;

  return (
    <div className={`h-screen flex bg-gray-50 dark:bg-gray-900 ${className}`}>
      <ErrorBoundary>
        {/* Header */}
        <header className="fixed top-0 left-0 right-0 z-50 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between px-4 py-3">
            {/* Left section */}
            <div className="flex items-center space-x-4">
              {/* Mobile menu button */}
              <button
                onClick={() => dispatch(toggleSidebar())}
                className="lg:hidden p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-100 dark:hover:bg-gray-700"
              >
                {sidebarCollapsed ? (
                  <Bars3Icon className="h-6 w-6" />
                ) : (
                  <XMarkIcon className="h-6 w-6" />
                )}
              </button>

              {/* Logo and branding */}
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">OS</span>
                </div>
                <div className="hidden sm:block">
                  <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                    OSINT Dashboard
                  </h1>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Intelligence Aggregation Platform
                  </p>
                </div>
              </div>
            </div>

            {/* Center section - Search bar */}
            <div className="flex-1 max-w-2xl mx-4">
              <SearchInterface compact />
            </div>

            {/* Right section */}
            <div className="flex items-center space-x-2">
              {/* Notifications */}
              <NotificationPanel />

              {/* User menu */}
              <UserMenu user={user} />

              {/* Theme toggle and other controls */}
              <div className="flex items-center space-x-1">
                <button
                  onClick={() => handleNavigation('settings')}
                  className="p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-100 dark:hover:bg-gray-700"
                >
                  <Cog6ToothIcon className="h-5 w-5" />
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Sidebar */}
        <AnimatePresence>
          {!sidebarCollapsed && (
            <motion.aside
              initial={{ x: -300 }}
              animate={{ x: 0 }}
              exit={{ x: -300 }}
              transition={{ type: 'spring', damping: 30, stiffness: 300 }}
              className="fixed left-0 top-16 bottom-0 w-80 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 z-40 overflow-y-auto"
            >
              <div className="p-4">
                <SidebarFilters />
              </div>
            </motion.aside>
          )}
        </AnimatePresence>

        {/* Main content area */}
        <main className={`flex-1 flex flex-col overflow-hidden ${
          sidebarCollapsed ? 'ml-0' : 'lg:ml-80'
        } mt-16`}>
          {/* Breadcrumbs */}
          <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-2">
            <Breadcrumbs />
          </div>

          {/* Navigation tabs */}
          <nav className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4">
            <div className="flex space-x-1 overflow-x-auto">
              {navigationItems.map((item) => {
                const Icon = item.icon;
                const isActive = activeView === item.id;
                
                return (
                  <button
                    key={item.id}
                    onClick={() => handleNavigation(item.id as typeof activeView)}
                    className={`flex items-center space-x-2 px-3 py-2 rounded-t-md text-sm font-medium transition-colors whitespace-nowrap ${
                      isActive
                        ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 border-b-2 border-blue-500'
                        : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700'
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    <span>{item.label}</span>
                  </button>
                );
              })}
            </div>
          </nav>

          {/* Content area */}
          <div className="flex-1 overflow-hidden bg-gray-50 dark:bg-gray-900">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeView}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.2 }}
                className="h-full"
              >
                {activeView === 'search' && <SearchInterface />}
                {activeView === 'results' && <ResultsView />}
                {activeView === 'graph' && <GraphVisualization />}
                {activeView === 'timeline' && <TimelineView />}
                {activeView === 'export' && <ExportPanel />}
                {activeView === 'settings' && <Settings />}
              </motion.div>
            </AnimatePresence>
          </div>
        </main>

        {/* Notifications */}
        <div className="fixed top-20 right-4 z-50 space-y-2">
          {notifications.map((notification) => (
            <motion.div
              key={notification.id}
              initial={{ opacity: 0, x: 300 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 300 }}
              className={`p-4 rounded-lg shadow-lg max-w-sm ${
                notification.type === 'success' 
                  ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
                  : notification.type === 'error'
                  ? 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800'
                  : notification.type === 'warning'
                  ? 'bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800'
                  : 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {notification.title}
                  </h4>
                  {notification.message && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {notification.message}
                    </p>
                  )}
                </div>
                <button
                  onClick={() => dispatch(removeNotification(notification.id))}
                  className="ml-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
                >
                  <XMarkIcon className="h-4 w-4" />
                </button>
              </div>
              
              {notification.actions && (
                <div className="mt-3 flex space-x-2">
                  {notification.actions.map((action, index) => (
                    <button
                      key={index}
                      className="text-xs px-2 py-1 bg-gray-200 dark:bg-gray-700 rounded hover:bg-gray-300 dark:hover:bg-gray-600"
                    >
                      {action.label}
                    </button>
                  ))}
                </div>
              )}
            </motion.div>
          ))}
        </div>

        {/* Loading overlay */}
        <LoadingOverlay />
      </ErrorBoundary>
    </div>
  );
};

export default Dashboard;