import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Search, BarChart3, Users, Globe, Activity, Shield } from 'lucide-react';
import SearchInterface from './SearchInterface';
import StatisticsPanel from './StatisticsPanel';
import RecentSearches from './RecentSearches';
import SavedSearches from './SavedSearches';

interface DashboardProps {
  currentView: string;
}

const Dashboard: React.FC<DashboardProps> = ({ currentView }) => {
  const [stats, setStats] = useState({
    totalSearches: 0,
    totalIdentities: 0,
    dataSources: 0,
    searchRate: 0
  });

  useEffect(() => {
    // Simulate loading statistics
    const timer = setTimeout(() => {
      setStats({
        totalSearches: 1234,
        totalIdentities: 5678,
        dataSources: 42,
        searchRate: 85
      });
    }, 500);

    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">OSINT Intelligence Dashboard</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Search, analyze, and visualize open-source intelligence data across multiple platforms and sources.
        </p>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700"
        >
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <Search className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Searches</p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">{stats.totalSearches.toLocaleString()}</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700"
        >
          <div className="flex items-center">
            <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
              <Users className="h-6 w-6 text-green-600 dark:text-green-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600 dark:text-gray-400">Identities Found</p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">{stats.totalIdentities.toLocaleString()}</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700"
        >
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
              <Globe className="h-6 w-6 text-purple-600 dark:text-purple-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600 dark:text-gray-400">Data Sources</p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">{stats.dataSources}</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700"
        >
          <div className="flex items-center">
            <div className="p-2 bg-orange-100 dark:bg-orange-900 rounded-lg">
              <Activity className="h-6 w-6 text-orange-600 dark:text-orange-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600 dark:text-gray-400">Search Efficiency</p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">{stats.searchRate}%</p>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Search Interface - Main */}
        <div className="lg:col-span-2">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
            <div className="p-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Quick Search</h2>
              <SearchInterface />
            </div>
          </div>
        </div>

        {/* Side Panels */}
        <div className="space-y-6">
          <RecentSearches />
          <SavedSearches />
        </div>
      </div>

      {/* Statistics Panel */}
      <StatisticsPanel />
    </div>
  );
};

export default Dashboard;