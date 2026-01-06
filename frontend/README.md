# OSINT Dashboard - Frontend

A comprehensive React frontend for the OSINT (Open Source Intelligence) platform, providing advanced visualization and analysis tools for security researchers and intelligence analysts.

## 🚀 Features

### Core Functionality
- **Interactive Search Interface**: Multi-type search with auto-complete and advanced filtering
- **Results Visualization**: Tabbed interface for identities, profiles, domains, and timeline data
- **Interactive Graph Visualization**: Network analysis using vis.js with 1000+ node support
- **Timeline Analysis**: Chronological view of activities and events
- **Export & Reporting**: Multiple format support (CSV, JSON, PDF, XLSX, HTML)
- **Identity Profiles**: Comprehensive person/identity intelligence cards
- **Geographic Visualization**: Location-based data mapping and analysis

### Advanced Features
- **Real-time Network Analysis**: Live graph updates with physics simulation
- **Relationship Mapping**: Advanced connection analysis between entities
- **Timeline Visualization**: Interactive timeline with event filtering
- **Workspace Management**: Save investigations, collaborative features
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Dark/Light Theme**: User preference-based theming
- **Keyboard Navigation**: Full accessibility support
- **Real-time Notifications**: System alerts and updates

## 🛠️ Technology Stack

### Core Technologies
- **React 18+** - Modern React with hooks and concurrent features
- **TypeScript** - Type-safe development
- **Redux Toolkit** - State management with RTK Query
- **Vite** - Fast build tool and development server

### UI & Styling
- **Tailwind CSS** - Utility-first CSS framework
- **Headless UI** - Accessible UI components
- **Framer Motion** - Animation and transitions
- **Lucide React** - Icon library

### Data Visualization
- **vis.js/vis-network** - Interactive network graphs
- **vis-timeline** - Timeline visualization
- **Chart.js/React-ChartJS-2** - Data charts
- **Leaflet** - Geographic mapping

### Development Tools
- **ESLint** - Code linting
- **Prettier** - Code formatting
- **Jest** - Unit testing
- **React Testing Library** - Component testing
- **Storybook** - Component documentation

## 📦 Installation

### Prerequisites
- Node.js 18+ 
- npm or yarn package manager

### Setup
```bash
# Clone the repository
git clone <repository-url>
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Run tests
npm run test
```

### Environment Variables
Create a `.env` file in the frontend directory:

```env
# API Configuration
VITE_API_BASE_URL=http://localhost:8000/api
VITE_API_TIMEOUT=30000
VITE_API_RETRY_ATTEMPTS=3

# Feature Flags
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_NOTIFICATIONS=true
VITE_ENABLE_DARK_MODE=true

# Development
VITE_DEBUG_MODE=false
VITE_LOG_LEVEL=info
```

## 🏗️ Project Structure

```
frontend/
├── public/                 # Static assets
├── src/
│   ├── components/         # React components
│   │   ├── ui/            # Reusable UI components
│   │   ├── Dashboard.tsx  # Main dashboard layout
│   │   ├── SearchInterface.tsx
│   │   ├── ResultsView.tsx
│   │   ├── GraphVisualization.tsx
│   │   ├── TimelineView.tsx
│   │   ├── ExportPanel.tsx
│   │   ├── Settings.tsx
│   │   └── IdentityProfile.tsx
│   ├── store/             # Redux store
│   │   ├── slices/        # Redux slices
│   │   └── index.ts       # Store configuration
│   ├── api/               # API client and services
│   │   ├── client.ts      # Axios HTTP client
│   │   └── search.ts      # Search API methods
│   ├── hooks/             # Custom React hooks
│   ├── utils/             # Utility functions
│   ├── types/             # TypeScript type definitions
│   ├── styles/            # Global styles and Tailwind config
│   ├── App.tsx            # Root component
│   └── main.tsx           # Application entry point
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
└── README.md
```

## 🎯 Component Overview

### Dashboard Layout
- **Header**: Navigation, search bar, user menu, notifications
- **Sidebar**: Search filters, saved searches, recent queries
- **Main Content**: Dynamic view switching based on active tab
- **Right Panel**: Detailed information for selected entities

### Search Interface
- **Multi-type Input**: Names, emails, phones, domains, usernames
- **Auto-complete**: Smart suggestions based on history
- **Advanced Filters**: Data sources, confidence thresholds, date ranges
- **Search History**: Recent queries and saved searches

### Results View
- **Tabbed Interface**: All Results, Identities, Profiles, Domains, Timeline
- **Sorting & Filtering**: Multiple criteria with real-time updates
- **Result Cards**: Entity preview with confidence scores
- **Pagination**: Efficient handling of large result sets

### Graph Visualization
- **Interactive Network**: Pan, zoom, select, and manipulate nodes
- **Multiple Layouts**: Force-directed, hierarchical, circular
- **Performance Optimized**: Handles 1000+ nodes smoothly
- **Real-time Updates**: Live graph modifications

### Timeline View
- **Chronological Analysis**: Time-based event visualization
- **Interactive Timeline**: Zoom, filter, and select events
- **Event Details**: Hover and click for comprehensive information
- **Export Options**: Timeline data export

### Export Panel
- **Multiple Formats**: CSV, JSON, PDF, XLSX, HTML
- **Template System**: Reusable export configurations
- **Batch Operations**: Export multiple entities
- **History Tracking**: Download management and history

## 🔧 Development

### Available Scripts
```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build
npm run test         # Run unit tests
npm run test:watch  # Run tests in watch mode
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript compiler check
npm run storybook    # Start Storybook dev server
```

### Code Style
- **TypeScript**: Strict mode enabled
- **ESLint**: Airbnb configuration
- **Prettier**: Automatic code formatting
- **Conventional Commits**: Standardized commit messages

### Testing Strategy
- **Unit Tests**: Jest + React Testing Library
- **Component Tests**: Storybook integration
- **E2E Tests**: Cypress (optional)
- **Visual Regression**: Screenshot testing

## 🎨 Theming & Styling

### Color System
- **Primary**: Blue palette for main actions
- **Secondary**: Gray palette for neutral elements
- **Semantic**: Success (green), Warning (yellow), Error (red)
- **OSINT Types**: Color-coded for different entity types

### Custom CSS Classes
```css
/* OSINT-specific styling */
.osint-node-identity    /* Identity entity nodes */
.osint-node-email      /* Email entity nodes */
.osint-node-phone      /* Phone entity nodes */
/* ... other entity types */

/* Component variants */
.timeline-event        /* Timeline event styling */
.vis-network          /* Graph container */
.loading-skeleton     /* Loading states */
```

## 🚀 Performance

### Optimization Features
- **Code Splitting**: Route-based lazy loading
- **Bundle Analysis**: Webpack bundle analyzer integration
- **Tree Shaking**: Unused code elimination
- **Image Optimization**: Lazy loading and responsive images
- **Memoization**: React.memo and useMemo usage
- **Virtual Scrolling**: Large list performance

### Bundle Size Targets
- **Initial Load**: < 500KB gzipped
- **Total Bundle**: < 2MB gzipped
- **Graph Library**: Separate chunk
- **Map Library**: Separate chunk

## 🔒 Security

### Input Validation
- **XSS Protection**: Content sanitization
- **CSRF Protection**: Token-based validation
- **SQL Injection**: Parameterized queries only
- **File Upload**: Type and size validation

### API Security
- **HTTPS Only**: Secure communication
- **Authentication**: JWT token handling
- **Rate Limiting**: Request throttling
- **Error Handling**: Secure error messages

## 📱 Responsive Design

### Breakpoints
- **Mobile**: 320px - 768px
- **Tablet**: 768px - 1024px
- **Desktop**: 1024px+

### Mobile Optimizations
- **Touch Interactions**: Optimized for touch devices
- **Collapsible Sidebar**: Space-efficient navigation
- **Responsive Tables**: Mobile-friendly data display
- **Performance**: Reduced animations on mobile

## 🧪 Testing

### Test Structure
```
src/
├── components/
│   ├── __tests__/        # Component tests
│   └── ComponentName.test.tsx
├── hooks/
│   ├── __tests__/        # Hook tests
│   └── useHook.test.ts
├── utils/
│   ├── __tests__/        # Utility tests
│   └── utils.test.ts
└── __mocks__/            # Mock files
```

### Test Examples
```typescript
// Component testing
import { render, screen, fireEvent } from '@testing-library/react';
import { Dashboard } from './Dashboard';

test('renders dashboard header', () => {
  render(<Dashboard />);
  expect(screen.getByText('OSINT Dashboard')).toBeInTheDocument();
});

// Hook testing
import { renderHook, act } from '@testing-library/react-hooks';
import { useSearch } from './useSearch';

test('updates search query', () => {
  const { result } = renderHook(() => useSearch());
  
  act(() => {
    result.current.setQuery('test@example.com');
  });
  
  expect(result.current.query).toBe('test@example.com');
});
```

## 📊 Monitoring & Analytics

### Error Tracking
- **Console Logging**: Development debugging
- **Error Boundaries**: React error handling
- **Performance Monitoring**: Core Web Vitals
- **User Analytics**: Usage patterns (optional)

### Development Tools
- **React DevTools**: Component inspection
- **Redux DevTools**: State debugging
- **Network Tab**: API request monitoring
- **Performance Tab**: Rendering performance

## 🤝 Contributing

### Development Workflow
1. **Fork & Clone**: Create your fork
2. **Branch**: Create feature branch
3. **Code**: Follow style guidelines
4. **Test**: Add/update tests
5. **Commit**: Use conventional commits
6. **Push**: Create pull request

### Code Review Process
- **Automated Checks**: CI/CD pipeline
- **Peer Review**: Code review required
- **Testing**: All tests must pass
- **Documentation**: Update as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## 🙏 Acknowledgments

- **React Team**: Amazing framework and ecosystem
- **Tailwind CSS**: Utility-first CSS framework
- **vis.js**: Powerful graph visualization library
- **Redux Toolkit**: Simplified state management
- **TypeScript**: Type safety and developer experience

## 📞 Support

For questions, issues, or contributions:
- **GitHub Issues**: Bug reports and feature requests
- **Documentation**: Comprehensive guides and API reference
- **Community**: Discord/Slack channels (if available)
- **Email**: support@osint-dashboard.com

---

Built with ❤️ for the OSINT community