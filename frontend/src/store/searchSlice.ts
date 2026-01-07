import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { searchAPI } from '../api/search';

export interface SearchQuery {
  query: string;
  type: 'username' | 'email' | 'phone' | 'name' | 'domain';
  filters?: {
    sources?: string[];
    dateRange?: { start?: string; end?: string };
    confidence?: number;
    platforms?: string[];
  };
}

export interface SearchState {
  currentQuery: SearchQuery | null;
  searchHistory: SearchQuery[];
  savedSearches: SearchQuery[];
  isLoading: boolean;
  error: string | null;
  suggestions: string[];
}

const initialState: SearchState = {
  currentQuery: null,
  searchHistory: [],
  savedSearches: [],
  isLoading: false,
  error: null,
  suggestions: [],
};

export const performSearch = createAsyncThunk(
  'search/performSearch',
  async (searchQuery: SearchQuery, { rejectWithValue }) => {
    try {
      const response = await searchAPI.search(searchQuery);
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const getSearchSuggestions = createAsyncThunk(
  'search/getSuggestions',
  async (query: string, { rejectWithValue }) => {
    try {
      const response = await searchAPI.getSuggestions(query);
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

const searchSlice = createSlice({
  name: 'search',
  initialState,
  reducers: {
    setCurrentQuery: (state, action) => {
      state.currentQuery = action.payload;
      if (action.payload) {
        state.searchHistory.unshift(action.payload);
        if (state.searchHistory.length > 50) {
          state.searchHistory = state.searchHistory.slice(0, 50);
        }
      }
    },
    saveSearch: (state, action) => {
      if (!state.savedSearches.find(s => s.query === action.payload.query)) {
        state.savedSearches.push(action.payload);
      }
    },
    removeSavedSearch: (state, action) => {
      state.savedSearches = state.savedSearches.filter(s => s.query !== action.payload);
    },
    clearSearchHistory: (state) => {
      state.searchHistory = [];
    },
    setSuggestions: (state, action) => {
      state.suggestions = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(performSearch.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(performSearch.fulfilled, (state) => {
        state.isLoading = false;
      })
      .addCase(performSearch.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      .addCase(getSearchSuggestions.fulfilled, (state, action) => {
        state.suggestions = action.payload;
      });
  },
});

export const { setCurrentQuery, saveSearch, removeSavedSearch, clearSearchHistory, setSuggestions } = searchSlice.actions;
export default searchSlice.reducer;