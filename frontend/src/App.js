import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import HomePage from './pages/HomePage';
import SearchPage from './pages/SearchPage';
import ResultsPage from './pages/ResultsPage';

function App() {
  return (
    <Router>
      <div className="App">
        <header className="App-header">
          <h1>OSINT Intelligence Platform</h1>
          <p className="tagline">Comprehensive Surface Web Intelligence Aggregation</p>
        </header>
        <main className="App-main">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/results/:searchId" element={<ResultsPage />} />
          </Routes>
        </main>
        <footer className="App-footer">
          <p>Phase 1: Surface Web OSINT Collection</p>
        </footer>
      </div>
    </Router>
  );
}

export default App;
