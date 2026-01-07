import React, { useState } from 'react';
import { Lightbulb, Menu, X, User, Settings as SettingsIcon, Download, MapPin, GitBranch, Search, List, BarChart3, Users, Globe, Activity } from 'lucide-react';

// Simple in-memory state management (Redux alternative for this implementation)
const AppState = {
  currentView: 'search',
  sidebarOpen: true,
  searchQuery: '',
  searchType: 'username' as const,
  darkMode: false
};

// Navigation items
const navItems = [
  { id: 'search', label: 'Search', icon: Search },
  { id: 'results', label: 'Results', icon: List },
  { id: 'graph', label: 'Graph', icon: GitBranch },
  { id: 'timeline', label: 'Timeline', icon: Activity },
  { id: 'geo', label: 'Map', icon: MapPin },
  { id: 'export', label: 'Export', icon: Download },
  { id: 'settings', label: 'Settings', icon: SettingsIcon }
];

function App() {
  const [currentView, setCurrentView] = useState(AppState.currentView);
  const [sidebarOpen, setSidebarOpen] = useState(AppState.sidebarOpen);
  const [searchQuery, setSearchQuery] = useState(AppState.searchQuery);
  const [searchType, setSearchType] = useState(AppState.searchType);
  const [darkMode, setDarkMode] = useState(AppState.darkMode);

  return (
    <div className={`min-h-screen ${darkMode ? 'dark bg-gray-900' : 'bg-gray-50'}`}>
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="p-2 rounded-md text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                {sidebarOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
              </button>
              <div className="flex items-center ml-4">
                <Lightbulb className="h-8 w-8 text-blue-600 dark:text-blue-500" />
                <span className="ml-3 text-xl font-semibold text-gray-900 dark:text-white">OSINT Dashboard</span>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setDarkMode(!darkMode)}
                className="p-2 rounded-full text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                {darkMode ? (
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                ) : (
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                  </svg>
                )}
              </button>
              <button className="p-2 rounded-full text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700">
                <User className="h-6 w-6" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="flex h-screen pt-16">
        {/* Sidebar */}
        <aside className={`${sidebarOpen ? 'w-64' : 'w-20'} bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transition-all duration-200`}>
          <nav className="p-4 space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => setCurrentView(item.id)}
                  className={`w-full flex items-center ${sidebarOpen ? 'justify-start px-3' : 'justify-center'} py-3 rounded-lg transition-colors ${
                    currentView === item.id
                      ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <Icon className={`h-5 w-5 ${sidebarOpen ? 'mr-3' : ''}`} />
                  {sidebarOpen && <span className="text-sm font-medium">{item.label}</span>}
                </button>
              );
            })}
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-auto">
          <div className="p-6">
            {/* Dashboard Welcome */}
            {currentView === 'search' && (
              <div className="space-y-6">
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
                  <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">OSINT Intelligence Dashboard</h1>
                  <p className="text-gray-600 dark:text-gray-400">
                    Search, analyze, and visualize open-source intelligence data across multiple platforms and sources.
                  </p>
                </div>

                {/* Statistics Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center">
                      <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                        <Search className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                      </div>
                      <div className="ml-4">
                        <p className="text-sm text-gray-600 dark:text-gray-400">Total Searches</p>
                        <p className="text-2xl font-semibold text-gray-900 dark:text-white">1,234</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center">
                      <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
                        <Users className="h-6 w-6 text-green-600 dark:text-green-400" />
                      </div>
                      <div className="ml-4">
                        <p className="text-sm text-gray-600 dark:text-gray-400">Identities Found</p>
                        <p className="text-2xl font-semibold text-gray-900 dark:text-white">5,678</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center">
                      <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
                        <Globe className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                      </div>
                      <div className="ml-4">
                        <p className="text-sm text-gray-600 dark:text-gray-400">Data Sources</p>
                        <p className="text-2xl font-semibold text-gray-900 dark:text-white">42</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center">
                      <div className="p-2 bg-orange-100 dark:bg-orange-900 rounded-lg">
                        <BarChart3 className="h-6 w-6 text-orange-600 dark:text-orange-400" />
                      </div>
                      <div className="ml-4">
                        <p className="text-sm text-gray-600 dark:text-gray-400">Search Efficiency</p>
                        <p className="text-2xl font-semibold text-gray-900 dark:text-white">85%</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Search Interface */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
                  <div className="p-6">
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Quick Search</h2>
                    <div className="space-y-4">
                      <div className="flex space-x-4">
                        <select
                          value={searchType}
                          onChange={(e) => setSearchType(e.target.value as any)}
                          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                          <option value="username">Username</option>
                          <option value="email">Email</option>
                          <option value="phone">Phone</option>
                          <option value="name">Name</option>
                          <option value="domain">Domain</option>
                        </select>
                        <input
                          type="text"
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          placeholder="Enter search query..."
                          className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                        <button className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                          <Search className="h-5 w-5" />
                        </button>
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        Searching for: <span className="font-medium">{searchType}</span> - <span className="font-mono">{searchQuery || '...'}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Results View */}
            {currentView === 'results' && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Search Results</h2>
                <div className="space-y-4">
                  <div className="p-4 border border-gray-200 dark:border-gray-600 rounded-lg">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-medium text-gray-900 dark:text-white">John_Doe_Coder</h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400">GitHub, Twitter, LinkedIn</p>
                        <span className="inline-block mt-2 px-2 py-1 text-xs bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-300 rounded">95% Confidence</span>
                      </div>
                      <button className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300">View Details</button>
                    </div>
                  </div>
                  <div className="p-4 border border-gray-200 dark:border-gray-600 rounded-lg">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-medium text-gray-900 dark:text-white">johndoe@example.com</h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400">Email, Social Media</p>
                        <span className="inline-block mt-2 px-2 py-1 text-xs bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-300 rounded">78% Confidence</span>
                      </div>
                      <button className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300">View Details</button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Graph Visualization */}
            {currentView === 'graph' && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Relationship Graph</h2>
                <div className="h-96 bg-gray-50 dark:bg-gray-900 rounded-lg flex items-center justify-center border border-dashed border-gray-300 dark:border-gray-600">
                  <div className="text-center">
                    <GitBranch className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600 dark:text-gray-400">Interactive network graph visualization</p>
                    <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">1000+ nodes with relationship mapping</p>
                  </div>
                </div>
              </div>
            )}

            {/* Timeline View */}
            {currentView === 'timeline' && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Activity Timeline</h2>
                <div className="space-y-4">
                  <div className="flex items-center space-x-4">
                    <div className="w-3 h-3 bg-blue-600 rounded-full"></div>
                    <div className="flex-1 border-l-2 border-gray-300 dark:border-gray-600 pl-4">
                      <p className="font-medium text-gray-900 dark:text-white">Account Created</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">GitHub - Jan 15, 2020</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="w-3 h-3 bg-green-600 rounded-full"></div>
                    <div className="flex-1 border-l-2 border-gray-300 dark:border-gray-600 pl-4">
                      <p className="font-medium text-gray-900 dark:text-white">First Repository</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Created 'hello-world' repo - Feb 3, 2020</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Geo Visualization */}
            {currentView === 'geo' && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Geographic Distribution</h2>
                <div className="h-96 bg-gray-50 dark:bg-gray-900 rounded-lg flex items-center justify-center border border-dashed border-gray-300 dark:border-gray-600">
                  <div className="text-center">
                    <MapPin className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600 dark:text-gray-400">Interactive world map with location data</p>
                    <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">IP geolocation and profile locations</p>
                  </div>
                </div>
              </div>
            )}

            {/* Export Panel */}
            {currentView === 'export' && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Export Data</h2>
                <div className="grid grid-cols-2 gap-4">
                  <button className="p-4 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                    <Download className="h-6 w-6 text-blue-600 dark:text-blue-400 mx-auto mb-2" />
                    <p className="text-sm font-medium text-gray-900 dark:text-white">CSV Export</p>
                  </button>
                  <button className="p-4 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                    <Download className="h-6 w-6 text-green-600 dark:text-green-400 mx-auto mb-2" />
                    <p className="text-sm font-medium text-gray-900 dark:text-white">JSON Export</p>
                  </button>
                  <button className="p-4 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                    <Download className="h-6 w-6 text-red-600 dark:text-red-400 mx-auto mb-2" />
                    <p className="text-sm font-medium text-gray-900 dark:text-white">PDF Report</p>
                  </button>
                  <button className="p-4 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                    <Download className="h-6 w-6 text-purple-600 dark:text-purple-400 mx-auto mb-2" />
                    <p className="text-sm font-medium text-gray-900 dark:text-white">Excel Export</p>
                  </button>
                </div>
              </div>
            )}

            {/* Settings */}
            {currentView === 'settings' && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Settings</h2>
                <div className="space-y-6">
                  <div>
                    <h3 className="font-medium text-gray-900 dark:text-white mb-3">Display</h3>
                    <div className="space-y-3">
                      <label className="flex items-center space-x-3">
                        <input
                          type="checkbox"
                          checked={darkMode}
                          onChange={() => setDarkMode(!darkMode)}
                          className="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="text-gray-700 dark:text-gray-300">Dark Mode</span>
                      </label>
                    </div>
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900 dark:text-white mb-3">Data Preferences</h3>
                    <div className="space-y-3">
                      <label className="flex items-center space-x-3">
                        <input type="checkbox" defaultChecked className="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500" />
                        <span className="text-gray-700 dark:text-gray-300">Auto-save searches</span>
                      </label>
                      <label className="flex items-center space-x-3">
                        <input type="checkbox" defaultChecked className="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500" />
                        <span className="text-gray-700 dark:text-gray-300">Show confidence scores</span>
                      </label>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;