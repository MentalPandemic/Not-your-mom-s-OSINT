import React from 'react';
import { FiSearch, FiClock, FiStar, FiFolder, FiTrendingUp } from 'react-icons/fi';
import { useAppSelector } from '../hooks/useAppSelector';
import { useAppDispatch } from '../hooks/useAppDispatch';
import { setActiveView } from '../store/uiSlice';

const Sidebar: React.FC = () => {
  const dispatch = useAppDispatch();
  const { workspaces, activeWorkspace } = useAppSelector(state => state.workspace);
  const { history, savedSearches } = useAppSelector(state => state.search);

  return (
    <div className="p-4 space-y-6">
      {/* Quick Actions */}
      <div>
        <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
          Quick Actions
        </h3>
        <div className="space-y-1">
          <button
            onClick={() => dispatch(setActiveView('search'))}
            className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-700 transition-colors text-gray-700 dark:text-gray-300"
          >
            <FiSearch size={18} />
            <span>New Search</span>
          </button>
          <button
            onClick={() => dispatch(setActiveView('graph'))}
            className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-700 transition-colors text-gray-700 dark:text-gray-300"
          >
            <FiTrendingUp size={18} />
            <span>View Graph</span>
          </button>
        </div>
      </div>

      {/* Recent Searches */}
      {history.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Recent Searches
            </h3>
            <FiClock size={14} className="text-gray-400" />
          </div>
          <div className="space-y-1">
            {history.slice(0, 5).map((item, index) => (
              <button
                key={index}
                className="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-700 transition-colors text-sm text-gray-700 dark:text-gray-300 truncate"
              >
                {item}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Saved Searches */}
      {savedSearches.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Saved Searches
            </h3>
            <FiStar size={14} className="text-yellow-500" />
          </div>
          <div className="space-y-1">
            {savedSearches.slice(0, 5).map((saved, index) => (
              <button
                key={index}
                className="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-700 transition-colors text-sm text-gray-700 dark:text-gray-300 truncate"
              >
                {saved.query}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Workspaces */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
            Workspaces
          </h3>
          <FiFolder size={14} className="text-gray-400" />
        </div>
        {workspaces.length > 0 ? (
          <div className="space-y-1">
            {workspaces.map((workspace) => (
              <button
                key={workspace.id}
                className={`w-full text-left px-3 py-2 rounded-lg transition-colors text-sm ${
                  activeWorkspace?.id === workspace.id
                    ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-700'
                }`}
              >
                {workspace.name}
              </button>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500 dark:text-gray-400 px-3">
            No workspaces yet
          </p>
        )}
        <button className="w-full mt-2 px-3 py-2 text-sm text-primary-600 dark:text-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/20 rounded-lg transition-colors">
          + New Workspace
        </button>
      </div>

      {/* Tags/Categories */}
      <div>
        <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
          Tags
        </h3>
        <div className="flex flex-wrap gap-2">
          {['Investigation', 'Research', 'Personal'].map((tag) => (
            <span
              key={tag}
              className="px-2 py-1 bg-gray-100 dark:bg-dark-700 text-gray-700 dark:text-gray-300 text-xs rounded-full"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
