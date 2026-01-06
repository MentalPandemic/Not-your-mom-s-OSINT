import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { 
  SearchQuery, 
  SearchResults, 
  SearchFilters, 
  EntitySearchResult,
  QueryType 
} from '@/types';

interface SearchState {
  currentQuery: SearchQuery | null;
  searchResults: SearchResults | null;
  searchHistory: SearchQuery[];
  savedSearches: SearchQuery[];
  isSearching: boolean;
  searchError: string | null;
  recentQueries: string[];
  suggestions: string[];
  filters: SearchFilters;
  sortBy: 'relevance' | 'confidence' | 'date' | 'name';
  sortOrder: 'asc' | 'desc';
  resultsPerPage: number;
  currentPage: number;
  selectedResult: EntitySearchResult | null;
}

const initialState: SearchState = {
  currentQuery: null,
  searchResults: null,
  searchHistory: [],
  savedSearches: [],
  isSearching: false,
  searchError: null,
  recentQueries: [],
  suggestions: [],
  filters: {
    confidenceThreshold: 0.7,
    includeNSFW: false,
  },
  sortBy: 'relevance',
  sortOrder: 'desc',
  resultsPerPage: 50,
  currentPage: 1,
  selectedResult: null,
};

const searchSlice = createSlice({
  name: 'search',
  initialState,
  reducers: {
    setCurrentQuery: (state, action: PayloadAction<SearchQuery>) => {
      state.currentQuery = action.payload;
      state.searchError = null;
    },
    
    setSearchResults: (state, action: PayloadAction<SearchResults>) => {
      state.searchResults = action.payload;
      state.isSearching = false;
      state.searchError = null;
      
      // Add to history
      if (state.currentQuery) {
        const existingIndex = state.searchHistory.findIndex(
          q => q.id === state.currentQuery!.id
        );
        
        if (existingIndex >= 0) {
          state.searchHistory[existingIndex] = state.currentQuery;
        } else {
          state.searchHistory.unshift(state.currentQuery);
          // Keep only last 50 searches
          state.searchHistory = state.searchHistory.slice(0, 50);
        }
        
        // Add query string to recent queries
        const queryString = `${state.currentQuery.query} (${state.currentQuery.queryType})`;
        const recentIndex = state.recentQueries.indexOf(queryString);
        if (recentIndex >= 0) {
          state.recentQueries.splice(recentIndex, 1);
        }
        state.recentQueries.unshift(queryString);
        // Keep only last 20 queries
        state.recentQueries = state.recentQueries.slice(0, 20);
      }
    },
    
    setIsSearching: (state, action: PayloadAction<boolean>) => {
      state.isSearching = action.payload;
      if (action.payload) {
        state.searchError = null;
      }
    },
    
    setSearchError: (state, action: PayloadAction<string>) => {
      state.searchError = action.payload;
      state.isSearching = false;
    },
    
    addToSavedSearches: (state, action: PayloadAction<SearchQuery>) => {
      const exists = state.savedSearches.find(s => s.id === action.payload.id);
      if (!exists) {
        state.savedSearches.push(action.payload);
      }
    },
    
    removeFromSavedSearches: (state, action: PayloadAction<string>) => {
      state.savedSearches = state.savedSearches.filter(s => s.id !== action.payload);
    },
    
    updateFilters: (state, action: PayloadAction<Partial<SearchFilters>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    
    resetFilters: (state) => {
      state.filters = initialState.filters;
    },
    
    setSortBy: (state, action: PayloadAction<typeof initialState.sortBy>) => {
      state.sortBy = action.payload;
    },
    
    setSortOrder: (state, action: PayloadAction<typeof initialState.sortOrder>) => {
      state.sortOrder = action.payload;
    },
    
    setResultsPerPage: (state, action: PayloadAction<number>) => {
      state.resultsPerPage = action.payload;
      state.currentPage = 1;
    },
    
    setCurrentPage: (state, action: PayloadAction<number>) => {
      state.currentPage = action.payload;
    },
    
    setSuggestions: (state, action: PayloadAction<string[]>) => {
      state.suggestions = action.payload;
    },
    
    setSelectedResult: (state, action: PayloadAction<EntitySearchResult | null>) => {
      state.selectedResult = action.payload;
    },
    
    clearSearchResults: (state) => {
      state.searchResults = null;
      state.selectedResult = null;
    },
    
    clearSearchHistory: (state) => {
      state.searchHistory = [];
      state.recentQueries = [];
    },
    
    removeFromRecentQueries: (state, action: PayloadAction<string>) => {
      state.recentQueries = state.recentQueries.filter(q => q !== action.payload);
    },
    
    // Generate search suggestions based on history and common patterns
    generateSuggestions: (state, action: PayloadAction<string>) => {
      const query = action.payload.toLowerCase();
      const suggestions: string[] = [];
      
      // From recent queries
      state.recentQueries.forEach(recentQuery => {
        if (recentQuery.toLowerCase().includes(query)) {
          suggestions.push(recentQuery);
        }
      });
      
      // From saved searches
      state.savedSearches.forEach(savedSearch => {
        if (savedSearch.query.toLowerCase().includes(query)) {
          suggestions.push(`${savedSearch.query} (${savedSearch.queryType})`);
        }
      });
      
      // Common OSINT patterns
      const patterns = [
        '@gmail.com',
        '@yahoo.com',
        '@outlook.com',
        '.com',
        '.org',
        '.net',
        'linkedin.com/in/',
        'twitter.com/',
        'github.com/',
      ];
      
      patterns.forEach(pattern => {
        if (query.includes(pattern)) {
          suggestions.push(query.replace(pattern, '') + pattern);
        }
      });
      
      // Remove duplicates and limit to 10
      state.suggestions = [...new Set(suggestions)].slice(0, 10);
    },
  },
});

export const {
  setCurrentQuery,
  setSearchResults,
  setIsSearching,
  setSearchError,
  addToSavedSearches,
  removeFromSavedSearches,
  updateFilters,
  resetFilters,
  setSortBy,
  setSortOrder,
  setResultsPerPage,
  setCurrentPage,
  setSuggestions,
  setSelectedResult,
  clearSearchResults,
  clearSearchHistory,
  removeFromRecentQueries,
  generateSuggestions,
} = searchSlice.actions;

export default searchSlice.reducer;

// Selectors
export const selectCurrentQuery = (state: { search: SearchState }) => state.search.currentQuery;
export const selectSearchResults = (state: { search: SearchState }) => state.search.searchResults;
export const selectIsSearching = (state: { search: SearchState }) => state.search.isSearching;
export const selectSearchError = (state: { search: SearchState }) => state.search.searchError;
export const selectFilters = (state: { search: SearchState }) => state.search.filters;
export const selectSortBy = (state: { search: SearchState }) => state.search.sortBy;
export const selectSortOrder = (state: { search: SearchState }) => state.search.sortOrder;
export const selectResultsPerPage = (state: { search: SearchState }) => state.search.resultsPerPage;
export const selectCurrentPage = (state: { search: SearchState }) => state.search.currentPage;
export const selectSelectedResult = (state: { search: SearchState }) => state.search.selectedResult;
export const selectSearchHistory = (state: { search: SearchState }) => state.search.searchHistory;
export const selectSavedSearches = (state: { search: SearchState }) => state.search.savedSearches;
export const selectRecentQueries = (state: { search: SearchState }) => state.search.recentQueries;
export const selectSuggestions = (state: { search: SearchState }) => state.search.suggestions;