# Similarity Search & Access Control Guide

This guide covers the **semantic similarity search** and **access control** features that demonstrate co-located vector embeddings with guardrails in CockroachDB.

## Overview

The application now includes:
- **Semantic similarity search** - Find conceptually similar reports using vector embeddings
- **Access control demo** - User-based filtering to show guardrails in action
- **Single-query retrieval** - Similarity + permissions enforced in one database query

This demonstrates the "co-location pattern" from the blog post: when vectors and metadata live together, retrieval becomes a bounded act of reasoning under policy constraints.

## Quick Setup

### 1. Install Dependencies

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

This installs:
- `openai>=1.0.0` - For generating embeddings
- `pgvector==0.3.6` - PostgreSQL vector extension support

### 2. Add OpenAI API Key

Edit `backend/.env`:

```bash
OPENAI_API_KEY=sk-proj-your-key-here
```

Get your key from: https://platform.openai.com/api-keys

**Cost:** ~$0.02 per 1M tokens (negligible for typical usage)

### 3. Run Database Migration

```bash
cockroach sql --url="postgresql://root@localhost:26257/tuning_reports?sslmode=disable" \
  --file=schema-add-embeddings.sql
```

This adds:
- `embedding VECTOR(1536)` columns to `reports` and `findings`
- `customers` table for multi-tenancy
- `user_access` table for access control mappings

### 4. Load Demo Users (Optional)

To demonstrate access control:

```bash
cockroach sql --url="postgresql://root@localhost:26257/tuning_reports?sslmode=disable" \
  --file=test-data-access-control.sql
```

Creates:
- **Alice Johnson** (`analyst_alice`) - Can only see Acme Corp reports
- **Bob Smith** (`analyst_bob`) - Can only see Globex Industries reports
- **Charlie Davis** (`admin_charlie`) - Admin with full access

### 5. Restart Services

```bash
# Terminal 1: Backend
cd backend && python main.py

# Terminal 2: Frontend
cd frontend && npm run dev
```

### 6. Test It!

1. Open http://localhost:5173
2. View any report detail page
3. Click **"Find Similar"** button
4. Switch between users to see different results based on access control

## How It Works

### Auto-Embedding

When reports or findings are created, the system automatically:
1. Combines `title + description` into text
2. Calls OpenAI `text-embedding-3-small` API
3. Stores the 1536-dimensional vector in the `embedding` column
4. All happens in the same transaction as the report save

```python
# backend/embedding_service.py
embedding = await generate_embedding(f"{report.title}\n{report.description}")
report.embedding = embedding
db.commit()  # Atomic: both metadata and vector
```

### Similarity Search Query

The magic happens in one SQL query:

```sql
-- Filter by access, then find similar
WITH authorized AS (
  SELECT customer_id 
  FROM user_access 
  WHERE user_id = $user_id
)
SELECT 
  r.*,
  r.embedding <-> $query_embedding AS distance
FROM reports r
WHERE r.customer_id IN (SELECT * FROM authorized)
  AND r.embedding IS NOT NULL
  AND r.status IN ('published', 'in_review')
  AND r.pii_flag = FALSE
ORDER BY distance
LIMIT 5;
```

**Key benefits:**
- Access control enforced **before** distance calculation
- ACID transaction guarantees
- `EXPLAIN ANALYZE` shows the full plan
- Prefilter by indexed columns, then compute distance on small set

### Frontend Flow

1. User clicks "Find Similar" on report detail page
2. Dialog shows user selector (Alice/Bob/Charlie)
3. API call: `GET /api/v1/reports/{id}/similar?user_id=analyst_alice`
4. Backend runs the filtered similarity query
5. Results displayed with similarity scores

## Access Control Demo

### Demo Users

| User | ID | Access | Use Case |
|------|----|---------|----|
| Alice Johnson | `analyst_alice` | Acme Corp only | Limited access |
| Bob Smith | `analyst_bob` | Globex only | Different isolation |
| Charlie Davis | `admin_charlie` | All customers | Admin view |

### Demo Script

**Scenario:** You have 10 reports (5 Acme, 5 Globex)

1. Open any report in the UI
2. Click "Find Similar"
3. **View as Alice** → See only Acme Corp similar reports (2-3 results)
4. **Switch to Bob** → See only Globex similar reports (different set)
5. **Switch to Charlie** → See ALL similar reports (4-5 results from both)

### What's Being Demonstrated

**Co-location benefits:**
- ✅ Single query enforces similarity + access control
- ✅ No "retrieve all then filter" - prefilters before distance calc
- ✅ ACID transactions eliminate consistency drift
- ✅ Standard SQL tooling (EXPLAIN, indexes, monitoring)

**vs. Separated systems:**
- ❌ Dual writes can get out of sync
- ❌ Must filter after retrieval
- ❌ Can't see full plan across two systems
- ❌ More hops, worse tail latency

## Schema Details

### Reports Table

```sql
CREATE TABLE reports (
  id UUID PRIMARY KEY,
  title STRING,
  report_text STRING,
  embedding VECTOR(1536),        -- Semantic representation
  customer_id UUID,               -- Access control boundary
  region STRING,                  -- Compliance (US, EU, etc.)
  pii_flag BOOL DEFAULT FALSE,    -- Content guardrail
  status STRING,                  -- Workflow state
  created_at TIMESTAMP,
  ...
);
```

### Access Control Tables

```sql
-- Multi-tenant customers
CREATE TABLE customers (
  id UUID PRIMARY KEY,
  name STRING NOT NULL,
  region STRING,
  created_at TIMESTAMP DEFAULT now()
);

-- User-to-customer access mappings
CREATE TABLE user_access (
  user_id STRING NOT NULL,
  customer_id UUID NOT NULL REFERENCES customers(id),
  access_level STRING DEFAULT 'read',
  PRIMARY KEY (user_id, customer_id)
);
```

### Users Table

```sql
CREATE TABLE users (
  id STRING PRIMARY KEY,
  name STRING NOT NULL,
  email STRING UNIQUE,
  role STRING DEFAULT 'analyst',  -- 'analyst' or 'admin'
  created_at TIMESTAMP DEFAULT now()
);
```

## API Endpoints

### Find Similar Reports

```
GET /api/v1/reports/{id}/similar
```

**Query Parameters:**
- `user_id` (optional) - Filter by user's accessible customers
- `enforce_access` (default: true) - Enable/disable access control
- `limit` (default: 5) - Number of results

**Response:**
```json
{
  "viewing_as": "analyst_alice",
  "access_control_enabled": true,
  "count": 3,
  "similar_reports": [
    {
      "id": "...",
      "title": "Performance Issues on Cluster X",
      "similarity_score": 0.92,
      "customer_name": "Acme Corp",
      "created_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

## Verification Queries

### Check User Access

```sql
SELECT 
  u.name,
  c.name as customer,
  COUNT(r.id) as accessible_reports
FROM users u
JOIN user_access ua ON u.id = ua.user_id
JOIN customers c ON ua.customer_id = c.id
LEFT JOIN reports r ON r.customer_id = c.id
WHERE u.id IN ('analyst_alice', 'analyst_bob', 'admin_charlie')
GROUP BY u.name, c.name;
```

### Test Similarity Search

```bash
# Alice's view
curl "http://localhost:8001/api/v1/reports/{id}/similar?user_id=analyst_alice"

# Bob's view
curl "http://localhost:8001/api/v1/reports/{id}/similar?user_id=analyst_bob"

# Admin view
curl "http://localhost:8001/api/v1/reports/{id}/similar?user_id=admin_charlie"
```

### Check Report Distribution

```sql
SELECT 
  c.name as customer,
  COUNT(*) as report_count,
  COUNT(r.embedding) as with_embeddings
FROM reports r
JOIN customers c ON r.customer_id = c.id
GROUP BY c.name;
```

## Troubleshooting

### "No similar reports found"

**Possible causes:**
1. Reports don't have embeddings yet (old data)
2. All reports are draft status
3. User has no accessible reports

**Fix:**
```sql
-- Check embeddings
SELECT COUNT(*) FROM reports WHERE embedding IS NOT NULL;

-- Check user access
SELECT COUNT(*) FROM reports r
JOIN user_access ua ON r.customer_id = ua.customer_id
WHERE ua.user_id = 'analyst_alice';

-- Publish some reports
UPDATE reports SET status = 'published' WHERE status = 'draft' LIMIT 5;
```

### "API key error"

Check `backend/.env` has:
```bash
OPENAI_API_KEY=sk-proj-...
```

Restart backend after adding the key.

### Backend errors in logs

Look for:
```
[INFO] Generated embedding for report {id}
[ERROR] OpenAI API error: ...
```

Common issues:
- Invalid API key
- API rate limits
- Network connectivity

### Column doesn't exist errors

Run the migration:
```bash
cockroach sql --file=schema-add-embeddings.sql
```

## Performance Considerations

### Query Performance

**Current approach (exact distance):**
- Prefilter by indexed columns (`customer_id`, `status`, `pii_flag`)
- Compute distance on filtered candidate set
- Fast for <1000 candidates

**For larger datasets:**
Add approximate nearest neighbor (ANN) indexes:

```sql
-- CockroachDB 24.x+ supports ANN indexes
CREATE INDEX idx_reports_embedding_ann 
  ON reports USING ivfflat(embedding)
  WHERE embedding IS NOT NULL;
```

### Recommended Indexes

```sql
-- Access control + status filtering
CREATE INDEX idx_reports_customer_status 
  ON reports(customer_id, status) 
  WHERE embedding IS NOT NULL;

-- User access lookups
CREATE INDEX idx_user_access_user 
  ON user_access(user_id, customer_id);
```

### Caching User Permissions

For production:

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_user_customers(user_id: str) -> List[UUID]:
    return db.query(UserAccess.customer_id)\
             .filter_by(user_id=user_id)\
             .all()
```

## Production Readiness

### Replace Demo Users with Real Auth

```python
# Instead of query param, extract from JWT
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

def get_current_user(token: str = Depends(security)):
    # Verify JWT token
    payload = verify_token(token)
    return payload['user_id']

@router.get("/reports/{id}/similar")
def find_similar(id: UUID, user_id: str = Depends(get_current_user)):
    # user_id now from authenticated token
    ...
```

### Add Audit Logging

```python
def log_similarity_search(user_id: str, report_id: UUID, results: List):
    audit_log.info({
        'event': 'similarity_search',
        'user_id': user_id,
        'report_id': report_id,
        'result_count': len(results),
        'timestamp': datetime.utcnow()
    })
```

### Monitoring

Track:
- Embedding generation latency
- Similarity search query performance
- OpenAI API usage and costs
- Access control violations (if any)

## Use Cases

This pattern works for any scenario needing:
- Semantic search with row-level security
- Compliance boundaries (GDPR, regional data sovereignty)
- Multi-tenant knowledge bases with isolation
- PII-aware retrieval systems
- Audit trails for access patterns

**Examples:**
- Customer support (similar tickets, customer-isolated)
- Legal documents (matter-specific access control)
- Healthcare records (HIPAA-compliant similarity search)
- Financial analysis (firm-separated research)
- Internal wikis (department-level boundaries)

## Key Takeaways

### The Single-Query Pattern

**Problem:** Separated vector DB + relational DB
- Dual writes can drift
- Post-filter after retrieval
- Two systems to monitor
- Worse tail latency

**Solution:** Co-located embeddings
- Access control before distance calculation
- Single transaction guarantees
- Full observability with EXPLAIN ANALYZE
- Simpler architecture

### When Semantics Meet Relations

From the blog post:

> "When semantics meet relations under ACID, retrieval becomes a bounded act of reasoning as opposed to simple recall."

This isn't just fetching similar items—it's reasoning about what *should be visible* under policy constraints, all in one auditable transaction.

## What's Next

Potential enhancements:
- **Hybrid search** - Combine semantic similarity with keyword filters
- **Similarity thresholds** - Configurable distance cutoffs
- **Finding similarity UI** - Findings have embeddings but no UI yet
- **Multi-modal embeddings** - Support images, logs, etc.
- **Similarity explanations** - Show why reports are similar

The core pattern is solid and extensible.

---

## Quick Reference

```bash
# Setup
cd backend && source venv/bin/activate
pip install -r requirements.txt
echo "OPENAI_API_KEY=sk-proj-..." >> .env
cockroach sql --file=schema-add-embeddings.sql
cockroach sql --file=test-data-access-control.sql  # Optional: demo users

# Start
python main.py  # Backend on 8001
cd ../frontend && npm run dev  # Frontend on 5173

# Test
open http://localhost:5173
# Open any report → Click "Find Similar" → Switch users
```

**Cost:** ~$0.02 per 1M tokens (negligible)  
**Latency:** <100ms for similarity search on filtered sets  
**Scalability:** Add ANN indexes when dataset grows large
