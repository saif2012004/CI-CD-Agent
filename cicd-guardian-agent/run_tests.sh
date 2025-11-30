#!/bin/bash
# Run tests script for Linux/Mac

echo "============================================"
echo "CI/CD Guardian Agent - Running Tests"
echo "============================================"
echo ""
echo "Installing test dependencies..."
python -m pip install requests
echo ""
echo "Running test suite..."
python test_agent.py
echo ""

