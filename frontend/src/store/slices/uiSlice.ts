import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface UIState {
  theme: 'light' | 'dark' | 'auto';
  sidebarCollapsed: boolean;
  sidebarWidth: number;
  rightPanelOpen: boolean;
  rightPanelWidth: number;
  activeView: 'search' | 'results' | 'graph' | 'timeline' | 'export' | 'settings';
  modals: {
    search: boolean;
    export: boolean;
    settings: boolean;
    identity: boolean;
    confirm: boolean;
  };
  notifications: Notification[];
  breadcrumbs: Breadcrumb[];
  loading: {
    global: boolean;
    search: boolean;
    graph: boolean;
    export: boolean;
  };
  preferences: {
    compactMode: boolean;
    showConfidenceScores: boolean;
    autoExpandNodes: boolean;
    graphAnimations: boolean;
    mapAnimations: boolean;
  };
  layout: {
    fullscreen: boolean;
    floatingPanels: boolean;
    panelPositions: Record<string, { x: number; y: number; width: number; height: number }>;
  };
}

interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
  actions?: {
    label: string;
    action: string;
  }[];
  timestamp: Date;
}

interface Breadcrumb {
  label: string;
  path: string;
  icon?: string;
}

const initialState: UIState = {
  theme: 'light',
  sidebarCollapsed: false,
  sidebarWidth: 300,
  rightPanelOpen: false,
  rightPanelWidth: 350,
  activeView: 'search',
  modals: {
    search: false,
    export: false,
    settings: false,
    identity: false,
    confirm: false,
  },
  notifications: [],
  breadcrumbs: [{ label: 'Dashboard', path: '/' }],
  loading: {
    global: false,
    search: false,
    graph: false,
    export: false,
  },
  preferences: {
    compactMode: false,
    showConfidenceScores: true,
    autoExpandNodes: false,
    graphAnimations: true,
    mapAnimations: true,
  },
  layout: {
    fullscreen: false,
    floatingPanels: false,
    panelPositions: {},
  },
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    setTheme: (state, action: PayloadAction<'light' | 'dark' | 'auto'>) => {
      state.theme = action.payload;
    },
    
    toggleTheme: (state) => {
      if (state.theme === 'light') {
        state.theme = 'dark';
      } else if (state.theme === 'dark') {
        state.theme = 'auto';
      } else {
        state.theme = 'light';
      }
    },
    
    setSidebarCollapsed: (state, action: PayloadAction<boolean>) => {
      state.sidebarCollapsed = action.payload;
    },
    
    toggleSidebar: (state) => {
      state.sidebarCollapsed = !state.sidebarCollapsed;
    },
    
    setSidebarWidth: (state, action: PayloadAction<number>) => {
      state.sidebarWidth = Math.max(200, Math.min(600, action.payload));
    },
    
    setRightPanelOpen: (state, action: PayloadAction<boolean>) => {
      state.rightPanelOpen = action.payload;
    },
    
    toggleRightPanel: (state) => {
      state.rightPanelOpen = !state.rightPanelOpen;
    },
    
    setRightPanelWidth: (state, action: PayloadAction<number>) => {
      state.rightPanelWidth = Math.max(250, Math.min(800, action.payload));
    },
    
    setActiveView: (state, action: PayloadAction<UIState['activeView']>) => {
      state.activeView = action.payload;
    },
    
    openModal: (state, action: PayloadAction<keyof UIState['modals']>) => {
      state.modals[action.payload] = true;
    },
    
    closeModal: (state, action: PayloadAction<keyof UIState['modals']>) => {
      state.modals[action.payload] = false;
    },
    
    closeAllModals: (state) => {
      Object.keys(state.modals).forEach(key => {
        state.modals[key as keyof UIState['modals']] = false;
      });
    },
    
    addNotification: (state, action: PayloadAction<Omit<Notification, 'id' | 'timestamp'>>) => {
      const notification: Notification = {
        ...action.payload,
        id: `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        timestamp: new Date(),
      };
      state.notifications.unshift(notification);
      
      // Auto-remove notifications after duration
      if (notification.duration && notification.duration > 0) {
        setTimeout(() => {
          const index = state.notifications.findIndex(n => n.id === notification.id);
          if (index >= 0) {
            state.notifications.splice(index, 1);
          }
        }, notification.duration * 1000);
      }
    },
    
    removeNotification: (state, action: PayloadAction<string>) => {
      state.notifications = state.notifications.filter(n => n.id !== action.payload);
    },
    
    clearNotifications: (state) => {
      state.notifications = [];
    },
    
    setBreadcrumbs: (state, action: PayloadAction<Breadcrumb[]>) => {
      state.breadcrumbs = action.payload;
    },
    
    addBreadcrumb: (state, action: PayloadAction<Breadcrumb>) => {
      const existingIndex = state.breadcrumbs.findIndex(b => b.path === action.payload.path);
      if (existingIndex >= 0) {
        state.breadcrumbs = [...state.breadcrumbs.slice(0, existingIndex + 1)];
      } else {
        state.breadcrumbs.push(action.payload);
      }
    },
    
    setLoading: (state, action: PayloadAction<{ key: keyof UIState['loading']; value: boolean }>) => {
      const { key, value } = action.payload;
      state.loading[key] = value;
      
      // Update global loading if any specific loading is active
      if (!value && !Object.values(state.loading).some(loading => loading && key !== 'global')) {
        state.loading.global = false;
      } else if (value) {
        state.loading.global = true;
      }
    },
    
    setPreference: (state, action: PayloadAction<{ key: keyof UIState['preferences']; value: any }>) => {
      const { key, value } = action.payload;
      state.preferences[key] = value;
    },
    
    updatePreferences: (state, action: PayloadAction<Partial<UIState['preferences']>>) => {
      state.preferences = { ...state.preferences, ...action.payload };
    },
    
    setLayout: (state, action: PayloadAction<Partial<UIState['layout']>>) => {
      state.layout = { ...state.layout, ...action.payload };
    },
    
    updatePanelPosition: (state, action: PayloadAction<{
      panelId: string;
      position: { x: number; y: number; width: number; height: number };
    }>) => {
      const { panelId, position } = action.payload;
      state.layout.panelPositions[panelId] = position;
    },
    
    resetLayout: (state) => {
      state.sidebarCollapsed = initialState.sidebarCollapsed;
      state.sidebarWidth = initialState.sidebarWidth;
      state.rightPanelOpen = initialState.rightPanelOpen;
      state.rightPanelWidth = initialState.rightPanelWidth;
      state.activeView = initialState.activeView;
      state.layout = initialState.layout;
    },
    
    // Keyboard shortcuts
    handleKeyboardShortcut: (state, action: PayloadAction<string>) => {
      // This would be handled by components that subscribe to keyboard events
      const shortcut = action.payload;
      
      switch (shortcut) {
        case 'toggle-sidebar':
          state.sidebarCollapsed = !state.sidebarCollapsed;
          break;
        case 'toggle-right-panel':
          state.rightPanelOpen = !state.rightPanelOpen;
          break;
        case 'focus-search':
          state.activeView = 'search';
          break;
        case 'toggle-theme':
          if (state.theme === 'light') {
            state.theme = 'dark';
          } else if (state.theme === 'dark') {
            state.theme = 'auto';
          } else {
            state.theme = 'light';
          }
          break;
      }
    },
  },
});

export const {
  setTheme,
  toggleTheme,
  setSidebarCollapsed,
  toggleSidebar,
  setSidebarWidth,
  setRightPanelOpen,
  toggleRightPanel,
  setRightPanelWidth,
  setActiveView,
  openModal,
  closeModal,
  closeAllModals,
  addNotification,
  removeNotification,
  clearNotifications,
  setBreadcrumbs,
  addBreadcrumb,
  setLoading,
  setPreference,
  updatePreferences,
  setLayout,
  updatePanelPosition,
  resetLayout,
  handleKeyboardShortcut,
} = uiSlice.actions;

export default uiSlice.reducer;

// Selectors
export const selectTheme = (state: { ui: UIState }) => state.ui.theme;
export const selectSidebarCollapsed = (state: { ui: UIState }) => state.ui.sidebarCollapsed;
export const selectSidebarWidth = (state: { ui: UIState }) => state.ui.sidebarWidth;
export const selectRightPanelOpen = (state: { ui: UIState }) => state.ui.rightPanelOpen;
export const selectRightPanelWidth = (state: { ui: UIState }) => state.ui.rightPanelWidth;
export const selectActiveView = (state: { ui: UIState }) => state.ui.activeView;
export const selectModals = (state: { ui: UIState }) => state.ui.modals;
export const selectNotifications = (state: { ui: UIState }) => state.ui.notifications;
export const selectBreadcrumbs = (state: { ui: UIState }) => state.ui.breadcrumbs;
export const selectLoading = (state: { ui: UIState }) => state.ui.loading;
export const selectPreferences = (state: { ui: UIState }) => state.ui.preferences;
export const selectLayout = (state: { ui: UIState }) => state.ui.layout;