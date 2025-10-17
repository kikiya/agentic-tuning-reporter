# MCP Server

This directory contains the Model Context Protocol (MCP) server that exposes the Main API endpoints as tools for the AI agent.

## What is MCP?

MCP (Model Context Protocol) is a protocol that allows AI agents to interact with external tools and services. In this application, the MCP server converts FastAPI endpoints into callable tools that the agent can use.

## File

- **`reporter_mcp.py`** - MCP server that exposes Main API routes as tools

## How It Works

```python
from main import app  # Import the Main API FastAPI app
from fastmcp import FastMCP

# Automatically convert all FastAPI routes to MCP tools
mcp = FastMCP.from_fastapi(app=app)
```

The agent can then call tools like:
- `get_cluster_topology_api_v1_cluster_topology_get` - Get cluster topology
- `get_database_schema_api_v1_cluster_schema_database_get` - Get database schema
- `create_new_report_api_v1_reports_post` - Create a new report
- And all other Main API endpoints...

## Configuration

The MCP server is configured in `../fastagent.config.yaml`:

```yaml
mcp:
  servers:
    reporter:
      command: "python"
      args: ["mcp/reporter_mcp.py"]
```

Environment variables are passed from `fastagent.secrets.yaml` to the MCP server, allowing it to connect to the database and CockroachDB cluster.

## Testing

Test the MCP server directly with the MCP Inspector:

```bash
cd backend
npx @modelcontextprotocol/inspector python mcp/reporter_mcp.py
```

This opens a web interface where you can see all available tools and test them interactively.
