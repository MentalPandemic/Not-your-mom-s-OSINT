import React from 'react';
import { useNavigate } from 'react-router-dom';
import './HomePage.css';

function HomePage() {
  const navigate = useNavigate();

  return (
    <div className="home-page">
      <div className="hero-section card">
        <h2>Welcome to the OSINT Intelligence Platform</h2>
        <p className="hero-description">
          A comprehensive open-source intelligence aggregation platform designed to discover 
          and map relationships between disparate data points across the surface web.
        </p>
        <button className="button hero-button" onClick={() => navigate('/search')}>
          Start Investigation
        </button>
      </div>

      <div className="features-section">
        <div className="feature-card card">
          <h3>🔍 Comprehensive Data Collection</h3>
          <p>
            Search across hundreds of platforms including social media, adult sites, 
            personals/classified platforms, public databases, and more.
          </p>
        </div>

        <div className="feature-card card">
          <h3>🕸️ Relationship Mapping</h3>
          <p>
            Automatically discover and visualize connections between identities, 
            usernames, emails, phone numbers, and content across platforms.
          </p>
        </div>

        <div className="feature-card card">
          <h3>📊 Data Enrichment</h3>
          <p>
            Enrich collected data with metadata, confidence scores, and cross-references 
            to build comprehensive intelligence profiles.
          </p>
        </div>

        <div className="feature-card card">
          <h3>📤 Multiple Export Formats</h3>
          <p>
            Export your findings in JSON, CSV, or GraphML format for further analysis 
            in your preferred tools.
          </p>
        </div>
      </div>

      <div className="phase1-info card">
        <h3>Phase 1: Surface Web Intelligence</h3>
        <div className="source-categories">
          <div className="source-category">
            <h4>Mainstream Platforms</h4>
            <ul>
              <li>Social media (Twitter, LinkedIn, Instagram, Facebook, etc.)</li>
              <li>GitHub repositories and commits</li>
              <li>Public data aggregators</li>
              <li>WHOIS/DNS records</li>
              <li>Username enumeration (hundreds of sites)</li>
            </ul>
          </div>

          <div className="source-category">
            <h4>Adult/NSFW Platforms</h4>
            <ul>
              <li>Adult content sites (Pornhub, xHamster, Motherless, etc.)</li>
              <li>Adult social platforms (Fetlife, OnlyFans, etc.)</li>
              <li>Adult forums and communities</li>
            </ul>
          </div>

          <div className="source-category">
            <h4>Personals & Classified Sites</h4>
            <ul>
              <li>Skipthegames.com</li>
              <li>Bedpage.com</li>
              <li>Craigslist (all sections)</li>
              <li>Doublelist</li>
              <li>Other personals platforms</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default HomePage;
