-- Plum Claims Database Initialization Script
-- This script runs on first PostgreSQL container startup

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Note: Tables are created via SQLAlchemy models (create_all) or Alembic migrations.
-- This file is for any initial setup SQL (extensions, roles, etc.)
