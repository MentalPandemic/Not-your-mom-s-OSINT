import React, { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Network,
  Node,
  Edge,
  DataSet,
  Options,
  IdType,
} from 'vis-network/standalone/esm/vis-network';
import {
  PlayIcon,
  PauseIcon,
  AdjustmentsHorizontalIcon,
  ArrowsPointingOutIcon,
  ArrowsPointingInIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
  EyeIcon,
  EyeSlashIcon,
  ArrowPathIcon,
  CpuChipIcon,
  MapIcon,
} from '@heroicons/react/24/outline';
import { useAppDispatch, useAppSelector } from '@/store';
import {
  selectGraphNodes,
  selectGraphEdges,
  selectSelectedNodes,
  selectHighlightedNodes,
  selectNetworkStats,
  selectGraphLayout,
  selectGraphFilters,
  selectGraphSettings,
  selectIsGraphLoading,
  selectIsSimulationRunning,
  selectPhysicsEnabled,
  selectGraphInteractionMode,
  setGraphData,
  setSelectedNodes,
  addSelectedNode,
  removeSelectedNode,
  clearSelectedNodes,
  setHighlightedNodes,
  togglePhysics,
  setLayout,
  updateFilters,
  updateSettings,
  setInteractionMode,
  clearGraph,
} from '@/store/slices/graphSlice';
import { setRightPanelOpen } from '@/store/slices/uiSlice';
import { EntityType, RelationshipType, GraphLayout } from '@/types';
import { debounce } from 'lodash';

interface GraphVisualizationProps {
  className?: string;
}

export const GraphVisualization: React.FC<GraphVisualizationProps> = ({ className = '' }) => {
  const dispatch = useAppDispatch();
  const nodes = useAppSelector(selectGraphNodes);
  const edges = useAppSelector(selectGraphEdges);
  const selectedNodes = useAppSelector(selectSelectedNodes);
  const highlightedNodes = useAppSelector(selectHighlightedNodes);
  const networkStats = useAppSelector(selectNetworkStats);
  const graphLayout = useAppSelector(selectGraphLayout);
  const filters = useAppSelector(selectGraphFilters);
  const settings = useAppSelector(selectGraphSettings);
  const isLoading = useAppSelector(selectIsGraphLoading);
  const isSimulationRunning = useAppSelector(selectIsSimulationRunning);
  const physicsEnabled = useAppSelector(selectPhysicsEnabled);
  const interactionMode = useAppSelector(selectGraphInteractionMode);

  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<Network | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showControls, setShowControls] = useState(true);
  const [showStats, setShowStats] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [highlightedNode, setHighlightedNode] = useState<IdType | null>(null);

  // Convert graph data to vis.js format
  const visNodes = useMemo(() => {
    return new DataSet(
      nodes.map(node => ({
        id: node.id,
        label: node.label,
        group: node.group,
        color: {
          background: node.color || getNodeColor(node.group),
          border: getNodeBorderColor(node.group),
          highlight: {
            background: '#4A90E2',
            border: '#2E5A8A',
          },
        },
        size: node.size || settings.nodeSize,
        shape: node.shape || 'dot',
        font: {
          color: '#333333',
          size: settings.fontSize,
          face: 'Inter, sans-serif',
        },
        borderWidth: node.confidence ? Math.round(node.confidence * 3) : 1,
        shadow: node.confidence && node.confidence > 0.8,
        hidden: node.hidden || false,
        x: node.x,
        y: node.y,
        ...node,
      }))
    );
  }, [nodes, settings]);

  const visEdges = useMemo(() => {
    return new DataSet(
      edges.map(edge => ({
        id: edge.id,
        from: edge.fromId,
        to: edge.toId,
        label: edge.label,
        color: {
          color: edge.color || getEdgeColor(edge.relationshipType),
          highlight: '#4A90E2',
          hover: '#4A90E2',
        },
        width: edge.width || settings.edgeWidth,
        arrows: edge.arrows || {
          to: { enabled: true, scaleFactor: 0.5 },
        },
        dashes: edge.dashes || false,
        hidden: edge.hidden || false,
        smooth: {
          enabled: true,
          type: 'continuous',
        },
        ...edge,
      }))
    );
  }, [edges, settings]);

  // Get node color based on type
  const getNodeColor = (group: string): string => {
    const colorMap: Record<string, string> = {
      identity: '#3B82F6',
      email: '#8B5CF6',
      phone: '#06B6D4',
      address: '#10B981',
      domain: '#F59E0B',
      organization: '#EF4444',
      social: '#EC4899',
      timeline: '#6366F1',
    };
    return colorMap[group] || '#6B7280';
  };

  // Get node border color
  const getNodeBorderColor = (group: string): string => {
    const colorMap: Record<string, string> = {
      identity: '#2563EB',
      email: '#7C3AED',
      phone: '#0891B2',
      address: '#059669',
      domain: '#D97706',
      organization: '#DC2626',
      social: '#DB2777',
      timeline: '#4F46E5',
    };
    return colorMap[group] || '#4B5563';
  };

  // Get edge color based on relationship type
  const getEdgeColor = (relationshipType: string): string => {
    const colorMap: Record<RelationshipType, string> = {
      LINKED_TO: '#3B82F6',
      MENTIONS: '#8B5CF6',
      POSTED_ON: '#06B6D4',
      WORKS_FOR: '#10B981',
      LIVES_AT: '#F59E0B',
      OWNS: '#EF4444',
      MANAGES: '#EC4899',
      COLLEAGUE_OF: '#6366F1',
      FAMILY_OF: '#84CC16',
      FRIEND_OF: '#F97316',
      REGISTERED_BY: '#06B6D4',
      HOSTED_ON: '#F59E0B',
      REFERENCED_BY: '#8B5CF6',
      CONNECTED_TO: '#3B82F6',
    };
    return colorMap[relationshipType as RelationshipType] || '#6B7280';
  };

  // Network options
  const networkOptions = useMemo((): Options => ({
    autoResize: true,
    physics: {
      enabled: physicsEnabled,
      stabilization: {
        enabled: true,
        iterations: 100,
        updateInterval: 25,
      },
      barnesHut: {
        gravitationalConstant: -2000,
        centralGravity: 0.3,
        springLength: 95,
        springConstant: 0.04,
        damping: 0.09,
        avoidOverlap: 0.1,
      },
    },
    layout: {
      improvedLayout: true,
      clusterThreshold: 150,
    },
    interaction: {
      hover: true,
      hoverConnectedEdges: true,
      selectConnectedEdges: false,
      tooltipDelay: 200,
      zoomView: true,
      dragView: true,
      dragNodes: interactionMode === 'select',
    },
    nodes: {
      borderWidth: 2,
      borderWidthSelected: 4,
      chosen: {
        node: function(values, id, selected, hovering) {
          values.shadow = true;
          values.shadowColor = 'rgba(0,0,0,0.3)';
          values.shadowSize = 10;
          values.shadowOffsetX = 2;
          values.shadowOffsetY = 2;
        }
      },
    },
    edges: {
      width: 2,
      widthSelectionMultiplier: 2,
      color: {
        color: '#848484',
        highlight: '#4A90E2',
        hover: '#4A90E2',
      },
      arrows: {
        to: { enabled: true, scaleFactor: 0.5 },
      },
      smooth: {
        enabled: true,
        type: 'continuous',
        roundness: 0.5,
      },
      chosen: {
        edge: function(values, id, selected, hovering) {
          values.color = '#4A90E2';
          values.width = values.width * 2;
        }
      },
    },
    configure: {
      enabled: false,
      filter: 'physics,layout',
      container: document.getElementById('network-config'),
    },
  }), [physicsEnabled, interactionMode, settings]);

  // Initialize network
  useEffect(() => {
    if (!containerRef.current) return;

    const data = {
      nodes: visNodes,
      edges: visEdges,
    };

    networkRef.current = new Network(containerRef.current, data, networkOptions);

    // Event handlers
    networkRef.current.on('click', (params) => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        if (selectedNodes.includes(nodeId as string)) {
          dispatch(removeSelectedNode(nodeId as string));
        } else {
          dispatch(addSelectedNode(nodeId as string));
        }
      } else {
        dispatch(clearSelectedNodes());
      }
    });

    networkRef.current.on('doubleClick', (params) => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        // Open node details in right panel
        dispatch(setRightPanelOpen(true));
      }
    });

    networkRef.current.on('hoverNode', (params) => {
      setHighlightedNode(params.node);
      // Highlight connected nodes and edges
      const connectedNodes = networkRef.current!.getConnectedNodes(params.node);
      const allHighlighted = [params.node, ...connectedNodes];
      dispatch(setHighlightedNodes(allHighlighted as string[]));
    });

    networkRef.current.on('blurNode', (params) => {
      setHighlightedNode(null);
      dispatch(setHighlightedNodes([]));
    });

    networkRef.current.on('stabilizationProgress', (params) => {
      const progress = (params.iterations / params.total) * 100;
      // Update stabilization progress
    });

    networkRef.current.on('stabilizationIterationsDone', () => {
      dispatch(setIsSimulationRunning(false));
    });

    networkRef.current.on('configChange', (options) => {
      // Handle configuration changes
    });

    return () => {
      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }
    };
  }, [visNodes, visEdges, networkOptions, dispatch, selectedNodes]);

  // Update network when data changes
  useEffect(() => {
    if (networkRef.current) {
      const updates = {
        nodes: visNodes,
        edges: visEdges,
      };
      networkRef.current.setData(updates);
    }
  }, [visNodes, visEdges]);

  // Handle search
  const handleSearch = useCallback(
    debounce((term: string) => {
      if (!networkRef.current || !term.trim()) {
        return;
      }

      const matchingNodes = nodes.filter(node =>
        node.label.toLowerCase().includes(term.toLowerCase()) ||
        node.id.toLowerCase().includes(term.toLowerCase())
      );

      if (matchingNodes.length > 0) {
        const nodeIds = matchingNodes.map(node => node.id);
        networkRef.current.selectNodes(nodeIds);
        
        // Focus on first matching node
        networkRef.current.focus(matchingNodes[0].id, {
          scale: 1.2,
          animation: {
            duration: 1000,
            easingFunction: 'easeInOutQuad',
          },
        });
      }
    }, 300),
    [nodes]
  );

  useEffect(() => {
    handleSearch(searchTerm);
  }, [searchTerm, handleSearch]);

  // Control functions
  const handleFit = () => {
    if (networkRef.current) {
      networkRef.current.fit({
        animation: {
          duration: 1000,
          easingFunction: 'easeInOutQuad',
        },
      });
    }
  };

  const handleZoomIn = () => {
    if (networkRef.current) {
      const scale = networkRef.current.getScale() * 1.2;
      networkRef.current.moveTo({ scale });
    }
  };

  const handleZoomOut = () => {
    if (networkRef.current) {
      const scale = networkRef.current.getScale() * 0.8;
      networkRef.current.moveTo({ scale });
    }
  };

  const handleTogglePhysics = () => {
    dispatch(togglePhysics());
    if (networkRef.current) {
      networkRef.current.setOptions({ physics: { enabled: !physicsEnabled } });
    }
  };

  const handleLayoutChange = (layout: GraphLayout) => {
    dispatch(setLayout(layout));
    if (networkRef.current) {
      const layoutOptions = getLayoutOptions(layout);
      networkRef.current.setOptions({ layout: layoutOptions });
    }
  };

  const getLayoutOptions = (layout: GraphLayout) => {
    switch (layout) {
      case GraphLayout.HIERARCHICAL:
        return {
          hierarchical: {
            enabled: true,
            levelSeparation: 150,
            nodeSpacing: 100,
            treeSpacing: 200,
            blockShifting: true,
            edgeMinimization: true,
            parentCentralization: true,
            direction: 'UD',
            sortMethod: 'directed',
          },
        };
      case GraphLayout.CIRCULAR:
        return {
          hierarchical: {
            enabled: false,
          },
        };
      default:
        return {
          hierarchical: {
            enabled: false,
          },
        };
    }
  };

  const handleClearGraph = () => {
    dispatch(clearGraph());
  };

  // Node type filtering
  const toggleNodeTypeFilter = (nodeType: EntityType) => {
    const currentTypes = filters.nodeTypes;
    const newTypes = currentTypes.includes(nodeType)
      ? currentTypes.filter(t => t !== nodeType)
      : [...currentTypes, nodeType];
    
    dispatch(updateFilters({ nodeTypes: newTypes }));
  };

  if (isLoading) {
    return (
      <div className={`flex items-center justify-center h-full ${className}`}>
        <div className="text-center">
          <div className="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
            Loading Network Graph
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Processing nodes and relationships...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={`relative h-full bg-gray-50 dark:bg-gray-900 ${className}`}>
      {/* Network container */}
      <div 
        ref={containerRef} 
        className={`w-full h-full ${isFullscreen ? 'fixed inset-0 z-50' : ''}`}
      />

      {/* Controls overlay */}
      <AnimatePresence>
        {showControls && (
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="absolute top-4 left-4 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-4 space-y-4"
          >
            {/* Search */}
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search nodes..."
                className="pl-10 pr-4 py-2 w-64 text-sm border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
              />
            </div>

            {/* Layout controls */}
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">Layout</h4>
              <div className="grid grid-cols-2 gap-2">
                {Object.values(GraphLayout).map((layout) => (
                  <button
                    key={layout}
                    onClick={() => handleLayoutChange(layout)}
                    className={`px-3 py-2 text-xs rounded-lg transition-colors ${
                      graphLayout === layout
                        ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                    }`}
                  >
                    {layout.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </button>
                ))}
              </div>
            </div>

            {/* Node type filters */}
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">Node Types</h4>
              <div className="space-y-1">
                {Object.values(EntityType).map((nodeType) => (
                  <label key={nodeType} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={!filters.nodeTypes.includes(nodeType)}
                      onChange={() => toggleNodeTypeFilter(nodeType)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-xs text-gray-600 dark:text-gray-400 capitalize">
                      {nodeType}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            {/* Physics control */}
            <button
              onClick={handleTogglePhysics}
              className={`flex items-center space-x-2 px-3 py-2 text-xs rounded-lg transition-colors ${
                physicsEnabled
                  ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
              }`}
            >
              {physicsEnabled ? (
                <PauseIcon className="h-4 w-4" />
              ) : (
                <PlayIcon className="h-4 w-4" />
              )}
              <span>{physicsEnabled ? 'Pause' : 'Start'} Physics</span>
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* View controls */}
      <div className="absolute top-4 right-4 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-2">
        <div className="flex items-center space-x-2">
          <button
            onClick={handleFit}
            className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
            title="Fit to view"
          >
            <ArrowsPointingOutIcon className="h-4 w-4" />
          </button>
          <button
            onClick={handleZoomIn}
            className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
            title="Zoom in"
          >
            <MagnifyingGlassIcon className="h-4 w-4" />
          </button>
          <button
            onClick={handleZoomOut}
            className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
            title="Zoom out"
          >
            <ArrowPathIcon className="h-4 w-4" />
          </button>
          <button
            onClick={() => setShowControls(!showControls)}
            className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
            title="Toggle controls"
          >
            <Cog6ToothIcon className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Stats panel */}
      <AnimatePresence>
        {showStats && networkStats && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="absolute bottom-4 right-4 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-4 min-w-64"
          >
            <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">
              Network Statistics
            </h4>
            <div className="space-y-2 text-xs text-gray-600 dark:text-gray-400">
              <div className="flex justify-between">
                <span>Nodes:</span>
                <span className="font-medium">{networkStats.nodeCount}</span>
              </div>
              <div className="flex justify-between">
                <span>Edges:</span>
                <span className="font-medium">{networkStats.edgeCount}</span>
              </div>
              <div className="flex justify-between">
                <span>Density:</span>
                <span className="font-medium">{networkStats.density.toFixed(3)}</span>
              </div>
              <div className="flex justify-between">
                <span>Avg Clustering:</span>
                <span className="font-medium">{networkStats.averageClustering.toFixed(3)}</span>
              </div>
              <div className="flex justify-between">
                <span>Communities:</span>
                <span className="font-medium">{networkStats.communityCount}</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Status bar */}
      <div className="absolute bottom-4 left-4 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 px-4 py-2">
        <div className="flex items-center space-x-4 text-xs text-gray-600 dark:text-gray-400">
          <span>{nodes.length} nodes</span>
          <span>•</span>
          <span>{edges.length} edges</span>
          <span>•</span>
          <span>{selectedNodes.length} selected</span>
          {isSimulationRunning && (
            <>
              <span>•</span>
              <span className="text-blue-600 dark:text-blue-400">Stabilizing...</span>
            </>
          )}
          <button
            onClick={() => setShowStats(!showStats)}
            className="ml-4 p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
          >
            <ChartBarIcon className="h-3 w-3" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default GraphVisualization;