# Frontend Architecture Documentation

## Overview

The OSINT Dashboard frontend is a comprehensive React-based single-page application (SPA) designed to provide researchers with powerful tools for visualizing and analyzing open-source intelligence data.

## Design Principles

### 1. Component-Based Architecture
- Modular, reusable components
- Single Responsibility Principle
- Clear component hierarchy
- Props-based data flow

### 2. State Management
- Centralized Redux store for global state
- Local component state for UI-specific data
- React Query for server state
- Immutable state updates

### 3. Type Safety
- TypeScript throughout the application
- Strict type checking
- Interface definitions for all data structures
- Generic types for reusable components

### 4. Performance
- Code splitting by route
- Lazy loading for heavy components
- Memoization of expensive computations
- Virtual scrolling for large lists
- Progressive rendering for graphs

### 5. Accessibility
- WCAG 2.1 AA compliance
- Semantic HTML
- ARIA labels and roles
- Keyboard navigation
- Screen reader support

## Architecture Layers

### Presentation Layer (Components)
Components are organized by feature and responsibility:

```
components/
├── Dashboard.tsx           # Main layout container
├── SearchInterface.tsx     # Search input and filters
├── ResultsView.tsx         # Search results display
├── GraphVisualization.tsx  # Network graph rendering
├── IdentityProfile.tsx     # Identity detail panel
├── TimelineView.tsx        # Timeline visualization
├── ExportPanel.tsx         # Export functionality
├── NetworkAnalysis.tsx     # Network statistics
├── GeoVisualization.tsx    # Geographic maps
├── Workspace.tsx           # Workspace management
├── Sidebar.tsx             # Navigation sidebar
└── Settings.tsx            # User preferences
```

### State Management Layer (Redux)
Redux store is split into domain-specific slices:

```
store/
├── index.ts              # Store configuration
├── searchSlice.ts        # Search state
├── graphSlice.ts         # Graph state
├── uiSlice.ts            # UI state
├── workspaceSlice.ts     # Workspace state
└── preferencesSlice.ts   # User preferences
```

### Data Layer (API)
API client handles all backend communication:

```
api/
├── client.ts     # HTTP client with interceptors
└── osintApi.ts   # Typed API methods
```

### Utility Layer
Helper functions for common operations:

```
utils/
├── formatters.ts    # Data formatting
├── graphUtils.ts    # Graph operations
└── exportUtils.ts   # Export functionality
```

## Data Flow

### 1. User Interaction Flow
```
User Action → Component Event Handler → Dispatch Redux Action → 
Update Store → Component Re-render
```

### 2. API Request Flow
```
User Action → Component → API Call → Loading State → 
Response → Update Store → Component Re-render
```

### 3. Graph Visualization Flow
```
Search Query → API Request → Graph Data → Transform → 
vis.js Network → Render → User Interaction
```

## Key Technologies

### Core
- **React 18**: Component framework
- **TypeScript**: Type safety
- **Vite**: Build tool

### State Management
- **Redux Toolkit**: Global state
- **React Query**: Server state
- **React Hooks**: Local state

### Visualization
- **vis.js**: Network graphs
- **Leaflet**: Geographic maps
- **Chart.js**: Data charts

### Styling
- **Tailwind CSS**: Utility-first CSS
- **CSS Custom Properties**: Theme variables
- **PostCSS**: CSS processing

### Routing
- **React Router**: Client-side routing

### HTTP
- **Axios**: HTTP client

## Component Patterns

### Container/Presentational Pattern
```typescript
// Container Component
const SearchContainer: React.FC = () => {
  const dispatch = useAppDispatch();
  const state = useAppSelector(state => state.search);
  
  const handleSearch = () => {
    dispatch(performSearch());
  };
  
  return <SearchPresentation data={state} onSearch={handleSearch} />;
};

// Presentational Component
const SearchPresentation: React.FC<Props> = ({ data, onSearch }) => {
  return <div>...</div>;
};
```

### Custom Hooks Pattern
```typescript
// Custom hook for common logic
const useSearch = () => {
  const dispatch = useAppDispatch();
  const [loading, setLoading] = useState(false);
  
  const search = async (query: string) => {
    setLoading(true);
    try {
      const results = await osintApi.search.execute({ query });
      dispatch(setResults(results));
    } finally {
      setLoading(false);
    }
  };
  
  return { search, loading };
};
```

### Render Props Pattern
```typescript
<DataProvider
  render={({ data, loading }) => (
    loading ? <Spinner /> : <DataDisplay data={data} />
  )}
/>
```

## State Structure

### Redux Store Shape
```typescript
{
  search: {
    query: SearchQuery,
    results: SearchResult[],
    loading: boolean,
    error: string | null,
    total: number,
    page: number,
    pageSize: number,
    history: string[],
    savedSearches: SearchQuery[]
  },
  graph: {
    nodes: GraphNode[],
    edges: GraphEdge[],
    selectedNode: GraphNode | null,
    highlightedNodes: string[],
    layout: 'force-directed' | 'hierarchical' | 'circular',
    filters: {
      nodeTypes: string[],
      edgeTypes: string[]
    },
    loading: boolean
  },
  ui: {
    theme: 'light' | 'dark',
    sidebarCollapsed: boolean,
    detailsPanelOpen: boolean,
    activeTab: string,
    activeView: string,
    notifications: Notification[]
  },
  workspace: {
    workspaces: Workspace[],
    activeWorkspace: Workspace | null,
    loading: boolean
  },
  preferences: UserPreferences
}
```

## API Integration

### Request Flow
1. Component calls API method
2. API client adds authentication headers
3. Request sent to backend
4. Response intercepted
5. Error handling
6. Retry logic (if needed)
7. Data returned to component

### Error Handling
- Network errors: Retry with exponential backoff
- 401 Unauthorized: Redirect to login
- 429 Rate Limited: Delay and retry
- Other errors: Display user-friendly message

### Caching Strategy
- React Query cache for GET requests
- 5-minute stale time
- Background refetching
- Cache invalidation on mutations

## Performance Optimizations

### Code Splitting
```typescript
const GraphVisualization = lazy(() => import('./components/GraphVisualization'));
const TimelineView = lazy(() => import('./components/TimelineView'));
```

### Memoization
```typescript
const MemoizedComponent = React.memo(Component);

const expensiveValue = useMemo(() => {
  return computeExpensiveValue(data);
}, [data]);
```

### Virtual Scrolling
```typescript
<FixedSizeList
  height={600}
  itemCount={items.length}
  itemSize={50}
>
  {Row}
</FixedSizeList>
```

### Graph Optimization
- Progressive rendering for large graphs
- Physics simulation throttling
- Node clustering for 1000+ nodes
- Lazy loading of node details

## Testing Strategy

### Unit Tests
- Component logic
- Redux actions and reducers
- Utility functions
- API client

### Integration Tests
- Component interactions
- Redux integration
- API integration
- Routing

### E2E Tests
- Critical user flows
- Search and display results
- Graph interactions
- Export functionality

## Security Considerations

### Input Validation
- Sanitize user input
- Validate data types
- Check data ranges

### XSS Prevention
- React's built-in XSS protection
- Sanitize HTML content
- Use dangerouslySetInnerHTML carefully

### CSRF Protection
- CSRF tokens in requests
- SameSite cookies

### Authentication
- JWT tokens
- Secure token storage
- Token refresh logic

## Accessibility Features

### Keyboard Navigation
- Tab navigation
- Arrow key navigation in lists
- Escape to close modals
- Enter to submit forms

### Screen Readers
- ARIA labels
- ARIA roles
- ARIA live regions
- Alt text for images

### Color Contrast
- WCAG AA compliance
- High contrast mode support
- Color-blind friendly palette

## Browser Support

### Desktop
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### Mobile
- iOS Safari 14+
- Chrome Mobile 90+
- Samsung Internet 14+

## Build & Deployment

### Development Build
```bash
npm run dev
```
- Fast HMR
- Source maps
- Dev server with proxy

### Production Build
```bash
npm run build
```
- Minification
- Tree shaking
- Code splitting
- Asset optimization

### Environment Variables
- VITE_API_URL: Backend API URL
- VITE_APP_NAME: Application name
- VITE_APP_VERSION: Application version

## Future Enhancements

### Planned Features
- Real-time collaboration
- Advanced graph algorithms
- Machine learning insights
- Custom report templates
- Plugin system
- Mobile app

### Technical Improvements
- WebAssembly for graph rendering
- Service workers for offline support
- Progressive Web App (PWA)
- GraphQL API integration
- Server-side rendering (SSR)

## Troubleshooting

### Common Issues

**Graph not rendering**
- Check data format
- Verify vis.js loaded
- Check browser console

**API requests failing**
- Verify backend running
- Check CORS settings
- Check network tab

**Performance issues**
- Check graph node count
- Disable physics simulation
- Use virtual scrolling

**Build errors**
- Clear node_modules
- Update dependencies
- Check TypeScript errors

## Contributing

### Code Style
- Use TypeScript
- Follow ESLint rules
- Use Prettier for formatting
- Write meaningful comments

### Component Guidelines
- Keep components small
- Use functional components
- Implement error boundaries
- Add PropTypes/TypeScript

### Testing Guidelines
- Write tests for new features
- Maintain test coverage
- Test edge cases
- Mock external dependencies

## Resources

- [React Documentation](https://react.dev)
- [Redux Toolkit Documentation](https://redux-toolkit.js.org)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [vis.js Documentation](https://visjs.org)
