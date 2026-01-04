import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { UserPreferences } from '../types';

const initialState: UserPreferences = {
  theme: 'dark',
  defaultConfidenceThreshold: 0.5,
  graphLayout: 'force-directed',
  resultsPerPage: 20,
  dataSources: [],
  includeNSFW: false,
  apiTimeout: 30000,
};

const preferencesSlice = createSlice({
  name: 'preferences',
  initialState,
  reducers: {
    setPreferences: (state, action: PayloadAction<Partial<UserPreferences>>) => {
      return { ...state, ...action.payload };
    },
    setTheme: (state, action: PayloadAction<'light' | 'dark' | 'auto'>) => {
      state.theme = action.payload;
    },
    setConfidenceThreshold: (state, action: PayloadAction<number>) => {
      state.defaultConfidenceThreshold = action.payload;
    },
    setGraphLayout: (state, action: PayloadAction<'force-directed' | 'hierarchical' | 'circular'>) => {
      state.graphLayout = action.payload;
    },
    setResultsPerPage: (state, action: PayloadAction<number>) => {
      state.resultsPerPage = action.payload;
    },
    toggleDataSource: (state, action: PayloadAction<string>) => {
      const index = state.dataSources.indexOf(action.payload);
      if (index > -1) {
        state.dataSources.splice(index, 1);
      } else {
        state.dataSources.push(action.payload);
      }
    },
    toggleNSFW: (state) => {
      state.includeNSFW = !state.includeNSFW;
    },
  },
});

export const {
  setPreferences,
  setTheme,
  setConfidenceThreshold,
  setGraphLayout,
  setResultsPerPage,
  toggleDataSource,
  toggleNSFW,
} = preferencesSlice.actions;

export default preferencesSlice.reducer;
