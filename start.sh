#!/bin/bash

echo "Starting MCP Backend Server..."
python mcp_server/server.py &

# Wait a moment to ensure the server starts properly
sleep 3

echo "Starting Streamlit UI on port 7860..."
streamlit run app.py --server.port=7860 --server.address=0.0.0.0 --server.headless=true
