"""
Agent Service - Standalone FastAPI service for AI-powered report generation
Runs on port 8002, separate from the main API service (port 8001)
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from mcp_agent.core.fastagent import FastAgent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create FastAgent instance (without parsing CLI args for FastAPI compatibility)
reporter = FastAgent("Report Generator", parse_cli_args=False, quiet=False)


# Register the agent via decorator
@reporter.agent(
    name="performance_analyzer",
    instruction="You are an expert at database performance analysis and optimization. Analyze CockroachDB cluster metrics and provide actionable recommendations.",
    servers=["reporter"],
    default=True
)
async def performance_analyzer():
    pass


# Keep FastAgent running for the app lifetime
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage FastAgent lifecycle with FastAPI"""
    async with reporter.run() as agents:
        app.state.agents = agents
        yield


# Create FastAPI application for agent service
app = FastAPI(
    title="CRDB Agent Service API",
    description="AI-powered report generation service for CockroachDB cluster analysis",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateReportRequest(BaseModel):
    """Request model for report generation"""
    database: str = "bookly"
    app: str = "bookly"
    prompt: Optional[str] = None


class GenerateReportResponse(BaseModel):
    """Response model for report generation"""
    success: bool
    error: Optional[str] = None


def build_prompt(database: str, app_name: str, custom_prompt: Optional[str] = None) -> str:
    """Build the analysis prompt for the agent"""
    if custom_prompt:
        return custom_prompt
    
    return f"""
Please analyze the CockroachDB cluster performance for the '{database}' database and '{app_name}' application.

**Step 1: Gather Data**
Use the cluster metrics tools to collect:
1. Cluster Topology - node configuration and locality
2. Database Schema - tables, columns, indexes, and zone configurations for '{database}'
3. CPU Usage - CPU metrics across all nodes
4. Slow Statements - slow-performing queries for '{app_name}' application

**Step 2: Create Report in Database**
After gathering the data, you MUST create a report in the database using these tools:

1. Create a new report using `create_new_report_api_v1_reports_post`:
   - cluster_id: "{database}"
   - title: "Performance Analysis for {database} - {app_name}"
   - description: Brief summary of the analysis

2. For each performance issue found, create findings using `create_finding_for_report_api_v1_reports`:
   - Category examples: "indexing", "cpu", "schema", "queries"
   - Severity: "low", "medium", or "high"
   - Include detailed description

3. For each finding, create actionable recommendations using `create_action_for_finding_api_v1_findings`:
   - action_type: "optimization", "configuration", "monitoring", etc.
   - Include specific SQL or configuration changes

**Step 3: Use tools to Update the report description with the Summary**
After creating the report in the database, use the `update_report_api_v1_reports` tool to update the report description with the summary of:
- Report ID created
- Number of findings
- Number of actions recommended
- Key performance insights

**Step 4: Return Success Message**
After updating the report description, return a success message using the response model for report generation:
    success: bool
    error: Optional[str] = None
"""


@app.post("/generate-report", response_model=GenerateReportResponse)
async def generate_report(request: GenerateReportRequest):
    """
    Generate an AI-powered performance report for the specified database and application
    """
    try:
        print(f"[INFO] Generating report for database={request.database}, app={request.app}")
        
        # Build the prompt
        prompt = build_prompt(request.database, request.app, request.prompt)
        
        # Send to the agent (reuses the persistent agent from app.state)
        result = await app.state.agents.send(prompt)
        
        print(f"[INFO] Report generated successfully, length={len(result) if result else 0}")
        return GenerateReportResponse(
            success=True,
            # report=result we don't need to return the report
            
        )
    except Exception as e:
        import traceback
        print(f"[ERROR] Failed to generate report: {e}")
        print(f"[ERROR] Traceback:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate report: {str(e)}"
        )


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "CRDB Agent Service API",
        "version": "1.0.0",
        "main_api": "http://localhost:8001"
    }


@app.get("/health")
async def health():
    """Check if the agent service is available"""
    return {"status": "healthy", "service": "agent"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
