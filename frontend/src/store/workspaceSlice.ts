import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Workspace } from '../types';

interface WorkspaceState {
  workspaces: Workspace[];
  activeWorkspace: Workspace | null;
  loading: boolean;
}

const initialState: WorkspaceState = {
  workspaces: [],
  activeWorkspace: null,
  loading: false,
};

const workspaceSlice = createSlice({
  name: 'workspace',
  initialState,
  reducers: {
    setWorkspaces: (state, action: PayloadAction<Workspace[]>) => {
      state.workspaces = action.payload;
    },
    setActiveWorkspace: (state, action: PayloadAction<Workspace | null>) => {
      state.activeWorkspace = action.payload;
    },
    addWorkspace: (state, action: PayloadAction<Workspace>) => {
      state.workspaces.push(action.payload);
    },
    updateWorkspace: (state, action: PayloadAction<Workspace>) => {
      const index = state.workspaces.findIndex(w => w.id === action.payload.id);
      if (index !== -1) {
        state.workspaces[index] = action.payload;
      }
      if (state.activeWorkspace?.id === action.payload.id) {
        state.activeWorkspace = action.payload;
      }
    },
    deleteWorkspace: (state, action: PayloadAction<string>) => {
      state.workspaces = state.workspaces.filter(w => w.id !== action.payload);
      if (state.activeWorkspace?.id === action.payload) {
        state.activeWorkspace = null;
      }
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
  },
});

export const {
  setWorkspaces,
  setActiveWorkspace,
  addWorkspace,
  updateWorkspace,
  deleteWorkspace,
  setLoading,
} = workspaceSlice.actions;

export default workspaceSlice.reducer;
