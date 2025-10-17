# Quick Start Guide

Get the CRDB Tuning Report Generator running in 3 steps!

## Prerequisites

- CockroachDB running locally (port 26257)
- Python 3.8+ with pip
- Node.js 16+ with npm
- Anthropic API key (for AI features)

## Step 1: Database Setup (1 minute)

```bash
./setup-database.sh
```

This creates the `tuning_reports` database and all tables.

## Step 2: Start Backend Services (2 minutes)

### Terminal 1 - Main API (port 8001)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
DATABASE_URL="cockroachdb+psycopg://root@localhost:26257/tuning_reports?sslmode=disable"
COCKROACH_ALLOW_INSECURE="true"
COCKROACHDB_API_URL="http://localhost:8080/api/v2"
COCKROACHDB_STATUS_URL="http://localhost:8080/_status/combinedstmts"
SESSION_COOKIE="your-session-cookie"
EOF

python main.py
```

### Terminal 2 - Agent Service (port 8002)

```bash
cd backend
source venv/bin/activate

# Edit fastagent.secrets.yaml and add your Anthropic API key
# Then start the agent service
python agent_main.py
```

## Step 3: Start Frontend (1 minute)

### Terminal 3 - Frontend (port 5173)

```bash
cd frontend
npm install
npm run dev
```

## Step 4: Load Sample Data (Optional)

Want to test with sample data? Load the "bookly" database with 100,000 book records:

```bash
./load-sample-data.sh
```

This creates a test database you can use immediately for report generation.

**Or create your own database:**
- Connect to CockroachDB: `cockroach sql --insecure`
- Create your database and tables
- Load your own data
- Use your database name when generating reports

## Access the App

Open http://localhost:5173 in your browser!

## Using the App

1. Click **"New Report"** button
2. Choose **"Quick Analysis"** for AI-powered reports
3. Enter database name (e.g., "bookly") and app name
4. Click **"Generate"** and wait ~10-30 seconds
5. View and edit your generated report!

**Testing with sample data:**
- Database: `bookly`
- App: `bookly`

## Troubleshooting

**Services not starting?**
- Check all three terminals for error messages
- Ensure ports 8001, 8002, and 5173 are available
- Verify CockroachDB is running: `cockroach sql --url="postgresql://root@localhost:26257"`

**Agent service fails?**
- Make sure Main API (8001) is running first
- Check your Anthropic API key in `fastagent.secrets.yaml`
- Verify you have credits in your Anthropic account

**Frontend can't connect?**
- Check browser console for errors
- Verify both backend services are running
- Try clearing browser cache

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [backend/AGENT_SERVICE.md](backend/AGENT_SERVICE.md) for agent architecture
- Explore the API docs at http://localhost:8001/docs

Happy tuning! 🚀
