import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { 
  GraphNode, 
  GraphEdge, 
  NetworkStats, 
  GraphLayout,
  EntityType,
  RelationshipType 
} from '@/types';

interface GraphState {
  nodes: GraphNode[];
  edges: GraphEdge[];
  selectedNodes: string[];
  highlightedNodes: string[];
  networkStats: NetworkStats | null;
  layout: GraphLayout;
  isLoading: boolean;
  isSimulationRunning: boolean;
  physicsEnabled: boolean;
  zoomLevel: number;
  centerPosition: { x: number; y: number };
  filters: {
    nodeTypes: EntityType[];
    edgeTypes: RelationshipType[];
    minConfidence: number;
    showLabels: boolean;
    showEdges: boolean;
  };
  settings: {
    nodeSize: number;
    edgeWidth: number;
    fontSize: number;
    spacing: number;
    colorScheme: 'default' | 'social' | 'security' | 'business';
  };
  interactionMode: 'view' | 'select' | 'pan' | 'zoom';
  lastLayoutUpdate: Date | null;
}

const initialState: GraphState = {
  nodes: [],
  edges: [],
  selectedNodes: [],
  highlightedNodes: [],
  networkStats: null,
  layout: GraphLayout.FORCE_DIRECTED,
  isLoading: false,
  isSimulationRunning: false,
  physicsEnabled: true,
  zoomLevel: 1,
  centerPosition: { x: 0, y: 0 },
  filters: {
    nodeTypes: [],
    edgeTypes: [],
    minConfidence: 0,
    showLabels: true,
    showEdges: true,
  },
  settings: {
    nodeSize: 20,
    edgeWidth: 2,
    fontSize: 12,
    spacing: 100,
    colorScheme: 'default',
  },
  interactionMode: 'view',
  lastLayoutUpdate: null,
};

const graphSlice = createSlice({
  name: 'graph',
  initialState,
  reducers: {
    setGraphData: (state, action: PayloadAction<{ nodes: GraphNode[]; edges: GraphEdge[] }>) => {
      state.nodes = action.payload.nodes;
      state.edges = action.payload.edges;
      state.isLoading = false;
      state.lastLayoutUpdate = new Date();
    },
    
    updateNodePositions: (state, action: PayloadAction<{ nodeId: string; x: number; y: number }[]>) => {
      action.payload.forEach(({ nodeId, x, y }) => {
        const node = state.nodes.find(n => n.id === nodeId);
        if (node) {
          node.x = x;
          node.y = y;
        }
      });
      state.lastLayoutUpdate = new Date();
    },
    
    setSelectedNodes: (state, action: PayloadAction<string[]>) => {
      state.selectedNodes = action.payload;
    },
    
    addSelectedNode: (state, action: PayloadAction<string>) => {
      if (!state.selectedNodes.includes(action.payload)) {
        state.selectedNodes.push(action.payload);
      }
    },
    
    removeSelectedNode: (state, action: PayloadAction<string>) => {
      state.selectedNodes = state.selectedNodes.filter(id => id !== action.payload);
    },
    
    clearSelectedNodes: (state) => {
      state.selectedNodes = [];
    },
    
    setHighlightedNodes: (state, action: PayloadAction<string[]>) => {
      state.highlightedNodes = action.payload;
    },
    
    highlightNode: (state, action: PayloadAction<string>) => {
      if (!state.highlightedNodes.includes(action.payload)) {
        state.highlightedNodes.push(action.payload);
      }
    },
    
    unhighlightNode: (state, action: PayloadAction<string>) => {
      state.highlightedNodes = state.highlightedNodes.filter(id => id !== action.payload);
    },
    
    clearHighlightedNodes: (state) => {
      state.highlightedNodes = [];
    },
    
    setNetworkStats: (state, action: PayloadAction<NetworkStats>) => {
      state.networkStats = action.payload;
    },
    
    setLayout: (state, action: PayloadAction<GraphLayout>) => {
      state.layout = action.payload;
      state.lastLayoutUpdate = new Date();
    },
    
    setIsLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    
    setIsSimulationRunning: (state, action: PayloadAction<boolean>) => {
      state.isSimulationRunning = action.payload;
    },
    
    togglePhysics: (state) => {
      state.physicsEnabled = !state.physicsEnabled;
    },
    
    setPhysicsEnabled: (state, action: PayloadAction<boolean>) => {
      state.physicsEnabled = action.payload;
    },
    
    setZoomLevel: (state, action: PayloadAction<number>) => {
      state.zoomLevel = Math.max(0.1, Math.min(5, action.payload));
    },
    
    setCenterPosition: (state, action: PayloadAction<{ x: number; y: number }>) => {
      state.centerPosition = action.payload;
    },
    
    updateFilters: (state, action: PayloadAction<Partial<GraphState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    
    updateSettings: (state, action: PayloadAction<Partial<GraphState['settings']>>) => {
      state.settings = { ...state.settings, ...action.payload };
    },
    
    setInteractionMode: (state, action: PayloadAction<GraphState['interactionMode']>) => {
      state.interactionMode = action.payload;
    },
    
    // Add nodes to graph
    addNodes: (state, action: PayloadAction<GraphNode[]>) => {
      state.nodes.push(...action.payload);
      state.lastLayoutUpdate = new Date();
    },
    
    // Remove nodes from graph
    removeNodes: (state, action: PayloadAction<string[]>) => {
      const nodeIdsToRemove = new Set(action.payload);
      state.nodes = state.nodes.filter(node => !nodeIdsToRemove.has(node.id));
      state.edges = state.edges.filter(edge => 
        !nodeIdsToRemove.has(edge.fromId) && !nodeIdsToRemove.has(edge.toId)
      );
      state.selectedNodes = state.selectedNodes.filter(id => !nodeIdsToRemove.has(id));
      state.highlightedNodes = state.highlightedNodes.filter(id => !nodeIdsToRemove.has(id));
      state.lastLayoutUpdate = new Date();
    },
    
    // Update node properties
    updateNode: (state, action: PayloadAction<{ id: string; updates: Partial<GraphNode> }>) => {
      const { id, updates } = action.payload;
      const nodeIndex = state.nodes.findIndex(node => node.id === id);
      if (nodeIndex !== -1) {
        state.nodes[nodeIndex] = { ...state.nodes[nodeIndex], ...updates };
        state.lastLayoutUpdate = new Date();
      }
    },
    
    // Add edges to graph
    addEdges: (state, action: PayloadAction<GraphEdge[]>) => {
      state.edges.push(...action.payload);
      state.lastLayoutUpdate = new Date();
    },
    
    // Remove edges from graph
    removeEdges: (state, action: PayloadAction<string[]>) => {
      const edgeIdsToRemove = new Set(action.payload);
      state.edges = state.edges.filter(edge => !edgeIdsToRemove.has(edge.id));
      state.lastLayoutUpdate = new Date();
    },
    
    // Update edge properties
    updateEdge: (state, action: PayloadAction<{ id: string; updates: Partial<GraphEdge> }>) => {
      const { id, updates } = action.payload;
      const edgeIndex = state.edges.findIndex(edge => edge.id === id);
      if (edgeIndex !== -1) {
        state.edges[edgeIndex] = { ...state.edges[edgeIndex], ...updates };
        state.lastLayoutUpdate = new Date();
      }
    },
    
    // Clear all graph data
    clearGraph: (state) => {
      state.nodes = [];
      state.edges = [];
      state.selectedNodes = [];
      state.highlightedNodes = [];
      state.networkStats = null;
      state.lastLayoutUpdate = null;
    },
    
    // Expand node (add related nodes and edges)
    expandNode: (state, action: PayloadAction<{ nodeId: string; relatedNodes: GraphNode[]; relatedEdges: GraphEdge[] }>) => {
      const { nodeId, relatedNodes, relatedEdges } = action.payload;
      
      // Add new nodes
      relatedNodes.forEach(newNode => {
        const existingNode = state.nodes.find(n => n.id === newNode.id);
        if (!existingNode) {
          state.nodes.push(newNode);
        }
      });
      
      // Add new edges
      relatedEdges.forEach(newEdge => {
        const existingEdge = state.edges.find(e => e.id === newEdge.id);
        if (!existingEdge) {
          state.edges.push(newEdge);
        }
      });
      
      state.lastLayoutUpdate = new Date();
    },
    
    // Collapse node (remove expanded nodes and edges)
    collapseNode: (state, action: PayloadAction<{ nodeId: string; depth?: number }>) => {
      const { nodeId, depth = 1 } = action.payload;
      
      if (depth === 1) {
        // Remove direct neighbors
        const connectedEdges = state.edges.filter(edge => 
          edge.fromId === nodeId || edge.toId === nodeId
        );
        
        const connectedNodeIds = new Set<string>();
        connectedEdges.forEach(edge => {
          connectedNodeIds.add(edge.fromId === nodeId ? edge.toId : edge.fromId);
        });
        
        // Remove edges first
        connectedEdges.forEach(edge => {
          state.edges = state.edges.filter(e => e.id !== edge.id);
        });
        
        // Remove connected nodes
        connectedNodeIds.forEach(connectedId => {
          state.nodes = state.nodes.filter(node => node.id !== connectedId);
        });
      }
      
      state.lastLayoutUpdate = new Date();
    },
    
    // Reset to original state
    resetGraph: (state) => {
      state.nodes = [];
      state.edges = [];
      state.selectedNodes = [];
      state.highlightedNodes = [];
      state.networkStats = null;
      state.lastLayoutUpdate = null;
      state.zoomLevel = 1;
      state.centerPosition = { x: 0, y: 0 };
    },
  },
});

export const {
  setGraphData,
  updateNodePositions,
  setSelectedNodes,
  addSelectedNode,
  removeSelectedNode,
  clearSelectedNodes,
  setHighlightedNodes,
  highlightNode,
  unhighlightNode,
  clearHighlightedNodes,
  setNetworkStats,
  setLayout,
  setIsLoading,
  setIsSimulationRunning,
  togglePhysics,
  setPhysicsEnabled,
  setZoomLevel,
  setCenterPosition,
  updateFilters,
  updateSettings,
  setInteractionMode,
  addNodes,
  removeNodes,
  updateNode,
  addEdges,
  removeEdges,
  updateEdge,
  clearGraph,
  expandNode,
  collapseNode,
  resetGraph,
} = graphSlice.actions;

export default graphSlice.reducer;

// Selectors
export const selectGraphNodes = (state: { graph: GraphState }) => state.graph.nodes;
export const selectGraphEdges = (state: { graph: GraphState }) => state.graph.edges;
export const selectSelectedNodes = (state: { graph: GraphState }) => state.graph.selectedNodes;
export const selectHighlightedNodes = (state: { graph: GraphState }) => state.graph.highlightedNodes;
export const selectNetworkStats = (state: { graph: GraphState }) => state.graph.networkStats;
export const selectGraphLayout = (state: { graph: GraphState }) => state.graph.layout;
export const selectGraphFilters = (state: { graph: GraphState }) => state.graph.filters;
export const selectGraphSettings = (state: { graph: GraphState }) => state.graph.settings;
export const selectIsGraphLoading = (state: { graph: GraphState }) => state.graph.isLoading;
export const selectIsSimulationRunning = (state: { graph: GraphState }) => state.graph.isSimulationRunning;
export const selectPhysicsEnabled = (state: { graph: GraphState }) => state.graph.physicsEnabled;
export const selectGraphInteractionMode = (state: { graph: GraphState }) => state.graph.interactionMode;