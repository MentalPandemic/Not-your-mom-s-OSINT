import React, { useEffect, useRef, useState } from 'react';
import { Network } from 'vis-network';
import { DataSet } from 'vis-data';
import { FiMaximize2, FiZoomIn, FiZoomOut, FiRefreshCw, FiLayers } from 'react-icons/fi';
import { useAppSelector } from '../hooks/useAppSelector';
import { useAppDispatch } from '../hooks/useAppDispatch';
import { setSelectedNode, setLayout } from '../store/graphSlice';
import { toggleDetailsPanel } from '../store/uiSlice';
import { transformToVisNetwork } from '../utils/graphUtils';
import clsx from 'clsx';

const GraphVisualization: React.FC = () => {
  const dispatch = useAppDispatch();
  const { nodes, edges, layout, filters } = useAppSelector(state => state.graph);
  const networkRef = useRef<HTMLDivElement>(null);
  const [network, setNetwork] = useState<Network | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedNodeTypes, setSelectedNodeTypes] = useState<string[]>([]);
  const [selectedEdgeTypes, setSelectedEdgeTypes] = useState<string[]>([]);

  useEffect(() => {
    if (!networkRef.current || nodes.length === 0) return;

    const visData = transformToVisNetwork(nodes, edges);
    const nodesDataSet = new DataSet(visData.nodes);
    const edgesDataSet = new DataSet(visData.edges);

    const options = {
      nodes: {
        shape: 'dot',
        scaling: {
          min: 10,
          max: 30,
        },
        font: {
          size: 12,
          face: 'Inter, sans-serif',
          color: '#ffffff',
        },
        borderWidth: 2,
        shadow: true,
      },
      edges: {
        width: 2,
        color: { inherit: 'from' },
        smooth: {
          type: 'continuous',
        },
        arrows: {
          to: {
            enabled: true,
            scaleFactor: 0.5,
          },
        },
        shadow: true,
      },
      physics: {
        enabled: layout === 'force-directed',
        forceAtlas2Based: {
          gravitationalConstant: -50,
          centralGravity: 0.01,
          springLength: 100,
          springConstant: 0.08,
        },
        maxVelocity: 50,
        solver: 'forceAtlas2Based',
        timestep: 0.35,
        stabilization: {
          enabled: true,
          iterations: 150,
        },
      },
      layout: layout === 'hierarchical' ? {
        hierarchical: {
          direction: 'UD',
          sortMethod: 'directed',
        },
      } : layout === 'circular' ? {
        randomSeed: 2,
      } : undefined,
      interaction: {
        hover: true,
        navigationButtons: true,
        keyboard: true,
        multiselect: true,
        tooltipDelay: 100,
      },
    };

    const networkInstance = new Network(
      networkRef.current,
      { nodes: nodesDataSet, edges: edgesDataSet },
      options
    );

    networkInstance.on('click', (params) => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const node = nodes.find(n => n.id === nodeId);
        if (node) {
          dispatch(setSelectedNode(node));
          dispatch(toggleDetailsPanel());
        }
      }
    });

    networkInstance.on('doubleClick', (params) => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
      }
    });

    networkInstance.on('hoverNode', (params) => {
      networkInstance.canvas.body.container.style.cursor = 'pointer';
    });

    networkInstance.on('blurNode', () => {
      networkInstance.canvas.body.container.style.cursor = 'default';
    });

    setNetwork(networkInstance);

    return () => {
      networkInstance.destroy();
    };
  }, [nodes, edges, layout, dispatch]);

  const handleZoomIn = () => {
    if (network) {
      const scale = network.getScale();
      network.moveTo({ scale: scale * 1.2 });
    }
  };

  const handleZoomOut = () => {
    if (network) {
      const scale = network.getScale();
      network.moveTo({ scale: scale / 1.2 });
    }
  };

  const handleFit = () => {
    if (network) {
      network.fit();
    }
  };

  const handleReset = () => {
    if (network) {
      network.fit();
      network.moveTo({ scale: 1 });
    }
  };

  const nodeTypes = Array.from(new Set(nodes.map(n => n.type)));
  const edgeTypes = Array.from(new Set(edges.map(e => e.type)));

  return (
    <div className="h-full relative">
      {/* Control Panel */}
      <div className="absolute top-4 left-4 z-10 bg-white dark:bg-dark-800 rounded-lg shadow-lg p-4 space-y-2">
        <div className="flex flex-col space-y-2">
          <button
            onClick={handleZoomIn}
            className="p-2 hover:bg-gray-100 dark:hover:bg-dark-700 rounded-lg transition-colors"
            title="Zoom In"
          >
            <FiZoomIn size={20} />
          </button>
          <button
            onClick={handleZoomOut}
            className="p-2 hover:bg-gray-100 dark:hover:bg-dark-700 rounded-lg transition-colors"
            title="Zoom Out"
          >
            <FiZoomOut size={20} />
          </button>
          <button
            onClick={handleFit}
            className="p-2 hover:bg-gray-100 dark:hover:bg-dark-700 rounded-lg transition-colors"
            title="Fit to Screen"
          >
            <FiMaximize2 size={20} />
          </button>
          <button
            onClick={handleReset}
            className="p-2 hover:bg-gray-100 dark:hover:bg-dark-700 rounded-lg transition-colors"
            title="Reset View"
          >
            <FiRefreshCw size={20} />
          </button>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="p-2 hover:bg-gray-100 dark:hover:bg-dark-700 rounded-lg transition-colors"
            title="Toggle Filters"
          >
            <FiLayers size={20} />
          </button>
        </div>
      </div>

      {/* Layout Selector */}
      <div className="absolute top-4 right-4 z-10 bg-white dark:bg-dark-800 rounded-lg shadow-lg p-4">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Layout
        </label>
        <div className="flex flex-col space-y-2">
          {(['force-directed', 'hierarchical', 'circular'] as const).map((layoutType) => (
            <button
              key={layoutType}
              onClick={() => dispatch(setLayout(layoutType))}
              className={clsx(
                'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                layout === layoutType
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 dark:bg-dark-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-dark-600'
              )}
            >
              {layoutType.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="absolute top-4 left-24 z-10 bg-white dark:bg-dark-800 rounded-lg shadow-lg p-4 max-w-xs">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Filters</h3>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Node Types
            </label>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {nodeTypes.map((type) => (
                <label key={type} className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={selectedNodeTypes.length === 0 || selectedNodeTypes.includes(type)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedNodeTypes(prev => [...prev, type]);
                      } else {
                        setSelectedNodeTypes(prev => prev.filter(t => t !== type));
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
              Edge Types
            </label>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {edgeTypes.map((type) => (
                <label key={type} className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={selectedEdgeTypes.length === 0 || selectedEdgeTypes.includes(type)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedEdgeTypes(prev => [...prev, type]);
                      } else {
                        setSelectedEdgeTypes(prev => prev.filter(t => t !== type));
                      }
                    }}
                    className="rounded text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    {type.replace(/_/g, ' ')}
                  </span>
                </label>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Statistics Panel */}
      <div className="absolute bottom-4 right-4 z-10 bg-white dark:bg-dark-800 rounded-lg shadow-lg p-4">
        <div className="text-sm space-y-1">
          <div className="flex items-center justify-between space-x-4">
            <span className="text-gray-600 dark:text-gray-400">Nodes:</span>
            <span className="font-semibold text-gray-900 dark:text-white">{nodes.length}</span>
          </div>
          <div className="flex items-center justify-between space-x-4">
            <span className="text-gray-600 dark:text-gray-400">Edges:</span>
            <span className="font-semibold text-gray-900 dark:text-white">{edges.length}</span>
          </div>
        </div>
      </div>

      {/* Graph Canvas */}
      <div ref={networkRef} className="w-full h-full bg-gray-50 dark:bg-dark-900" />

      {/* Empty State */}
      {nodes.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <p className="text-gray-600 dark:text-gray-400 text-lg mb-2">
              No graph data available
            </p>
            <p className="text-gray-500 dark:text-gray-500 text-sm">
              Perform a search to visualize connections
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default GraphVisualization;
