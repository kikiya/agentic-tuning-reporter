-- ============================================================================
-- Schema Migration: Add Vector Embeddings for Similarity Search
-- ============================================================================
-- This migration adds vector embedding support to enable similarity search
-- across reports and findings.
-- ============================================================================

-- Enable pgvector extension (if not already enabled)
-- Note: CockroachDB has native vector support, no extension needed

-- Add embedding column to reports table
ALTER TABLE reports 
  ADD COLUMN IF NOT EXISTS embedding VECTOR(1536);

-- Add optional metadata columns for future guardrails
-- These are nullable to allow gradual adoption
ALTER TABLE reports
  ADD COLUMN IF NOT EXISTS customer_id UUID,
  ADD COLUMN IF NOT EXISTS region STRING,
  ADD COLUMN IF NOT EXISTS pii_flag BOOL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS crdb_version STRING;

-- Add embedding column to findings table (for finding-level similarity)
ALTER TABLE findings
  ADD COLUMN IF NOT EXISTS embedding VECTOR(1536),
  ADD COLUMN IF NOT EXISTS customer_id UUID;

-- Create indexes for efficient filtering
-- Note: CockroachDB has native vector support but may not support vector indexes yet
-- For now, we rely on regular B-tree indexes for prefiltering
-- Vector distance calculation happens on the filtered result set

-- Standard B-tree index for customer/region filtering (prefilter before vector search)
CREATE INDEX IF NOT EXISTS idx_reports_customer_region 
  ON reports(customer_id, region) 
  WHERE pii_flag = FALSE;

-- Index for efficient NULL checks and status filtering
CREATE INDEX IF NOT EXISTS idx_reports_embedding_status
  ON reports(status)
  WHERE embedding IS NOT NULL AND pii_flag = FALSE;

-- Similar index for findings
CREATE INDEX IF NOT EXISTS idx_findings_embedding_status
  ON findings(status)
  WHERE embedding IS NOT NULL;

-- ============================================================================
-- Optional: Create customers table for future multi-tenant access control
-- ============================================================================

CREATE TABLE IF NOT EXISTS customers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name STRING NOT NULL,
  region STRING CHECK (region IN ('US', 'EU', 'APAC', 'GLOBAL')),
  pii_allowed BOOL DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================================
-- Optional: Create user_access table for fine-grained permissions
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_access (
  user_id STRING NOT NULL REFERENCES users(id),
  customer_id UUID NOT NULL REFERENCES customers(id),
  access_level STRING DEFAULT 'read' 
    CHECK (access_level IN ('read', 'write', 'admin')),
  granted_at TIMESTAMPTZ DEFAULT now(),
  granted_by STRING REFERENCES users(id),
  PRIMARY KEY (user_id, customer_id)
);

-- Create index for efficient access checks
CREATE INDEX IF NOT EXISTS idx_user_access_user_id ON user_access(user_id);

-- ============================================================================
-- Optional: Create content_flags table for fine-grained content controls
-- ============================================================================

CREATE TABLE IF NOT EXISTS content_flags (
  report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
  flag STRING NOT NULL,  -- e.g., 'pii', 'restricted', 'needs_review'
  added_by STRING REFERENCES users(id),
  added_at TIMESTAMPTZ DEFAULT now(),
  notes TEXT,
  PRIMARY KEY (report_id, flag)
);

CREATE INDEX IF NOT EXISTS idx_content_flags_report_id ON content_flags(report_id);

-- ============================================================================
-- Verification Queries
-- ============================================================================

/*
-- Verify the columns were added
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'reports' 
  AND column_name IN ('embedding', 'customer_id', 'region', 'pii_flag', 'crdb_version');

-- Check new tables
SHOW TABLES;
*/
