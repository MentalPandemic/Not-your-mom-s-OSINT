import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Workspace, SavedGraph, Note } from '@/types';

interface WorkspaceState {
  currentWorkspace: Workspace | null;
  workspaces: Workspace[];
  isLoading: boolean;
  error: string | null;
  activeTab: string;
  sidebarCollapsed: boolean;
  notes: Note[];
  isEditingNote: string | null;
  recentActivity: {
    action: string;
    timestamp: Date;
    entityId?: string;
  }[];
}

const initialState: WorkspaceState = {
  currentWorkspace: null,
  workspaces: [],
  isLoading: false,
  error: null,
  activeTab: 'overview',
  sidebarCollapsed: false,
  notes: [],
  isEditingNote: null,
  recentActivity: [],
};

const workspaceSlice = createSlice({
  name: 'workspace',
  initialState,
  reducers: {
    setCurrentWorkspace: (state, action: PayloadAction<Workspace>) => {
      state.currentWorkspace = action.payload;
      state.error = null;
    },
    
    setWorkspaces: (state, action: PayloadAction<Workspace[]>) => {
      state.workspaces = action.payload;
    },
    
    createWorkspace: (state, action: PayloadAction<Omit<Workspace, 'id' | 'createdAt' | 'updatedAt'>>) => {
      const newWorkspace: Workspace = {
        ...action.payload,
        id: `ws-${Date.now()}`,
        createdAt: new Date(),
        updatedAt: new Date(),
      };
      state.workspaces.push(newWorkspace);
      state.currentWorkspace = newWorkspace;
    },
    
    updateWorkspace: (state, action: PayloadAction<{ id: string; updates: Partial<Workspace> }>) => {
      const { id, updates } = action.payload;
      const workspaceIndex = state.workspaces.findIndex(ws => ws.id === id);
      if (workspaceIndex !== -1) {
        state.workspaces[workspaceIndex] = {
          ...state.workspaces[workspaceIndex],
          ...updates,
          updatedAt: new Date(),
        };
        
        if (state.currentWorkspace?.id === id) {
          state.currentWorkspace = state.workspaces[workspaceIndex];
        }
      }
    },
    
    deleteWorkspace: (state, action: PayloadAction<string>) => {
      const workspaceId = action.payload;
      state.workspaces = state.workspaces.filter(ws => ws.id !== workspaceId);
      
      if (state.currentWorkspace?.id === workspaceId) {
        state.currentWorkspace = null;
      }
    },
    
    setActiveTab: (state, action: PayloadAction<string>) => {
      state.activeTab = action.payload;
    },
    
    toggleSidebar: (state) => {
      state.sidebarCollapsed = !state.sidebarCollapsed;
    },
    
    setSidebarCollapsed: (state, action: PayloadAction<boolean>) => {
      state.sidebarCollapsed = action.payload;
    },
    
    // Notes management
    addNote: (state, action: PayloadAction<Omit<Note, 'id' | 'createdAt' | 'updatedAt'>>) => {
      const newNote: Note = {
        ...action.payload,
        id: `note-${Date.now()}`,
        createdAt: new Date(),
        updatedAt: new Date(),
      };
      state.notes.push(newNote);
    },
    
    updateNote: (state, action: PayloadAction<{ id: string; updates: Partial<Note> }>) => {
      const { id, updates } = action.payload;
      const noteIndex = state.notes.findIndex(note => note.id === id);
      if (noteIndex !== -1) {
        state.notes[noteIndex] = {
          ...state.notes[noteIndex],
          ...updates,
          updatedAt: new Date(),
        };
      }
    },
    
    deleteNote: (state, action: PayloadAction<string>) => {
      state.notes = state.notes.filter(note => note.id !== action.payload);
      if (state.isEditingNote === action.payload) {
        state.isEditingNote = null;
      }
    },
    
    setEditingNote: (state, action: PayloadAction<string | null>) => {
      state.isEditingNote = action.payload;
    },
    
    // Activity tracking
    addActivity: (state, action: PayloadAction<{
      action: string;
      timestamp: Date;
      entityId?: string;
    }>) => {
      state.recentActivity.unshift(action.payload);
      // Keep only last 50 activities
      state.recentActivity = state.recentActivity.slice(0, 50);
    },
    
    clearActivity: (state) => {
      state.recentActivity = [];
    },
    
    // Graph management within workspace
    addSavedGraph: (state, action: PayloadAction<Omit<SavedGraph, 'id' | 'createdAt' | 'lastModified'>>) => {
      if (state.currentWorkspace) {
        const newGraph: SavedGraph = {
          ...action.payload,
          id: `graph-${Date.now()}`,
          createdAt: new Date(),
          lastModified: new Date(),
        };
        state.currentWorkspace.graphs.push(newGraph);
        state.currentWorkspace.updatedAt = new Date();
      }
    },
    
    updateSavedGraph: (state, action: PayloadAction<{ id: string; updates: Partial<SavedGraph> }>) => {
      if (state.currentWorkspace) {
        const { id, updates } = action.payload;
        const graphIndex = state.currentWorkspace.graphs.findIndex(g => g.id === id);
        if (graphIndex !== -1) {
          state.currentWorkspace.graphs[graphIndex] = {
            ...state.currentWorkspace.graphs[graphIndex],
            ...updates,
            lastModified: new Date(),
          };
          state.currentWorkspace.updatedAt = new Date();
        }
      }
    },
    
    deleteSavedGraph: (state, action: PayloadAction<string>) => {
      if (state.currentWorkspace) {
        state.currentWorkspace.graphs = state.currentWorkspace.graphs.filter(g => g.id !== action.payload);
        state.currentWorkspace.updatedAt = new Date();
      }
    },
    
    // Workspace sharing
    shareWorkspace: (state, action: PayloadAction<{ workspaceId: string; collaborators: string[] }>) => {
      const { workspaceId, collaborators } = action.payload;
      const workspace = state.workspaces.find(ws => ws.id === workspaceId);
      if (workspace) {
        workspace.isShared = true;
        workspace.collaborators = collaborators;
        workspace.updatedAt = new Date();
      }
    },
    
    unshareWorkspace: (state, action: PayloadAction<string>) => {
      const workspaceId = action.payload;
      const workspace = state.workspaces.find(ws => ws.id === workspaceId);
      if (workspace) {
        workspace.isShared = false;
        workspace.collaborators = [];
        workspace.updatedAt = new Date();
      }
    },
    
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
      if (action.payload) {
        state.error = null;
      }
    },
    
    setError: (state, action: PayloadAction<string>) => {
      state.error = action.payload;
      state.isLoading = false;
    },
    
    clearError: (state) => {
      state.error = null;
    },
  },
});

export const {
  setCurrentWorkspace,
  setWorkspaces,
  createWorkspace,
  updateWorkspace,
  deleteWorkspace,
  setActiveTab,
  toggleSidebar,
  setSidebarCollapsed,
  addNote,
  updateNote,
  deleteNote,
  setEditingNote,
  addActivity,
  clearActivity,
  addSavedGraph,
  updateSavedGraph,
  deleteSavedGraph,
  shareWorkspace,
  unshareWorkspace,
  setLoading,
  setError,
  clearError,
} = workspaceSlice.actions;

export default workspaceSlice.reducer;

// Selectors
export const selectCurrentWorkspace = (state: { workspace: WorkspaceState }) => state.workspace.currentWorkspace;
export const selectWorkspaces = (state: { workspace: WorkspaceState }) => state.workspace.workspaces;
export const selectWorkspaceActiveTab = (state: { workspace: WorkspaceState }) => state.workspace.activeTab;
export const selectSidebarCollapsed = (state: { workspace: WorkspaceState }) => state.workspace.sidebarCollapsed;
export const selectNotes = (state: { workspace: WorkspaceState }) => state.workspace.notes;
export const selectEditingNote = (state: { workspace: WorkspaceState }) => state.workspace.isEditingNote;
export const selectRecentActivity = (state: { workspace: WorkspaceState }) => state.workspace.recentActivity;
export const selectWorkspaceLoading = (state: { workspace: WorkspaceState }) => state.workspace.isLoading;
export const selectWorkspaceError = (state: { workspace: WorkspaceState }) => state.workspace.error;