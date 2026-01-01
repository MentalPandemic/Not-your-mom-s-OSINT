-- PostgreSQL initialization script for OSINT Platform
-- This script sets up the initial database structure

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text similarity searches

-- Create schema version table for migrations
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- Insert initial version
INSERT INTO schema_version (version, description) 
VALUES (1, 'Initial schema creation')
ON CONFLICT (version) DO NOTHING;

-- Note: Tables will be created by SQLAlchemy models
-- This script is for additional setup and extensions
