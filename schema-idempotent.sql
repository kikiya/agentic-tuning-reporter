-- ============================================================================
-- CRDB Cluster Tuning Report Generator Schema (Idempotent Version)
-- ============================================================================
-- This schema is safe to run multiple times. It will create the database
-- and tables if they don't exist, and recreate them if they do.
-- ============================================================================

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS tuning_reports;

-- Use the tuning_reports database
USE tuning_reports;

-- ============================================================================
-- DROP EXISTING TABLES (in reverse dependency order)
-- ============================================================================

DROP TABLE IF EXISTS action_status_history CASCADE;
DROP TABLE IF EXISTS finding_status_history CASCADE;
DROP TABLE IF EXISTS report_status_history CASCADE;
DROP TABLE IF EXISTS comments CASCADE;
DROP TABLE IF EXISTS recommended_actions CASCADE;
DROP TABLE IF EXISTS findings CASCADE;
DROP TABLE IF EXISTS reports CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ============================================================================
-- USERS TABLE
-- ============================================================================

CREATE TABLE users (
    id STRING PRIMARY KEY,
    name STRING NOT NULL,
    email STRING UNIQUE,
    role STRING DEFAULT 'analyst'
        CHECK (role IN ('admin', 'analyst', 'reviewer', 'viewer')),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================================
-- REPORTS TABLE
-- ============================================================================

CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cluster_id STRING NOT NULL,
    title STRING NOT NULL,
    description TEXT,
    status STRING NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'in_review', 'published', 'archived')),
    generated_at TIMESTAMPTZ,
    version INT DEFAULT 1,
    metadata JSONB,
    created_by STRING NOT NULL REFERENCES users(id),
    status_changed_by STRING REFERENCES users(id),
    status_changed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================================
-- FINDINGS TABLE
-- ============================================================================

CREATE TABLE findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    category STRING NOT NULL
        CHECK (category IN ('performance', 'configuration', 'security', 'reliability', 'monitoring')),
    severity STRING NOT NULL DEFAULT 'medium'
        CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    title STRING NOT NULL,
    description TEXT NOT NULL,
    details JSONB,
    status STRING NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'acknowledged', 'resolved', 'false_positive')),
    tags STRING[],
    created_by STRING NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================================
-- RECOMMENDED ACTIONS TABLE
-- ============================================================================

CREATE TABLE recommended_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    finding_id UUID NOT NULL REFERENCES findings(id) ON DELETE CASCADE,
    title STRING NOT NULL,
    description TEXT NOT NULL,
    action_type STRING NOT NULL
        CHECK (action_type IN ('configuration_change', 'query_optimization', 'index_creation', 'hardware_upgrade', 'monitoring_setup', 'backup_strategy', 'security_hardening')),
    priority STRING NOT NULL DEFAULT 'medium'
        CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    estimated_effort STRING DEFAULT 'medium'
        CHECK (estimated_effort IN ('low', 'medium', 'high')),
    status STRING NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),
    due_date TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    implementation_notes TEXT,
    created_by STRING NOT NULL REFERENCES users(id),
    status_changed_by STRING REFERENCES users(id),
    status_changed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================================
-- COMMENTS TABLE
-- ============================================================================

CREATE TABLE comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    parent_comment_id UUID REFERENCES comments(id) ON DELETE CASCADE,
    author_id STRING NOT NULL REFERENCES users(id),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================================
-- STATUS HISTORY TABLES
-- ============================================================================

CREATE TABLE report_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    old_status STRING,
    new_status STRING NOT NULL,
    changed_by STRING NOT NULL REFERENCES users(id),
    change_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE finding_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    finding_id UUID NOT NULL REFERENCES findings(id) ON DELETE CASCADE,
    old_status STRING,
    new_status STRING NOT NULL,
    changed_by STRING NOT NULL REFERENCES users(id),
    change_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE action_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action_id UUID NOT NULL REFERENCES recommended_actions(id) ON DELETE CASCADE,
    old_status STRING,
    new_status STRING NOT NULL,
    changed_by STRING NOT NULL REFERENCES users(id),
    change_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Reports indexes
CREATE INDEX IF NOT EXISTS idx_reports_cluster_status ON reports(cluster_id, status);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reports_status_changed_at ON reports(status_changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_reports_created_by ON reports(created_by);

-- Findings indexes
CREATE INDEX IF NOT EXISTS idx_findings_report_id ON findings(report_id);
CREATE INDEX IF NOT EXISTS idx_findings_category_severity ON findings(category, severity);
CREATE INDEX IF NOT EXISTS idx_findings_status ON findings(status);
CREATE INDEX IF NOT EXISTS idx_findings_created_by ON findings(created_by);

-- Actions indexes
CREATE INDEX IF NOT EXISTS idx_actions_finding_id ON recommended_actions(finding_id);
CREATE INDEX IF NOT EXISTS idx_actions_status_priority ON recommended_actions(status, priority);
CREATE INDEX IF NOT EXISTS idx_actions_due_date ON recommended_actions(due_date) WHERE status != 'completed';
CREATE INDEX IF NOT EXISTS idx_actions_created_by ON recommended_actions(created_by);
CREATE INDEX IF NOT EXISTS idx_actions_status_changed_at ON recommended_actions(status_changed_at DESC);

-- Comments indexes
CREATE INDEX IF NOT EXISTS idx_comments_report_id ON comments(report_id);
CREATE INDEX IF NOT EXISTS idx_comments_parent_id ON comments(parent_comment_id) WHERE parent_comment_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_comments_author_id ON comments(author_id);

-- Status history indexes (for audit queries)
CREATE INDEX IF NOT EXISTS idx_report_status_history_report_id ON report_status_history(report_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_report_status_history_changed_by ON report_status_history(changed_by, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_finding_status_history_finding_id ON finding_status_history(finding_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_finding_status_history_changed_by ON finding_status_history(changed_by, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_action_status_history_action_id ON action_status_history(action_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_action_status_history_changed_by ON action_status_history(changed_by, created_at DESC);

-- ============================================================================
-- SAMPLE DATA (Optional - for testing)
-- ============================================================================

/*
-- Sample users
INSERT INTO users (id, name, email, role) VALUES
    ('user_001', 'Alice Johnson', 'alice@company.com', 'analyst'),
    ('user_002', 'Bob Smith', 'bob@company.com', 'reviewer'),
    ('user_003', 'Carol Davis', 'carol@company.com', 'admin');

-- Sample report
INSERT INTO reports (cluster_id, title, description, created_by) VALUES
    ('prod-cluster-001', 'Q4 2024 Performance Tuning Report', 'Comprehensive analysis of production cluster performance', 'user_001');

-- Sample finding
INSERT INTO findings (report_id, category, severity, title, description, created_by)
SELECT id, 'performance', 'high', 'Slow Query Pattern Detected', 'Multiple queries showing N+1 patterns', 'user_001'
FROM reports WHERE title = 'Q4 2024 Performance Tuning Report';

-- Sample action
INSERT INTO recommended_actions (finding_id, title, description, action_type, priority, created_by)
SELECT f.id, 'Add Missing Index', 'Create index on frequently queried columns', 'index_creation', 'high', 'user_001'
FROM findings f
JOIN reports r ON f.report_id = r.id
WHERE r.title = 'Q4 2024 Performance Tuning Report';
*/

-- ============================================================================
-- USEFUL VIEWS (Optional)
-- ============================================================================

/*
-- View for recent status changes across all entities
CREATE OR REPLACE VIEW recent_status_changes AS
SELECT
    'report' as entity_type,
    r.id as entity_id,
    r.title as entity_title,
    rsh.new_status as current_status,
    rsh.changed_by as changed_by_name,
    u.name as changed_by_email,
    rsh.created_at as changed_at,
    rsh.change_reason
FROM reports r
JOIN report_status_history rsh ON r.id = rsh.report_id
JOIN users u ON rsh.changed_by = u.id
WHERE rsh.created_at >= now() - interval '30 days'

UNION ALL

SELECT
    'finding' as entity_type,
    f.id as entity_id,
    f.title as entity_title,
    fsh.new_status as current_status,
    fsh.changed_by as changed_by_name,
    u.name as changed_by_email,
    fsh.created_at as changed_at,
    fsh.change_reason
FROM findings f
JOIN finding_status_history fsh ON f.id = fsh.finding_id
JOIN users u ON fsh.changed_by = u.id
WHERE fsh.created_at >= now() - interval '30 days'

UNION ALL

SELECT
    'action' as entity_type,
    ra.id as entity_id,
    ra.title as entity_title,
    ash.new_status as current_status,
    ash.changed_by as changed_by_name,
    u.name as changed_by_email,
    ash.created_at as changed_at,
    ash.change_reason
FROM recommended_actions ra
JOIN action_status_history ash ON ra.id = ash.action_id
JOIN users u ON ash.changed_by = u.id
WHERE ash.created_at >= now() - interval '30 days'

ORDER BY changed_at DESC;
*/

-- ============================================================================
-- SETUP COMPLETE
-- ============================================================================
-- The database and all tables have been created successfully.
-- You can now run your application and start creating reports!
-- ============================================================================
