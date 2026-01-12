import { configureStore } from '@reduxjs/toolkit';
import { useDispatch, useSelector, TypedUseSelectorHook } from 'react-redux';
import authSlice from './slices/authSlice';
import searchSlice from './slices/searchSlice';
import graphSlice from './slices/graphSlice';
import workspaceSlice from './slices/workspaceSlice';
import uiSlice from './slices/uiSlice';
import exportSlice from './slices/exportSlice';

export const store = configureStore({
  reducer: {
    auth: authSlice,
    search: searchSlice,
    graph: graphSlice,
    workspace: workspaceSlice,
    ui: uiSlice,
    export: exportSlice,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: [
          'persist/PERSIST',
          'persist/REHYDRATE',
          'graph/updateNodePositions',
          'graph/setGraphData',
        ],
        ignoredPaths: ['graph.nodes', 'graph.edges'],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// Typed hooks
export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;