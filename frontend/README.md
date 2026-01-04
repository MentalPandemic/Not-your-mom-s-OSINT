# OSINT Dashboard - Frontend

A comprehensive React-based web interface for visualizing and analyzing Open Source Intelligence (OSINT) data.

## Features

### Core Functionality
- **Advanced Search Interface**: Multi-type search (username, email, phone, name, domain) with autocomplete and filters
- **Interactive Graph Visualization**: Network graphs with 1000+ nodes using vis.js
- **Identity Profiling**: Detailed identity panels with social media, employment, education, and relationships
- **Timeline Analysis**: Chronological activity visualization
- **Geographic Mapping**: Location-based data visualization with Leaflet
- **Data Export**: Multiple export formats (CSV, JSON, PDF, XLSX, HTML)
- **Workspace Management**: Organize investigations with multiple workspaces

### UI/UX Features
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Dark/Light Mode**: Theme switching with system preference detection
- **Keyboard Shortcuts**: Enhanced productivity with keyboard navigation
- **Real-time Updates**: Live data updates and notifications
- **Accessibility**: WCAG 2.1 AA compliant

## Tech Stack

- **React 18**: Modern React with hooks
- **TypeScript**: Type-safe development
- **Redux Toolkit**: State management
- **React Query**: Data fetching and caching
- **Tailwind CSS**: Utility-first styling
- **Vite**: Fast build tool
- **vis.js**: Graph visualization
- **Leaflet**: Map visualization
- **Chart.js**: Data charts
- **Axios**: HTTP client

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn
- Backend API running (see backend documentation)

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Update .env with your API URL
# VITE_API_URL=http://localhost:8000/api
```

### Development

```bash
# Start development server
npm run dev

# The app will be available at http://localhost:3000
```

### Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

### Testing

```bash
# Run unit tests
npm run test

# Run tests in watch mode
npm run test:watch

# Generate coverage report
npm run test:coverage
```

### Linting & Type Checking

```bash
# Run ESLint
npm run lint

# Run TypeScript type checking
npm run type-check
```

## Project Structure

```
frontend/
├── src/
│   ├── components/       # React components
│   │   ├── Dashboard.tsx
│   │   ├── SearchInterface.tsx
│   │   ├── ResultsView.tsx
│   │   ├── GraphVisualization.tsx
│   │   ├── IdentityProfile.tsx
│   │   ├── TimelineView.tsx
│   │   ├── ExportPanel.tsx
│   │   ├── Sidebar.tsx
│   │   ├── Settings.tsx
│   │   ├── NetworkAnalysis.tsx
│   │   ├── GeoVisualization.tsx
│   │   └── Workspace.tsx
│   ├── store/            # Redux store and slices
│   │   ├── index.ts
│   │   ├── searchSlice.ts
│   │   ├── graphSlice.ts
│   │   ├── uiSlice.ts
│   │   ├── workspaceSlice.ts
│   │   └── preferencesSlice.ts
│   ├── api/              # API client
│   │   ├── client.ts
│   │   └── osintApi.ts
│   ├── utils/            # Utility functions
│   │   ├── formatters.ts
│   │   ├── graphUtils.ts
│   │   └── exportUtils.ts
│   ├── hooks/            # Custom React hooks
│   │   ├── useAppDispatch.ts
│   │   ├── useAppSelector.ts
│   │   └── useDebounce.ts
│   ├── types/            # TypeScript type definitions
│   │   └── index.ts
│   ├── styles/           # Global styles
│   │   └── globals.css
│   ├── App.tsx           # Main App component
│   └── main.tsx          # Entry point
├── public/               # Static assets
├── index.html            # HTML template
├── vite.config.ts        # Vite configuration
├── tsconfig.json         # TypeScript configuration
├── tailwind.config.js    # Tailwind CSS configuration
└── package.json          # Dependencies and scripts
```

## Component Overview

### Dashboard
Main container component with header, navigation, and layout management.

### SearchInterface
Advanced search with filters, autocomplete, and saved searches.

### ResultsView
Tabbed results display with sorting, pagination, and filtering.

### GraphVisualization
Interactive network graph with zoom, pan, and layout options.

### IdentityProfile
Detailed identity information panel with tabs for different data categories.

### TimelineView
Chronological visualization of events and activities.

### ExportPanel
Data export with multiple formats and report templates.

### NetworkAnalysis
Network statistics and influence metrics visualization.

### GeoVisualization
Geographic data visualization on interactive maps.

### Workspace
Investigation workspace management and organization.

## State Management

The application uses Redux Toolkit for state management with the following slices:

- **searchSlice**: Search queries, results, and filters
- **graphSlice**: Graph nodes, edges, and visualization state
- **uiSlice**: UI state (theme, sidebar, active view)
- **workspaceSlice**: Workspace management
- **preferencesSlice**: User preferences and settings

## API Integration

The frontend communicates with the backend API through:

- **apiClient**: Axios-based HTTP client with interceptors
- **osintApi**: Typed API methods for all endpoints
- **React Query**: Data fetching, caching, and synchronization

## Styling

- **Tailwind CSS**: Utility-first CSS framework
- **Dark Mode**: CSS class-based dark mode support
- **Responsive Design**: Mobile-first approach with breakpoints
- **Custom Components**: Reusable styled components

## Performance Optimizations

- **Code Splitting**: Route-based code splitting
- **Lazy Loading**: Dynamic imports for heavy components
- **Virtual Scrolling**: Efficient rendering of long lists
- **Memoization**: React.memo and useMemo for expensive computations
- **Graph Optimization**: Progressive rendering for large graphs

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Accessibility

- Semantic HTML
- ARIA labels and roles
- Keyboard navigation
- Screen reader support
- Focus management
- Color contrast compliance

## Contributing

1. Follow the existing code style
2. Write TypeScript with proper types
3. Add tests for new features
4. Update documentation
5. Follow component naming conventions

## Troubleshooting

### Development server won't start
- Check Node.js version (18+)
- Clear node_modules and reinstall
- Check for port conflicts (default: 3000)

### API requests failing
- Verify backend is running
- Check VITE_API_URL in .env
- Check CORS configuration
- Verify API endpoint paths

### Graph not rendering
- Check browser console for errors
- Verify data format matches GraphNode/GraphEdge types
- Check vis-network library loaded correctly

### Build errors
- Run `npm run type-check` to find TypeScript errors
- Clear dist folder and rebuild
- Update dependencies if needed

## License

See LICENSE file in root directory.

## Support

For issues and questions:
- GitHub Issues: [Repository URL]
- Documentation: See docs folder
- Contact: [Contact Information]
