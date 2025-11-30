#!/bin/bash
# Setup script for CI/CD Guardian Agent

echo "============================================"
echo "CI/CD Guardian Agent - Setup"
echo "============================================"
echo ""

# Check Python version
echo "Checking Python version..."
python --version

if [ $? -ne 0 ]; then
    echo "❌ Python not found. Please install Python 3.11 or higher."
    exit 1
fi

echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies."
    exit 1
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the server, run:"
echo "  python -m uvicorn src.agent:app --reload --port 8000"
echo ""
echo "Or use the convenience scripts:"
echo "  Windows: run_server.bat"
echo "  Linux/Mac: ./run_server.sh"
echo ""
echo "To run tests:"
echo "  Windows: run_tests.bat"
echo "  Linux/Mac: ./run_tests.sh"
echo ""

