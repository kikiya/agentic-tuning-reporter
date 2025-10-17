import sys
import os
from pathlib import Path

# Add parent directory to path to import main
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from fastmcp import FastMCP

# Convert to MCP server
mcp = FastMCP.from_fastapi(app=app)

if __name__ == "__main__":
    mcp.run()