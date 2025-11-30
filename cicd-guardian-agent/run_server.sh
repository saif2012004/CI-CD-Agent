#!/bin/bash
# Start server script for Linux/Mac

echo "============================================"
echo "CI/CD Guardian Agent - Starting Server"
echo "============================================"
echo ""
echo "Installing dependencies..."
python -m pip install -r requirements.txt
echo ""
echo "Starting FastAPI server on http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo ""
echo "Press CTRL+C to stop the server"
echo ""
python -m uvicorn src.agent:app --reload --port 8000

