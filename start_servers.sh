#!/bin/bash
# Start both frontend and backend servers
# For Linux/Mac users

echo "Starting HE Team LLM Assistant Servers..."
echo ""

# Start backend in background
echo "Starting Backend API Server on port 8000..."
python run_backend.py &
BACKEND_PID=$!

# Wait a moment for backend to initialize
sleep 2

# Start frontend in background
echo "Starting Frontend Server on port 3000..."
python run_frontend.py &
FRONTEND_PID=$!

# Wait a moment for frontend to start
sleep 2

echo ""
echo "========================================"
echo "Both servers are running!"
echo "========================================"
echo ""
echo "Backend API:  http://localhost:8000"
echo "Frontend UI:  http://localhost:3000"
echo ""
echo "Backend PID:  $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Open your browser and go to:"
echo "http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"
echo "========================================"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo "Servers stopped."
    exit 0
}

# Trap Ctrl+C and call cleanup
trap cleanup INT TERM

# Wait for user interrupt
wait
