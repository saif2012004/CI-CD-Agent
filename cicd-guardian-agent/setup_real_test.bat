@echo off
REM Quick setup script for testing Guardian Agent with a real repository

echo ============================================
echo CI/CD Guardian Agent - Real Repository Test
echo ============================================
echo.

REM Check if agent is running
echo 1. Checking if Guardian Agent is running...
curl -s http://localhost:8000/health >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo    OK Agent is running at http://localhost:8000
) else (
    echo    X Agent is not running!
    echo    Please start it first:
    echo    python -m uvicorn src.agent:app --port 8000
    echo.
    pause
    exit /b 1
)

echo.
echo 2. Choose testing method:
echo    a^) Local testing with ngrok ^(temporary URL^)
echo    b^) Use deployed Render URL ^(permanent^)
echo    c^) Test with curl only ^(no GitHub integration^)
echo.
set /p choice="Enter choice (a/b/c): "

if "%choice%"=="c" goto curl_test
if "%choice%"=="a" goto ngrok_setup
if "%choice%"=="b" goto render_setup
goto invalid_choice

:ngrok_setup
echo.
echo Setting up ngrok...
echo You need ngrok installed: https://ngrok.com/download
echo.
pause
echo.
echo Starting ngrok tunnel...
echo Run this in a NEW COMMAND PROMPT:
echo.
echo   ngrok http 8000
echo.
echo Then copy the HTTPS URL (e.g., https://abc123.ngrok-free.app)
set /p ngrok_url="Enter your ngrok URL: "
set AGENT_URL=%ngrok_url%
goto github_setup

:render_setup
echo.
set /p render_url="Enter your Render URL (e.g., https://cicd-guardian-agent.onrender.com): "
set AGENT_URL=%render_url%
goto github_setup

:curl_test
echo.
echo Testing with curl...
echo.
echo Test 1: Health Check
curl http://localhost:8000/health
echo.
echo.

echo Test 2: Analyze Critical Failure
curl -X POST http://localhost:8000/analyze -H "Content-Type: application/json" -d "{\"pipeline_id\":\"manual-test-123\",\"status\":\"failed\",\"duration_seconds\":300,\"logs\":\"Manual test\",\"vulnerabilities\":[\"CVE-2023-12345\"],\"branch\":\"main\",\"commit_sha\":\"abc123\",\"test_coverage_percent\":65.0,\"is_direct_push\":true,\"pr_approved\":false,\"pr_reviewers_count\":0}"
echo.
echo.

echo Test 3: Check Metrics
curl http://localhost:8000/metrics
echo.
echo.

echo OK Manual curl testing complete!
echo Visit http://localhost:8000/docs for interactive testing
pause
exit /b 0

:github_setup
echo.
echo 3. GitHub Repository Setup
echo.
echo To integrate with GitHub Actions:
echo.
echo Step 1: Go to your test repository on GitHub
echo.
echo Step 2: Add this file: .github/workflows/test-guardian.yml
echo         (File already created in this project)
echo.
echo Step 3: Add GitHub Secret:
echo         Repository -^> Settings -^> Secrets -^> Actions
echo         Name: GUARDIAN_AGENT_URL
echo         Value: %AGENT_URL%
echo.
echo Step 4: Make a test commit:
echo.
echo         git add .github/workflows/test-guardian.yml
echo         git commit -m "Add Guardian Agent"
echo         git push origin main
echo.
echo Step 5: Watch the results:
echo         - GitHub Actions tab (workflow run)
echo         - Your agent terminal (incoming requests)
echo         - Metrics: %AGENT_URL%/metrics
echo.
echo For detailed instructions, see:
echo   - REAL_REPO_TESTING.md
echo   - QUICK_REAL_TEST.md
echo.
echo OK Setup complete!
echo.
pause
exit /b 0

:invalid_choice
echo Invalid choice
pause
exit /b 1

