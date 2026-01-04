# Not-your-mom's-OSINT

A comprehensive Open Source Intelligence (OSINT) aggregation platform with advanced visualization and analysis capabilities.

## Overview

This platform provides researchers and investigators with powerful tools to:
- Aggregate data from multiple OSINT sources
- Visualize relationships between disparate data points
- Analyze social networks and connections
- Track activity timelines
- Generate comprehensive intelligence reports
- Export data in multiple formats

## Features

### 🔍 Advanced Search
- Multi-type search (username, email, phone, name, domain)
- Advanced filtering and date range selection
- Autocomplete and search suggestions
- Search history and saved searches

### 📊 Interactive Visualization
- Network graph with 1000+ nodes
- Multiple layout algorithms (force-directed, hierarchical, circular)
- Node/edge filtering and customization
- Zoom, pan, and interactive controls

### 👤 Identity Profiling
- Comprehensive identity information
- Social media profile aggregation
- Employment and education history
- Relationship mapping
- Confidence scoring

### 📅 Timeline Analysis
- Chronological activity visualization
- Event filtering and categorization
- Platform-specific timelines
- Export timeline data

### 🗺️ Geographic Mapping
- Location visualization on interactive maps
- Address clustering and heatmaps
- Movement pattern analysis

### 📤 Data Export
- Multiple formats: CSV, JSON, PDF, XLSX, HTML
- Report templates (standard, executive, detailed)
- Batch export capabilities
- Custom export options

### 🗂️ Workspace Management
- Organize investigations in workspaces
- Save queries and results
- Tagging and categorization
- Collaboration features (planned)

## Technology Stack

### Frontend
- React 18 with TypeScript
- Redux Toolkit for state management
- Tailwind CSS for styling
- vis.js for graph visualization
- Leaflet for maps
- Vite for building

### Architecture
- Component-based design
- Type-safe development
- Responsive and accessible
- Dark/light mode support
- Performance optimized

## Getting Started

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/not-your-moms-osint.git
cd not-your-moms-osint

# Install frontend dependencies
cd frontend
npm install

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Start development server
npm run dev
```

The application will be available at `http://localhost:3000`

### Building for Production

```bash
cd frontend
npm run build
npm run preview
```

## Documentation

- **[Frontend README](./frontend/README.md)** - Frontend setup and development
- **[User Guide](./frontend/USER_GUIDE.md)** - How to use the dashboard
- **[Architecture](./frontend/ARCHITECTURE.md)** - Technical architecture details

## Project Structure

```
not-your-moms-osint/
├── frontend/              # React frontend application
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── store/        # Redux store
│   │   ├── api/          # API client
│   │   ├── utils/        # Utility functions
│   │   ├── hooks/        # Custom React hooks
│   │   ├── types/        # TypeScript types
│   │   └── styles/       # Global styles
│   ├── public/           # Static assets
│   └── README.md
└── README.md             # This file
```

## Features Roadmap

### Current (v1.0)
- ✅ Advanced search interface
- ✅ Interactive graph visualization
- ✅ Identity profiling
- ✅ Timeline analysis
- ✅ Data export
- ✅ Workspace management

### Planned (v2.0)
- 🔄 Real-time collaboration
- 🔄 Advanced analytics and ML insights
- 🔄 Custom data source integration
- 🔄 Automated report generation
- 🔄 API rate limiting and quota management
- 🔄 Mobile application

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Security

For security issues, please email security@example.com instead of using the issue tracker.

## License

[Add your license here]

## Acknowledgments

- vis.js for graph visualization
- Leaflet for mapping
- React and the React ecosystem
- All open source contributors

## Support

- Documentation: See docs folder
- Issues: GitHub Issues
- Discussions: GitHub Discussions

## Screenshots

[Add screenshots of your dashboard here]

## Demo

[Add link to live demo if available]

---

**Note**: This is a powerful intelligence tool. Please use responsibly and ethically, respecting privacy laws and regulations in your jurisdiction.
