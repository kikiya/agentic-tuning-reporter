-- ============================================================================
-- Test Data: User Access Control Demo
-- ============================================================================
-- This script sets up test users, customers, and access mappings to demonstrate
-- access-controlled similarity search.
-- ============================================================================

-- ============================================================================
-- 1. Create Test Users
-- ============================================================================

-- Use UPSERT (INSERT ON CONFLICT) to handle existing users gracefully
-- This won't fail if users already exist or have foreign key references

INSERT INTO users (id, name, email, role) VALUES
  ('analyst_alice', 'Alice Johnson (Analyst)', 'alice@tuningcorp.com', 'analyst'),
  ('analyst_bob', 'Bob Smith (Analyst)', 'bob@tuningcorp.com', 'analyst'),
  ('admin_charlie', 'Charlie Davis (Admin)', 'charlie@tuningcorp.com', 'admin'),
  ('system', 'System', 'system@tuningcorp.com', 'admin')
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name,
  email = EXCLUDED.email,
  role = EXCLUDED.role;

-- ============================================================================
-- 2. Create Test Customers
-- ============================================================================

-- Insert customers and let CockroachDB auto-generate UUIDs
-- Use name as unique identifier to avoid duplicates
INSERT INTO customers (name, region, pii_allowed) 
SELECT 'Acme Corp', 'US', FALSE
WHERE NOT EXISTS (SELECT 1 FROM customers WHERE name = 'Acme Corp');

INSERT INTO customers (name, region, pii_allowed) 
SELECT 'Globex Industries', 'EU', FALSE
WHERE NOT EXISTS (SELECT 1 FROM customers WHERE name = 'Globex Industries');

-- ============================================================================
-- 3. Set Up User Access Mappings
-- ============================================================================

-- Use UPSERT to handle existing access mappings
-- Look up customer IDs by name (since they're auto-generated UUIDs)

-- Alice can only see Acme Corp reports
INSERT INTO user_access (user_id, customer_id, access_level, granted_by)
SELECT 'analyst_alice', id, 'read', 'admin_charlie'
FROM customers WHERE name = 'Acme Corp'
ON CONFLICT (user_id, customer_id) DO UPDATE SET
  access_level = EXCLUDED.access_level,
  granted_by = EXCLUDED.granted_by;

-- Bob can only see Globex Industries reports
INSERT INTO user_access (user_id, customer_id, access_level, granted_by)
SELECT 'analyst_bob', id, 'read', 'admin_charlie'
FROM customers WHERE name = 'Globex Industries'
ON CONFLICT (user_id, customer_id) DO UPDATE SET
  access_level = EXCLUDED.access_level,
  granted_by = EXCLUDED.granted_by;

-- Admin Charlie can see all reports
INSERT INTO user_access (user_id, customer_id, access_level, granted_by)
SELECT 'admin_charlie', id, 'admin', 'admin_charlie'
FROM customers WHERE name IN ('Acme Corp', 'Globex Industries')
ON CONFLICT (user_id, customer_id) DO UPDATE SET
  access_level = EXCLUDED.access_level,
  granted_by = EXCLUDED.granted_by;

-- ============================================================================
-- 4. Tag Existing Reports with Customer IDs
-- ============================================================================

-- Assign half of existing reports to Acme Corp (look up UUID by name)
UPDATE reports 
SET customer_id = (SELECT id FROM customers WHERE name = 'Acme Corp')
WHERE id IN (
  SELECT id FROM reports 
  WHERE customer_id IS NULL 
  ORDER BY created_at 
  LIMIT (SELECT (COUNT(*)/2)::INT FROM reports WHERE customer_id IS NULL)
);

-- Assign remaining reports to Globex Industries
UPDATE reports 
SET customer_id = (SELECT id FROM customers WHERE name = 'Globex Industries')
WHERE customer_id IS NULL;

-- ============================================================================
-- 5. Add Some Metadata to Demonstrate Filtering
-- ============================================================================

-- Set region for Acme Corp reports (look up UUID)
UPDATE reports 
SET region = 'US'
WHERE customer_id = (SELECT id FROM customers WHERE name = 'Acme Corp') 
  AND region IS NULL;

-- Set region for Globex reports (look up UUID)
UPDATE reports 
SET region = 'EU'
WHERE customer_id = (SELECT id FROM customers WHERE name = 'Globex Industries') 
  AND region IS NULL;

-- Mark some reports as containing PII (for demo purposes)
UPDATE reports
SET pii_flag = TRUE
WHERE customer_id = (SELECT id FROM customers WHERE name = 'Globex Industries')
  AND (
    title LIKE '%sensitive%'
    OR title LIKE '%confidential%'
    OR description LIKE '%customer data%'
  );

-- ============================================================================
-- 6. Verification Queries
-- ============================================================================

/*
-- Check users
SELECT id, name, role FROM users WHERE id IN ('analyst_alice', 'analyst_bob', 'admin_charlie');

-- Check customers
SELECT id, name, region FROM customers;

-- Check access mappings
SELECT ua.user_id, u.name, c.name as customer_name, ua.access_level
FROM user_access ua
JOIN users u ON ua.user_id = u.id
JOIN customers c ON ua.customer_id = c.id
ORDER BY ua.user_id;

-- Check report distribution
SELECT 
  customer_id,
  c.name as customer_name,
  COUNT(*) as report_count
FROM reports r
LEFT JOIN customers c ON r.customer_id = c.id
GROUP BY customer_id, c.name;

-- Test: What Alice can see
SELECT r.id, r.title, c.name as customer
FROM reports r
JOIN customers c ON r.customer_id = c.id
WHERE r.customer_id IN (
  SELECT customer_id FROM user_access WHERE user_id = 'analyst_alice'
);

-- Test: What Bob can see
SELECT r.id, r.title, c.name as customer
FROM reports r
JOIN customers c ON r.customer_id = c.id
WHERE r.customer_id IN (
  SELECT customer_id FROM user_access WHERE user_id = 'analyst_bob'
);

-- Test: What Admin can see (should be all)
SELECT r.id, r.title, c.name as customer
FROM reports r
JOIN customers c ON r.customer_id = c.id
WHERE r.customer_id IN (
  SELECT customer_id FROM user_access WHERE user_id = 'admin_charlie'
);
*/

-- ============================================================================
-- Success Message
-- ============================================================================

SELECT 
  'Setup complete!' as status,
  COUNT(DISTINCT u.id) as users_created,
  COUNT(DISTINCT c.id) as customers_created,
  COUNT(DISTINCT ua.user_id || ua.customer_id) as access_mappings
FROM users u
CROSS JOIN customers c
CROSS JOIN user_access ua
WHERE u.id IN ('analyst_alice', 'analyst_bob', 'admin_charlie')
  AND c.name IN ('Acme Corp', 'Globex Industries');

SELECT 
  'Reports tagged:' as info,
  customer_id,
  COUNT(*) as count
FROM reports
GROUP BY customer_id;
