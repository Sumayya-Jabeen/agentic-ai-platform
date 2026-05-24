#!/bin/bash

echo "========================================"
echo "  Agentic AI Platform — Starting Up"
echo "========================================"

# Kill any existing processes
pkill -f uvicorn 2>/dev/null
pkill -f "serve frontend" 2>/dev/null
sleep 1

# Create venv if missing
if [ ! -d "venv" ]; then
  echo "[1/4] Creating virtual environment..."
  python3 -m venv venv
  source venv/bin/activate
  pip install -r backend/requirements.txt
else
  echo "[1/4] Activating virtual environment..."
  source venv/bin/activate
fi

# Install backend deps if needed
echo "[2/4] Checking backend dependencies..."
pip install -r backend/requirements.txt -q

# Always rebuild frontend so the latest code is served
echo "[3/4] Building frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
  npm install
fi
npm run build
cd ..

# Start backend in the background, immune to SSH disconnects
echo "[4/4] Starting backend on port 8000..."
cd backend
nohup ../venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
cd ..

# Start frontend in the background, immune to SSH disconnects
echo "      Starting frontend on port 3000..."
nohup npx serve frontend/out -p 3000 > frontend.log 2>&1 &

sleep 2

echo ""
echo "========================================"
echo "  Backend  → http://localhost:8000"
echo "  Frontend → http://localhost:3000"
echo "  API Docs → http://localhost:8000/docs"
echo "========================================"
echo "  Servers run in the background."
echo "  Logs:    tail -f backend.log  or  tail -f frontend.log"
echo "  Stop:    ./stop.sh"
echo "  You can safely close this terminal."
echo "========================================"
