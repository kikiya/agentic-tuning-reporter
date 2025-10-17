#!/bin/bash

# ============================================================================
# CRDB Tuning Reports Database Setup Script
# ============================================================================
# This script sets up the tuning_reports database and schema for the
# CRDB Cluster Tuning Report Generator application.
#
# Usage:
#   ./setup-database.sh [cockroach-db-url]
#
# Default URL: postgresql://root@localhost:26257
# ============================================================================

set -e

# Default database URL
DEFAULT_DB_URL="postgresql://root@Kikias-MacBook-Pro-2.local:26257/defaultdb?sslmode=disable"
DB_URL="${1:-$DEFAULT_DB_URL}"

echo "🐛 Setting up CRDB Tuning Reports Database..."
echo "📍 Database URL: $DB_URL"

# Function to execute SQL commands
execute_sql() {
    local sql="$1"
    echo "⚡ Executing: $sql"
    cockroach sql --url="$DB_URL" --execute="$sql"
}

# Create database if it doesn't exist
echo ""
echo "📦 Creating database 'tuning_reports'..."
execute_sql "CREATE DATABASE IF NOT EXISTS tuning_reports;"

execute_sql "USE tuning_reports;"

# Use the tuning_reports database for subsequent commands
DB_URL_WITH_DB="postgresql://root@localhost:26257/tuning_reports?sslmode=disable"

echo ""
echo "🔗 Switching connection to tuning_reports database for subsequent commands..."
DB_URL="$DB_URL_WITH_DB"

echo ""
echo "🗂️  Setting up schema..."

# Drop existing tables (in reverse dependency order)
echo "🗑️  Dropping existing tables..."
execute_sql "DROP TABLE IF EXISTS action_status_history CASCADE;" 
execute_sql "DROP TABLE IF EXISTS finding_status_history CASCADE;" 
execute_sql "DROP TABLE IF EXISTS report_status_history CASCADE;" 
execute_sql "DROP TABLE IF EXISTS comments CASCADE;" 
execute_sql "DROP TABLE IF EXISTS recommended_actions CASCADE;" 
execute_sql "DROP TABLE IF EXISTS findings CASCADE;" 
execute_sql "DROP TABLE IF EXISTS reports CASCADE;" 
execute_sql "DROP TABLE IF EXISTS users CASCADE;" 

# Create users table
echo "👥 Creating users table..."
execute_sql "CREATE TABLE users (id STRING PRIMARY KEY, name STRING NOT NULL, email STRING UNIQUE, role STRING DEFAULT 'analyst' CHECK (role IN ('admin', 'analyst', 'reviewer', 'viewer')), created_at TIMESTAMPTZ DEFAULT now());" 

# Create reports table
echo "📊 Creating reports table..."
execute_sql "CREATE TABLE reports (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), cluster_id STRING NOT NULL, title STRING NOT NULL, description TEXT, status STRING NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'in_review', 'published', 'archived')), generated_at TIMESTAMPTZ, version INT DEFAULT 1, metadata JSONB, created_by STRING NOT NULL REFERENCES users(id), status_changed_by STRING REFERENCES users(id), status_changed_at TIMESTAMPTZ, created_at TIMESTAMPTZ DEFAULT now(), updated_at TIMESTAMPTZ DEFAULT now());" 

# Create findings table
echo "🔍 Creating findings table..."
execute_sql "CREATE TABLE findings (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE, category STRING NOT NULL CHECK (category IN ('performance', 'configuration', 'security', 'reliability', 'monitoring')), severity STRING NOT NULL DEFAULT 'medium' CHECK (severity IN ('low', 'medium', 'high', 'critical')), title STRING NOT NULL, description TEXT NOT NULL, details JSONB, status STRING NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'acknowledged', 'resolved', 'false_positive')), tags STRING[], created_by STRING NOT NULL REFERENCES users(id), created_at TIMESTAMPTZ DEFAULT now(), updated_at TIMESTAMPTZ DEFAULT now());" 

# Create recommended_actions table
echo "⚡ Creating recommended_actions table..."
execute_sql "CREATE TABLE recommended_actions (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), finding_id UUID NOT NULL REFERENCES findings(id) ON DELETE CASCADE, title STRING NOT NULL, description TEXT NOT NULL, action_type STRING NOT NULL CHECK (action_type IN ('configuration_change', 'query_optimization', 'index_creation', 'hardware_upgrade', 'monitoring_setup', 'backup_strategy', 'security_hardening')), priority STRING NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')), estimated_effort STRING DEFAULT 'medium' CHECK (estimated_effort IN ('low', 'medium', 'high')), status STRING NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')), due_date TIMESTAMPTZ, completed_at TIMESTAMPTZ, implementation_notes TEXT, created_by STRING NOT NULL REFERENCES users(id), status_changed_by STRING REFERENCES users(id), status_changed_at TIMESTAMPTZ, created_at TIMESTAMPTZ DEFAULT now(), updated_at TIMESTAMPTZ DEFAULT now());" 

# Create comments table
echo "💬 Creating comments table..."
execute_sql "CREATE TABLE comments (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE, parent_comment_id UUID REFERENCES comments(id) ON DELETE CASCADE, author_id STRING NOT NULL REFERENCES users(id), content TEXT NOT NULL, created_at TIMESTAMPTZ DEFAULT now(), updated_at TIMESTAMPTZ DEFAULT now());" 

# Create status history tables
echo "📚 Creating status history tables..."
execute_sql "CREATE TABLE report_status_history (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE, old_status STRING, new_status STRING NOT NULL, changed_by STRING NOT NULL REFERENCES users(id), change_reason TEXT, created_at TIMESTAMPTZ DEFAULT now());" 
execute_sql "CREATE TABLE finding_status_history (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), finding_id UUID NOT NULL REFERENCES findings(id) ON DELETE CASCADE, old_status STRING, new_status STRING NOT NULL, changed_by STRING NOT NULL REFERENCES users(id), change_reason TEXT, created_at TIMESTAMPTZ DEFAULT now());" 
execute_sql "CREATE TABLE action_status_history (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), action_id UUID NOT NULL REFERENCES recommended_actions(id) ON DELETE CASCADE, old_status STRING, new_status STRING NOT NULL, changed_by STRING NOT NULL REFERENCES users(id), change_reason TEXT, created_at TIMESTAMPTZ DEFAULT now());" 

# Create indexes
echo "⚡ Creating performance indexes..."
execute_sql "CREATE INDEX IF NOT EXISTS idx_reports_cluster_status ON reports(cluster_id, status);" 
execute_sql "CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at DESC);" 
execute_sql "CREATE INDEX IF NOT EXISTS idx_reports_created_by ON reports(created_by);" 
execute_sql "CREATE INDEX IF NOT EXISTS idx_findings_report_id ON findings(report_id);" 
execute_sql "CREATE INDEX IF NOT EXISTS idx_findings_category_severity ON findings(category, severity);" 
execute_sql "CREATE INDEX IF NOT EXISTS idx_actions_finding_id ON recommended_actions(finding_id);" 
execute_sql "CREATE INDEX IF NOT EXISTS idx_actions_status_priority ON recommended_actions(status, priority);" 
execute_sql "CREATE INDEX IF NOT EXISTS idx_comments_report_id ON comments(report_id);" 

# Add sample data (optional)
echo ""
echo "🌱 Adding sample data..."
execute_sql "INSERT INTO users (id, name, email, role) VALUES ('user_001', 'Alice Johnson', 'alice@company.com', 'analyst'), ('user_002', 'Bob Smith', 'bob@company.com', 'reviewer'), ('user_003', 'Carol Davis', 'carol@company.com', 'admin');" 

echo ""
echo "✅ Database setup complete!"
echo ""
echo "📋 Summary:"
echo "  • Database: tuning_reports"
echo "  • Tables: 7 main tables + 3 history tables"
echo "  • Indexes: 10 performance indexes"
echo "  • Sample Users: 3 users created"
echo ""
echo "🚀 You can now:"
echo "  • Run your FastAPI backend: python main.py"
echo "  • Run your React frontend: npm start"
echo "  • Access the app at http://localhost:3000"
echo ""
echo "📖 For more information, check the README.md file."
