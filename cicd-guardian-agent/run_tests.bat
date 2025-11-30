@echo off
echo ============================================
echo CI/CD Guardian Agent - Running Tests
echo ============================================
echo.
echo Installing test dependencies...
python -m pip install requests
echo.
echo Running test suite...
python test_agent.py
echo.
pause

