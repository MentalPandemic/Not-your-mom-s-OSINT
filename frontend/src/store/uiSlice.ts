import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface UIState {
  theme: 'light' | 'dark';
  sidebarCollapsed: boolean;
  detailsPanelOpen: boolean;
  activeTab: string;
  activeView: 'search' | 'results' | 'graph' | 'timeline' | 'export';
  notifications: Notification[];
}

interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
}

const initialState: UIState = {
  theme: 'dark',
  sidebarCollapsed: false,
  detailsPanelOpen: true,
  activeTab: 'all',
  activeView: 'search',
  notifications: [],
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    setTheme: (state, action: PayloadAction<'light' | 'dark'>) => {
      state.theme = action.payload;
    },
    toggleSidebar: (state) => {
      state.sidebarCollapsed = !state.sidebarCollapsed;
    },
    toggleDetailsPanel: (state) => {
      state.detailsPanelOpen = !state.detailsPanelOpen;
    },
    setActiveTab: (state, action: PayloadAction<string>) => {
      state.activeTab = action.payload;
    },
    setActiveView: (state, action: PayloadAction<UIState['activeView']>) => {
      state.activeView = action.payload;
    },
    addNotification: (state, action: PayloadAction<Notification>) => {
      state.notifications.push(action.payload);
    },
    removeNotification: (state, action: PayloadAction<string>) => {
      state.notifications = state.notifications.filter(n => n.id !== action.payload);
    },
  },
});

export const {
  setTheme,
  toggleSidebar,
  toggleDetailsPanel,
  setActiveTab,
  setActiveView,
  addNotification,
  removeNotification,
} = uiSlice.actions;

export default uiSlice.reducer;
