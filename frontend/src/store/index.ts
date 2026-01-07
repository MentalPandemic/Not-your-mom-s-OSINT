import { configureStore } from '@reduxjs/toolkit';
import searchReducer from './searchSlice';
import resultsReducer from './resultsSlice';
import graphReducer from './graphSlice';
import uiReducer from './uiSlice';
import workspaceReducer from './workspaceSlice';

export const store = configureStore({
  reducer: {
    search: searchReducer,
    results: resultsReducer,
    graph: graphReducer,
    ui: uiReducer,
    workspace: workspaceReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;