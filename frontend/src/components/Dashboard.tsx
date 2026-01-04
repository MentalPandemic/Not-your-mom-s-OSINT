import React, { useState, useEffect } from 'react';
import { FiSearch, FiSettings, FiUser, FiDownload, FiMenu, FiX, FiMoon, FiSun } from 'react-icons/fi';
import { useAppSelector } from '../hooks/useAppSelector';
import { useAppDispatch } from '../hooks/useAppDispatch';
import { setActiveView, setTheme, toggleSidebar, toggleDetailsPanel } from '../store/uiSlice';
import SearchInterface from './SearchInterface';
import ResultsView from './ResultsView';
import GraphVisualization from './GraphVisualization';
import TimelineView from './TimelineView';
import ExportPanel from './ExportPanel';
import IdentityProfile from './IdentityProfile';
import Sidebar from './Sidebar';
import Settings from './Settings';
import clsx from 'clsx';

const Dashboard: React.FC = () => {
  const dispatch = useAppDispatch();
  const { theme, sidebarCollapsed, detailsPanelOpen, activeView } = useAppSelector(state => state.ui);
  const { selectedNode } = useAppSelector(state => state.graph);
  const [showSettings, setShowSettings] = useState(false);

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  const toggleTheme = () => {
    dispatch(setTheme(theme === 'dark' ? 'light' : 'dark'));
  };

  const renderMainContent = () => {
    switch (activeView) {
      case 'search':
        return <SearchInterface />;
      case 'results':
        return <ResultsView />;
      case 'graph':
        return <GraphVisualization />;
      case 'timeline':
        return <TimelineView />;
      case 'export':
        return <ExportPanel />;
      default:
        return <SearchInterface />;
    }
  };

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-dark-900">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 h-16 bg-white dark:bg-dark-800 border-b border-gray-200 dark:border-dark-700 z-50">
        <div className="flex items-center justify-between h-full px-4">
          {/* Logo and Brand */}
          <div className="flex items-center space-x-4">
            <button
              onClick={() => dispatch(toggleSidebar())}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-700 transition-colors"
              aria-label="Toggle sidebar"
            >
              {sidebarCollapsed ? <FiMenu size={20} /> : <FiX size={20} />}
            </button>
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <FiSearch className="text-white" size={18} />
              </div>
              <h1 className="text-xl font-bold text-gray-900 dark:text-white hidden sm:block">
                OSINT Dashboard
              </h1>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex items-center space-x-2">
            <button
              onClick={() => dispatch(setActiveView('search'))}
              className={clsx(
                'px-4 py-2 rounded-lg transition-colors',
                activeView === 'search'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-700'
              )}
            >
              Search
            </button>
            <button
              onClick={() => dispatch(setActiveView('results'))}
              className={clsx(
                'px-4 py-2 rounded-lg transition-colors',
                activeView === 'results'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-700'
              )}
            >
              Results
            </button>
            <button
              onClick={() => dispatch(setActiveView('graph'))}
              className={clsx(
                'px-4 py-2 rounded-lg transition-colors',
                activeView === 'graph'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-700'
              )}
            >
              Graph
            </button>
            <button
              onClick={() => dispatch(setActiveView('export'))}
              className={clsx(
                'px-4 py-2 rounded-lg transition-colors',
                activeView === 'export'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-700'
              )}
            >
              <FiDownload className="inline mr-1" />
              Export
            </button>
          </nav>

          {/* User Menu */}
          <div className="flex items-center space-x-2">
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-700 transition-colors"
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? <FiSun size={20} /> : <FiMoon size={20} />}
            </button>
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-700 transition-colors"
              aria-label="Settings"
            >
              <FiSettings size={20} />
            </button>
            <button
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-700 transition-colors"
              aria-label="User profile"
            >
              <FiUser size={20} />
            </button>
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex w-full pt-16">
        {/* Left Sidebar */}
        {!sidebarCollapsed && (
          <aside className="w-64 bg-white dark:bg-dark-800 border-r border-gray-200 dark:border-dark-700 overflow-y-auto">
            <Sidebar />
          </aside>
        )}

        {/* Center Content */}
        <main className="flex-1 overflow-y-auto">
          {renderMainContent()}
        </main>

        {/* Right Details Panel */}
        {detailsPanelOpen && selectedNode && (
          <aside className="w-80 bg-white dark:bg-dark-800 border-l border-gray-200 dark:border-dark-700 overflow-y-auto">
            <IdentityProfile />
          </aside>
        )}
      </div>

      {/* Settings Modal */}
      {showSettings && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white dark:bg-dark-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <Settings onClose={() => setShowSettings(false)} />
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
