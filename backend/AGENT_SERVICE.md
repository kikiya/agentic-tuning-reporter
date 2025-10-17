# Agent Service Architecture

## Overview

The system is split into **two separate FastAPI services** to avoid circular dependencies and enable independent development.

## Services

### 1. Main API Service (Port 8001)
**File:** `main.py`

**Responsibilities:**
- Cluster metrics endpoints (`/api/v1/cluster/*`)
- Reports CRUD operations (`/api/v1/reports/*`)
- Direct database connection
- CockroachDB API integration

**Endpoints:**
- `GET /api/v1/cluster/topology`
- `GET /api/v1/cluster/schema/{database}`
- `GET /api/v1/cluster/cpu-usage`
- `GET /api/v1/cluster/slow-statements`
- `GET /api/v1/cluster/all`
- Plus reports CRUD endpoints

### 2. Agent Service (Port 8002)
**File:** `agent_main.py`

**Responsibilities:**
- AI-powered report generation
- Uses FastAgent with MCP server
- Consumes Main API functionality via MCP tools
- No direct database connection

**Endpoints:**
- `POST /generate-report` - Generate AI report
- `GET /health` - Health check
- `GET /` - Service info

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                     Agent Service (8002)                     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │          FastAgent (AI Agent)                      │    │
│  │  - Receives user prompt                            │    │
│  │  - Calls MCP tools to gather data                  │    │
│  │  - Generates report using Claude                   │    │
│  └────────────────┬───────────────────────────────────┘    │
│                   │                                          │
│                   │ Uses MCP Tools                           │
│                   ▼                                          │
│  ┌────────────────────────────────────────────────────┐    │
│  │      MCP Server (reporter_mcp.py)                  │    │
│  │  - Converts FastAPI routes to MCP tools            │    │
│  │  - FastMCP.from_fastapi(app)                       │    │
│  └────────────────┬───────────────────────────────────┘    │
└───────────────────┼──────────────────────────────────────────┘
                    │
                    │ Imports main.py app
                    │ (with env vars set by FastAgent)
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                   Main API Service (8001)                    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │          FastAPI App (main.py)                     │    │
│  │  - Cluster metrics routes                          │    │
│  │  - Reports CRUD routes                             │    │
│  └────────────────┬───────────────────────────────────┘    │
│                   │                                          │
│                   │ Direct connection                        │
│                   ▼                                          │
│  ┌────────────────────────────────────────────────────┐    │
│  │          CockroachDB Cluster                       │    │
│  │  - Database queries                                │    │
│  │  - Cluster API calls                               │    │
│  └────────────────────────────���───────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Key Points

1. **No Circular Dependencies**: Agent service imports main.py through the MCP server, but main.py doesn't import agent code

2. **Environment Variables**: The MCP server needs CockroachDB connection details (DATABASE_URL, SESSION_COOKIE, etc.) which are passed via `fastagent.secrets.yaml`

3. **Independent Development**: You can develop and test each service separately

4. **MCP Magic**: `FastMCP.from_fastapi(app)` automatically converts all FastAPI routes into MCP tools that the agent can call

## Starting the Services

### Terminal 1: Main API
```bash
cd /Users/kiki/development/agentic-tuning-reporter/backend
source venv/bin/activate
python main.py
```

### Terminal 2: Agent Service
```bash
cd /Users/kiki/development/agentic-tuning-reporter/backend
source venv/bin/activate
python agent_main.py
```

## Testing

```bash
# Test main API
curl http://localhost:8001/health

# Test agent service
curl http://localhost:8002/health

# Generate a report
curl -X POST "http://localhost:8002/generate-report" \
  -H "Content-Type: application/json" \
  -d '{"database": "bookly", "app": "bookly"}'
```

## UI Integration

Your frontend should call:
- **Port 8001** for cluster metrics and reports CRUD
- **Port 8002** for AI-powered report generation

Example:
```javascript
// Get cluster metrics
const metrics = await fetch('http://localhost:8001/api/v1/cluster/all');

// Generate AI report
const report = await fetch('http://localhost:8002/generate-report', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ database: 'bookly', app: 'bookly' })
});
```
