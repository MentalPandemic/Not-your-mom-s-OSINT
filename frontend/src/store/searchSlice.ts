import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { SearchQuery, SearchResult, SearchFilters } from '../types';

interface SearchState {
  query: SearchQuery;
  results: SearchResult[];
  loading: boolean;
  error: string | null;
  total: number;
  page: number;
  pageSize: number;
  history: string[];
  savedSearches: SearchQuery[];
}

const initialState: SearchState = {
  query: {
    query: '',
    type: 'all',
    filters: {},
  },
  results: [],
  loading: false,
  error: null,
  total: 0,
  page: 1,
  pageSize: 20,
  history: [],
  savedSearches: [],
};

const searchSlice = createSlice({
  name: 'search',
  initialState,
  reducers: {
    setQuery: (state, action: PayloadAction<SearchQuery>) => {
      state.query = action.payload;
      if (action.payload.query && !state.history.includes(action.payload.query)) {
        state.history = [action.payload.query, ...state.history.slice(0, 19)];
      }
    },
    setFilters: (state, action: PayloadAction<SearchFilters>) => {
      state.query.filters = action.payload;
    },
    setResults: (state, action: PayloadAction<{ results: SearchResult[]; total: number }>) => {
      state.results = action.payload.results;
      state.total = action.payload.total;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    setPage: (state, action: PayloadAction<number>) => {
      state.page = action.payload;
    },
    setPageSize: (state, action: PayloadAction<number>) => {
      state.pageSize = action.payload;
    },
    addSavedSearch: (state, action: PayloadAction<SearchQuery>) => {
      state.savedSearches = [action.payload, ...state.savedSearches];
    },
    removeSavedSearch: (state, action: PayloadAction<number>) => {
      state.savedSearches.splice(action.payload, 1);
    },
    clearResults: (state) => {
      state.results = [];
      state.total = 0;
      state.page = 1;
    },
  },
});

export const {
  setQuery,
  setFilters,
  setResults,
  setLoading,
  setError,
  setPage,
  setPageSize,
  addSavedSearch,
  removeSavedSearch,
  clearResults,
} = searchSlice.actions;

export default searchSlice.reducer;
