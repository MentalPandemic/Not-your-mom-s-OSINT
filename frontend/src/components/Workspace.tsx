import React, { useState } from 'react';
import { FiPlus, FiTrash2, FiEdit, FiSave } from 'react-icons/fi';
import { useAppSelector } from '../hooks/useAppSelector';
import { useAppDispatch } from '../hooks/useAppDispatch';
import { addWorkspace, updateWorkspace, deleteWorkspace, setActiveWorkspace } from '../store/workspaceSlice';
import { Workspace as WorkspaceType } from '../types';
import toast from 'react-hot-toast';
import clsx from 'clsx';

const Workspace: React.FC = () => {
  const dispatch = useAppDispatch();
  const { workspaces, activeWorkspace } = useAppSelector(state => state.workspace);
  const [isCreating, setIsCreating] = useState(false);
  const [newWorkspaceName, setNewWorkspaceName] = useState('');
  const [newWorkspaceDesc, setNewWorkspaceDesc] = useState('');

  const handleCreateWorkspace = () => {
    if (!newWorkspaceName.trim()) {
      toast.error('Workspace name is required');
      return;
    }

    const workspace: WorkspaceType = {
      id: Date.now().toString(),
      name: newWorkspaceName,
      description: newWorkspaceDesc,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      queries: [],
      results: [],
      graphData: { nodes: [], edges: [] },
      notes: '',
      tags: [],
    };

    dispatch(addWorkspace(workspace));
    setIsCreating(false);
    setNewWorkspaceName('');
    setNewWorkspaceDesc('');
    toast.success('Workspace created successfully');
  };

  const handleDeleteWorkspace = (id: string) => {
    if (window.confirm('Are you sure you want to delete this workspace?')) {
      dispatch(deleteWorkspace(id));
      toast.success('Workspace deleted');
    }
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Workspaces
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            Organize and manage your investigations
          </p>
        </div>
        <button
          onClick={() => setIsCreating(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <FiPlus />
          <span>New Workspace</span>
        </button>
      </div>

      {/* Create Workspace Modal */}
      {isCreating && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white dark:bg-dark-800 rounded-lg shadow-xl max-w-md w-full p-6">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              Create New Workspace
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Workspace Name
                </label>
                <input
                  type="text"
                  value={newWorkspaceName}
                  onChange={(e) => setNewWorkspaceName(e.target.value)}
                  placeholder="Enter workspace name"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-lg bg-white dark:bg-dark-700 text-gray-900 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Description (Optional)
                </label>
                <textarea
                  value={newWorkspaceDesc}
                  onChange={(e) => setNewWorkspaceDesc(e.target.value)}
                  placeholder="Enter description"
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-lg bg-white dark:bg-dark-700 text-gray-900 dark:text-white"
                />
              </div>
            </div>

            <div className="flex items-center justify-end space-x-3 mt-6">
              <button
                onClick={() => {
                  setIsCreating(false);
                  setNewWorkspaceName('');
                  setNewWorkspaceDesc('');
                }}
                className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-700 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateWorkspace}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Workspaces Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {workspaces.map((workspace) => (
          <div
            key={workspace.id}
            className={clsx(
              'bg-white dark:bg-dark-800 rounded-lg shadow p-6 transition-all cursor-pointer',
              activeWorkspace?.id === workspace.id
                ? 'ring-2 ring-primary-600'
                : 'hover:shadow-lg'
            )}
            onClick={() => dispatch(setActiveWorkspace(workspace))}
          >
            <div className="flex items-start justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {workspace.name}
              </h3>
              <div className="flex items-center space-x-2">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                  }}
                  className="p-1 text-gray-500 hover:text-primary-600 transition-colors"
                >
                  <FiEdit size={16} />
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteWorkspace(workspace.id);
                  }}
                  className="p-1 text-gray-500 hover:text-red-600 transition-colors"
                >
                  <FiTrash2 size={16} />
                </button>
              </div>
            </div>

            {workspace.description && (
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                {workspace.description}
              </p>
            )}

            <div className="flex items-center justify-between text-sm">
              <div className="text-gray-500 dark:text-gray-400">
                {workspace.queries.length} queries
              </div>
              <div className="text-gray-500 dark:text-gray-400">
                {new Date(workspace.updatedAt).toLocaleDateString()}
              </div>
            </div>

            {workspace.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-4">
                {workspace.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-1 bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300 text-xs rounded-full"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {workspaces.length === 0 && !isCreating && (
        <div className="text-center py-12">
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            No workspaces yet. Create one to get started!
          </p>
        </div>
      )}
    </div>
  );
};

export default Workspace;
