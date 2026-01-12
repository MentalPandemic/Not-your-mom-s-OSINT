import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { User, UserRole } from '@/types';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  token: string | null;
  refreshToken: string | null;
  tokenExpiry: Date | null;
  permissions: string[];
  loginAttempts: number;
  lastLoginAttempt: Date | null;
}

const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  token: null,
  refreshToken: null,
  tokenExpiry: null,
  permissions: [],
  loginAttempts: 0,
  lastLoginAttempt: null,
};

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setUser: (state, action: PayloadAction<User>) => {
      state.user = action.payload;
      state.isAuthenticated = true;
      state.error = null;
      
      // Set permissions based on user role
      switch (action.payload.role) {
        case UserRole.ADMIN:
          state.permissions = ['read', 'write', 'delete', 'admin', 'export'];
          break;
        case UserRole.ANALYST:
          state.permissions = ['read', 'write', 'export'];
          break;
        case UserRole.VIEWER:
          state.permissions = ['read'];
          break;
        default:
          state.permissions = [];
      }
    },
    
    setTokens: (state, action: PayloadAction<{ 
      token: string; 
      refreshToken: string; 
      expiresIn: number;
    }>) => {
      const { token, refreshToken, expiresIn } = action.payload;
      state.token = token;
      state.refreshToken = refreshToken;
      state.tokenExpiry = new Date(Date.now() + expiresIn * 1000);
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
    
    logout: (state) => {
      state.user = null;
      state.isAuthenticated = false;
      state.token = null;
      state.refreshToken = null;
      state.tokenExpiry = null;
      state.permissions = [];
      state.error = null;
    },
    
    updateUser: (state, action: PayloadAction<Partial<User>>) => {
      if (state.user) {
        state.user = { ...state.user, ...action.payload };
      }
    },
    
    updatePreferences: (state, action: PayloadAction<Partial<User['preferences']>>) => {
      if (state.user) {
        state.user.preferences = { ...state.user.preferences, ...action.payload };
      }
    },
    
    incrementLoginAttempts: (state) => {
      state.loginAttempts += 1;
      state.lastLoginAttempt = new Date();
    },
    
    resetLoginAttempts: (state) => {
      state.loginAttempts = 0;
      state.lastLoginAttempt = null;
    },
    
    clearError: (state) => {
      state.error = null;
    },
    
    // Session management
    refreshSession: (state) => {
      // Token refresh logic would be implemented here
      state.isLoading = false;
    },
    
    // Permission checks
    hasPermission: (state, action: PayloadAction<string>) => {
      return state.permissions.includes(action.payload);
    },
  },
});

export const {
  setUser,
  setTokens,
  setLoading,
  setError,
  logout,
  updateUser,
  updatePreferences,
  incrementLoginAttempts,
  resetLoginAttempts,
  clearError,
  refreshSession,
  hasPermission,
} = authSlice.actions;

export default authSlice.reducer;

// Selectors
export const selectUser = (state: { auth: AuthState }) => state.auth.user;
export const selectIsAuthenticated = (state: { auth: AuthState }) => state.auth.isAuthenticated;
export const selectIsAuthLoading = (state: { auth: AuthState }) => state.auth.isLoading;
export const selectAuthError = (state: { auth: AuthState }) => state.auth.error;
export const selectToken = (state: { auth: AuthState }) => state.auth.token;
export const selectTokenExpiry = (state: { auth: AuthState }) => state.auth.tokenExpiry;
export const selectPermissions = (state: { auth: AuthState }) => state.auth.permissions;
export const selectUserRole = (state: { auth: AuthState }) => state.auth.user?.role;
export const selectUserPreferences = (state: { auth: AuthState }) => state.auth.user?.preferences;
export const selectLoginAttempts = (state: { auth: AuthState }) => state.auth.loginAttempts;