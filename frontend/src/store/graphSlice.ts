import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { GraphNode, GraphEdge, GraphData } from '../types';

interface GraphState {
  nodes: GraphNode[];
  edges: GraphEdge[];
  selectedNode: GraphNode | null;
  highlightedNodes: string[];
  layout: 'force-directed' | 'hierarchical' | 'circular';
  filters: {
    nodeTypes: string[];
    edgeTypes: string[];
  };
  loading: boolean;
}

const initialState: GraphState = {
  nodes: [],
  edges: [],
  selectedNode: null,
  highlightedNodes: [],
  layout: 'force-directed',
  filters: {
    nodeTypes: [],
    edgeTypes: [],
  },
  loading: false,
};

const graphSlice = createSlice({
  name: 'graph',
  initialState,
  reducers: {
    setGraphData: (state, action: PayloadAction<GraphData>) => {
      state.nodes = action.payload.nodes;
      state.edges = action.payload.edges;
    },
    addNode: (state, action: PayloadAction<GraphNode>) => {
      state.nodes.push(action.payload);
    },
    addEdge: (state, action: PayloadAction<GraphEdge>) => {
      state.edges.push(action.payload);
    },
    setSelectedNode: (state, action: PayloadAction<GraphNode | null>) => {
      state.selectedNode = action.payload;
    },
    setHighlightedNodes: (state, action: PayloadAction<string[]>) => {
      state.highlightedNodes = action.payload;
    },
    setLayout: (state, action: PayloadAction<'force-directed' | 'hierarchical' | 'circular'>) => {
      state.layout = action.payload;
    },
    setNodeTypeFilters: (state, action: PayloadAction<string[]>) => {
      state.filters.nodeTypes = action.payload;
    },
    setEdgeTypeFilters: (state, action: PayloadAction<string[]>) => {
      state.filters.edgeTypes = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    clearGraph: (state) => {
      state.nodes = [];
      state.edges = [];
      state.selectedNode = null;
      state.highlightedNodes = [];
    },
  },
});

export const {
  setGraphData,
  addNode,
  addEdge,
  setSelectedNode,
  setHighlightedNodes,
  setLayout,
  setNodeTypeFilters,
  setEdgeTypeFilters,
  setLoading,
  clearGraph,
} = graphSlice.actions;

export default graphSlice.reducer;
