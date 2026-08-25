import os
import sys
import warnings

# Suppress annoying warnings (like the Pydantic one)
warnings.filterwarnings("ignore")

# Add the project root to sys.path so Python can find 'mcp_server' and 'rag'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastmcp import FastMCP

# Create the MCP server
mcp = FastMCP("AgentPlatform")

# Import our tools
from mcp_server.tools.generate_report import generate_report
from mcp_server.tools.query_structured_data import query_structured_data
from mcp_server.tools.search_documents import search_documents
from mcp_server.tools.summarize_document import summarize_document

# Register the tools with the MCP server
mcp.tool()(search_documents)
mcp.tool()(summarize_document)
mcp.tool()(query_structured_data)
mcp.tool()(generate_report)

if __name__ == "__main__":
    # Run the server using SSE (Server-Sent Events) transport over HTTP
    mcp.run(transport="http", host="0.0.0.0", port=8000)
