import { configureStore } from '@reduxjs/toolkit';
import searchReducer from './searchSlice';
import graphReducer from './graphSlice';
import uiReducer from './uiSlice';
import workspaceReducer from './workspaceSlice';
import preferencesReducer from './preferencesSlice';

export const store = configureStore({
  reducer: {
    search: searchReducer,
    graph: graphReducer,
    ui: uiReducer,
    workspace: workspaceReducer,
    preferences: preferencesReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['graph/setGraphData'],
        ignoredPaths: ['graph.nodes', 'graph.edges'],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
