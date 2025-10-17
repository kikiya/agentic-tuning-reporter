# CRDB Tuning Report Generator

A full-stack application for generating and managing CockroachDB cluster tuning reports with **AI-powered analysis** and comprehensive audit trails.

## ✨ Features

- **🤖 AI-Powered Analysis**: Automated performance report generation using Claude AI
- **✏️ Custom Reports**: Manual report creation with full control
- **📊 Cluster Metrics**: Real-time topology, schema, CPU, and query analysis
- **🔍 Findings & Actions**: Track issues and recommendations
- **💬 Collaboration**: Comment system for team discussions
- **📝 Audit Trails**: Complete history of all changes

## 🏗️ Architecture

The application runs as **three separate services**:

1. **Main API Service** (port 8001) - FastAPI backend for CRUD operations and cluster metrics
2. **Agent Service** (port 8002) - AI-powered report generation using FastAgent + Claude
3. **Frontend** (port 5173) - React UI with Material-UI

```
┌─────────────────┐
│   Frontend      │ (port 5173)
│   React + TS    │
└────────┬────────┘
         │
         ├─────────────────┐
         │                 │
         ▼                 ▼
┌─────────────────┐  ┌──────────────────┐
│  Main API       │  │  Agent Service   │
│  (port 8001)    │◄─┤  (port 8002)     │
│  Reports CRUD   │  │  AI Analysis     │
│  Cluster Data   │  │  FastAgent+MCP   │
└────────┬────────┘  └──────────────────┘
         │
         ▼
┌─────────────────┐
│  CockroachDB    │
│  tuning_reports │
└─────────────────┘
```

## 🚀 Quick Start

### 1. Database Setup

Run the automated setup script:

```bash
./setup-database.sh
```

Or manually run the idempotent schema:

```bash
cockroach sql --url="postgresql://root@localhost:26257" --file=schema-idempotent.sql
```

### 2. Backend Setup

#### Main API Service (Port 8001)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment (.env file)
DATABASE_URL="cockroachdb+psycopg://root@localhost:26257/tuning_reports?sslmode=disable"
COCKROACH_ALLOW_INSECURE="true"  # For local development
COCKROACHDB_API_URL="http://localhost:8080/api/v2"
COCKROACHDB_STATUS_URL="http://localhost:8080/_status/combinedstmts"
SESSION_COOKIE="your-session-cookie"

# Start Main API
python main.py
# Or: ./start-main-api.sh
```

#### Agent Service (Port 8002)

```bash
cd backend

# Ensure virtual environment is activated
source venv/bin/activate

# Configure agent (backend/fastagent.secrets.yaml)
# Add your Anthropic API key and environment variables

# Start Agent Service
python agent_main.py
# Or: ./start-agent-service.sh
```

**Important:** The Agent Service requires the Main API to be running first!

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment (optional - defaults work for local dev)
# Create .env.local file:
VITE_API_URL=http://localhost:8001/api/v1
VITE_AGENT_API_URL=http://localhost:8002

# Start the development server
npm run dev
```

### 4. Load Sample Data (Optional)

Want to test the AI agent immediately? Load the sample "bookly" database:

```bash
./load-sample-data.sh
```

This creates a database with 100,000 book records for testing report generation.

**Or use your own database:**
- Connect to your CockroachDB cluster
- Create your own database and tables
- Use your database name when generating reports

### 5. Access the Application

- **Frontend**: http://localhost:5173
- **Main API**: http://localhost:8001
- **Agent Service**: http://localhost:8002
- **API Documentation**: http://localhost:8001/docs

## 🤖 AI-Powered Report Generation

### Quick Analysis vs Custom Reports

The UI offers two ways to create reports:

#### ⚡ Quick Analysis
- **AI-powered**: Automated analysis using Claude AI
- **Fast**: Generates comprehensive reports in seconds
- **Editable**: All generated reports can be edited after creation
- **Smart**: Analyzes cluster topology, schema, CPU usage, and slow queries
- **Structured**: Creates findings and actionable recommendations automatically

**How it works:**
1. Click "New Report" in the dashboard
2. Select "Quick Analysis"
3. Enter database name and application name (try "bookly" if you loaded sample data)
4. Click "Generate"
5. AI analyzes your cluster and creates a structured report
6. Edit the report as needed

**Testing with sample data:**
- Run `./load-sample-data.sh` to create a test database
- Use database: `bookly`, app: `bookly` when generating reports

#### ✏️ Custom Report
- **Manual**: Start from scratch with full control
- **Flexible**: Create reports for any use case
- **Detailed**: Add findings and actions manually

### Agent Service Details

The Agent Service uses:
- **FastAgent**: Agentic framework for tool-calling AI
- **MCP (Model Context Protocol)**: Exposes Main API endpoints as tools
- **Claude 3.5 Haiku**: Fast, cost-effective AI model
- **Persistent Connection**: Agent stays running for fast responses

See `backend/AGENT_SERVICE.md` for detailed architecture documentation.

## 📋 Core Features

### ✅ Report Management
- Create AI-generated or custom reports
- Edit, archive, and version reports
- Track report status (draft, in_review, published, archived)
- Full audit history

### 🔍 Findings & Actions
- Document performance issues and bottlenecks
- Categorize findings (indexing, cpu, schema, queries)
- Set severity levels (low, medium, high)
- Create actionable recommendations with priority and effort estimates

### 📊 Cluster Metrics
- **Topology**: Node IDs, locality information
- **Schema**: Tables, columns, indexes, zone configurations
- **CPU Usage**: Per-node CPU metrics
- **Slow Statements**: Query performance analysis by application

### 💬 Collaboration
- Comment system for team discussions
- Threaded conversations
- User tracking and timestamps

## 🏗️ Technical Stack

### Backend Services

#### Main API (FastAPI + SQLAlchemy)
- **Synchronous Operations**: Optimized for CockroachDB
- **RESTful API**: Comprehensive CRUD endpoints
- **Type Safety**: Pydantic models for validation
- **Cluster Metrics**: Direct CockroachDB API integration
- **Audit System**: Automatic change tracking

#### Agent Service (FastAgent + MCP)
- **AI Integration**: Claude 3.5 Haiku via Anthropic API
- **MCP Server**: Converts FastAPI routes to AI tools
- **Persistent Agent**: Stays running for fast responses
- **Tool Calling**: Automated data gathering and analysis

### Frontend (React + TypeScript)
- **Material-UI**: Modern, responsive design
- **React Query**: Efficient data fetching and caching
- **TypeScript**: Full type safety
- **Vite**: Fast development and builds

### Database (CockroachDB)
- **Distributed SQL**: Optimized for CRDB's architecture
- **UUID Primary Keys**: Efficient range distribution
- **JSONB Support**: Flexible metadata storage
- **Comprehensive Indexes**: Optimized queries

## 🗄️ Database Schema

### Core Tables
- **`users`**: System users with roles (admin, analyst, reviewer, viewer)
- **`reports`**: Main tuning reports with status workflow
- **`findings`**: Issues discovered during cluster analysis
- **`recommended_actions`**: Specific tuning recommendations
- **`comments`**: Threaded discussion system

### Audit Tables
- **`report_status_history`**: Complete status change history for reports
- **`finding_status_history`**: Status changes for findings
- **`action_status_history`**: Status changes for recommended actions

## 🔧 Configuration

### Environment Variables

#### Backend - Main API (.env)
```bash
# Database connection
DATABASE_URL="cockroachdb+psycopg://root@localhost:26257/tuning_reports?sslmode=disable"

# CockroachDB cluster connection
COCKROACH_ALLOW_INSECURE="true"  # Set to "false" for production with certs
COCKROACHDB_API_URL="http://localhost:8080/api/v2"
COCKROACHDB_STATUS_URL="http://localhost:8080/_status/combinedstmts"
SESSION_COOKIE="your-session-cookie-here"

# Optional: For secure connections (production)
# COCKROACH_CERT="/path/to/client.root.crt"
# COCKROACH_KEY="/path/to/client.root.key"
# COCKROACH_CA="/path/to/ca.crt"
```

#### Backend - Agent Service (fastagent.secrets.yaml)
```yaml
anthropic:
  api_key: sk-ant-api03-your-key-here

mcp:
  servers:
    reporter:
      env:
        DATABASE_URL: "cockroachdb+psycopg://root@localhost:26257/tuning_reports?sslmode=disable"
        SESSION_COOKIE: "your-session-cookie"
        COCKROACHDB_API_URL: "http://localhost:8080/api/v2"
        COCKROACHDB_STATUS_URL: "http://localhost:8080/_status/combinedstmts"
        COCKROACH_ALLOW_INSECURE: "true"
```

#### Frontend (.env.local - optional)
```bash
# Main API Service
VITE_API_URL=http://localhost:8001/api/v1

# Agent Service
VITE_AGENT_API_URL=http://localhost:8002
```

**Note:** Frontend defaults work for local development. Only create `.env.local` if you need custom URLs.

## 📚 API Documentation

### Authentication
Currently uses simple user ID strings. Ready for JWT token implementation.

### Key Endpoints

#### Main API Service (Port 8001)

**Reports**
- `GET /api/v1/reports` - List all reports
- `POST /api/v1/reports` - Create new report
- `GET /api/v1/reports/{id}` - Get report with full details
- `PUT /api/v1/reports/{id}` - Update report
- `DELETE /api/v1/reports/{id}` - Delete report

**Findings**
- `GET /api/v1/reports/{report_id}/findings` - List findings for report
- `POST /api/v1/reports/{report_id}/findings` - Create finding
- `PUT /api/v1/findings/{finding_id}` - Update finding
- `DELETE /api/v1/findings/{finding_id}` - Delete finding

**Actions**
- `GET /api/v1/findings/{finding_id}/actions` - List actions for finding
- `POST /api/v1/findings/{finding_id}/actions` - Create action
- `PUT /api/v1/actions/{action_id}` - Update action

**Cluster Metrics**
- `GET /api/v1/cluster/topology` - Get cluster topology
- `GET /api/v1/cluster/schema/{database}` - Get database schema
- `GET /api/v1/cluster/cpu-usage` - Get CPU usage metrics
- `GET /api/v1/cluster/slow-statements` - Get slow statements
- `GET /api/v1/cluster/all` - Get all metrics in one call

#### Agent Service (Port 8002)

**AI Report Generation**
- `POST /generate-report` - Generate AI-powered performance report
  ```json
  {
    "database": "bookly",
    "app": "bookly",
    "prompt": "optional custom prompt"
  }
  ```
- `GET /health` - Agent service health check

## 🧪 Development

### Running Tests

```bash
# Backend tests (when implemented)
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test
```

### Code Quality

```bash
# Backend linting
cd backend
flake8 . --max-line-length=100

# Frontend linting
cd frontend
npm run lint
```

## 🚀 Deployment

### Backend Deployment
```bash
# Production settings
export DATABASE_URL="your-production-connection-string"
export DEBUG=false

# Run with production server
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend Deployment
```bash
cd frontend
npm run build
# Deploy the build/ folder to your web server
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Service Startup Issues

**Problem: Agent Service fails to start**
```bash
# Make sure Main API is running first
curl http://localhost:8001/health

# Check if port 8002 is available
lsof -i :8002

# Verify Anthropic API key in fastagent.secrets.yaml
```

**Problem: "Connection refused" errors**
```bash
# Check all services are running
curl http://localhost:8001/health  # Main API
curl http://localhost:8002/health  # Agent Service
curl http://localhost:5173         # Frontend

# Restart services in order:
# 1. Main API (port 8001)
# 2. Agent Service (port 8002)
# 3. Frontend (port 5173)
```

### Database Connection Issues
```bash
# Test database connection
cockroach sql --url="postgresql://root@localhost:26257"

# Check if database exists
cockroach sql --url="postgresql://root@localhost:26257" --execute="SHOW DATABASES;"

# Verify tuning_reports database
cockroach sql --url="postgresql://root@localhost:26257/tuning_reports" --execute="SHOW TABLES;"
```

### Agent Service Issues

**Problem: SSL certificate errors**
```bash
# For local development, use insecure mode
# In backend/.env:
COCKROACH_ALLOW_INSECURE="true"
COCKROACHDB_API_URL="http://localhost:8080/api/v2"  # Use http, not https

# In fastagent.secrets.yaml:
COCKROACH_ALLOW_INSECURE: "true"
```

**Problem: Agent generates report but it's not in database**
- Check the agent prompt includes instructions to create report in database
- Look for report ID in the agent response
- Check Main API logs for database errors
- Verify the agent has access to report creation tools

### Frontend Issues

**Problem: "Failed to fetch" errors**
```bash
# Check CORS settings in backend
# Verify API URLs in frontend/.env.local
VITE_API_URL=http://localhost:8001/api/v1
VITE_AGENT_API_URL=http://localhost:8002

# Clear browser cache and reload
```

**Problem: Modal doesn't open or buttons don't work**
```bash
# Check browser console for errors
# Reinstall dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Performance Issues

**Problem: AI report generation is slow**
- First request initializes MCP server (slower)
- Subsequent requests are faster (agent stays running)
- Consider upgrading to Claude 3.5 Sonnet for better quality (slower but more accurate)

**Problem: Cluster metrics timeout**
```bash
# Increase timeout in cluster_metrics.py
# Check CockroachDB cluster is responsive
curl http://localhost:8080/health.pb
```

## 📞 Support

For support and questions:
- Check the troubleshooting section above
- Review the API documentation at http://localhost:8001/docs
- Check the browser console for frontend errors
- Check backend logs for API errors
- See `backend/AGENT_SERVICE.md` for agent architecture details
