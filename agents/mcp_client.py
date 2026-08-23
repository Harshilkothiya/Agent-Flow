import asyncio
from contextlib import asynccontextmanager
from fastmcp.client import Client
from langchain_mcp_adapters.tools import load_mcp_tools

import os

# ---------------------------------------------------------
# Connects to the running MCP Server via HTTP Stream
# Run 'python mcp_server/server.py' in a separate terminal first
# ---------------------------------------------------------
@asynccontextmanager
async def mcp_session(url=None):
    if url is None:
        url = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8000/mcp")
        
    # FastMCP's unified client handles the SSE transport connection automatically
    async with Client(url) as client:
        # Pass the underlying raw session to LangChain to convert them to tools
        tools = await load_mcp_tools(client.session)
        yield client, tools
