import React from 'react';
import { FiUsers, FiTrendingUp, FiActivity } from 'react-icons/fi';
import { useAppSelector } from '../hooks/useAppSelector';
import { calculateCentrality } from '../utils/graphUtils';

const NetworkAnalysis: React.FC = () => {
  const { nodes, edges } = useAppSelector(state => state.graph);

  const stats = {
    nodeCount: nodes.length,
    edgeCount: edges.length,
    density: nodes.length > 0 ? (2 * edges.length) / (nodes.length * (nodes.length - 1)) : 0,
    avgConnections: nodes.length > 0 ? edges.length / nodes.length : 0,
  };

  const topNodes = nodes
    .map(node => ({
      ...node,
      centrality: calculateCentrality(node.id, edges),
    }))
    .sort((a, b) => b.centrality - a.centrality)
    .slice(0, 10);

  return (
    <div className="bg-white dark:bg-dark-800 rounded-lg shadow p-6">
      <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
        Network Analysis
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="p-4 bg-primary-50 dark:bg-primary-900/20 rounded-lg">
          <div className="flex items-center space-x-2 mb-2">
            <FiUsers className="text-primary-600" />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Nodes
            </span>
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {stats.nodeCount}
          </p>
        </div>

        <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
          <div className="flex items-center space-x-2 mb-2">
            <FiTrendingUp className="text-green-600" />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Connections
            </span>
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {stats.edgeCount}
          </p>
        </div>

        <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
          <div className="flex items-center space-x-2 mb-2">
            <FiActivity className="text-purple-600" />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Density
            </span>
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {(stats.density * 100).toFixed(1)}%
          </p>
        </div>
      </div>

      <div>
        <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Most Connected Nodes
        </h4>
        <div className="space-y-2">
          {topNodes.map((node, index) => (
            <div
              key={node.id}
              className="flex items-center justify-between p-3 bg-gray-50 dark:bg-dark-700 rounded-lg"
            >
              <div className="flex items-center space-x-3">
                <span className="text-lg font-bold text-gray-400">#{index + 1}</span>
                <span className="text-gray-900 dark:text-white">{node.label}</span>
                <span className="text-xs text-gray-500 capitalize">({node.type})</span>
              </div>
              <span className="text-sm font-medium text-primary-600">
                {node.centrality} connections
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default NetworkAnalysis;
