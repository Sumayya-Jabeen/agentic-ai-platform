#!/bin/bash

echo "Stopping Agentic AI Platform..."
pkill -f uvicorn 2>/dev/null && echo "Backend stopped." || echo "Backend was not running."
pkill -f "serve frontend" 2>/dev/null && echo "Frontend stopped." || echo "Frontend was not running."
echo "Done."
