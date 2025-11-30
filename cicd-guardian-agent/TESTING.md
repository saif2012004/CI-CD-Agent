# 🧪 Testing Guide

## Running the Project Locally

### Method 1: Using Batch Files (Windows)

#### Start the Server:
```bash
run_server.bat
```
This will:
- Install all dependencies
- Start the server on http://localhost:8000
- Show API docs at http://localhost:8000/docs

#### Run Tests:
Open a new terminal and run:
```bash
run_tests.bat
```

### Method 2: Manual Commands

#### Install Dependencies:
```bash
pip install -r requirements.txt
```

#### Start Server:
```bash
python -m uvicorn src.agent:app --reload --port 8000
```

#### Run Tests (in another terminal):
```bash
pip install requests
python test_agent.py
```

## Test Coverage

The test suite (`test_agent.py`) includes:

### ✅ Test 1: Health Check
- Verifies the `/health` endpoint
- Checks agent status and memory
- Expected: 200 OK with agent info

### ✅ Test 2: Critical Failure Analysis
Tests pipeline with multiple critical issues:
- Security vulnerabilities (CVEs)
- Direct push to protected branch
- Low test coverage (65%)
- No PR approval
- Build failure

Expected response:
- **Severity**: Critical
- **Anomalies**: Multiple detected
- **Escalate**: Yes

### ✅ Test 3: Successful Pipeline Analysis
Tests pipeline with no issues:
- 95% test coverage
- Feature branch (not protected)
- PR approved with 2 reviewers
- No vulnerabilities
- Build success

Expected response:
- **Severity**: None
- **Anomalies**: None
- **Escalate**: No

### ✅ Test 4: Metrics
- Verifies metrics endpoint
- Checks aggregated statistics
- Expected: Total pipelines, success rate, etc.

### ✅ Test 5: API Documentation
- Verifies Swagger UI is accessible
- Expected: 200 OK at `/docs`

## Manual Testing

### Using cURL

#### Health Check:
```bash
curl http://localhost:8000/health
```

#### Analyze Pipeline:
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_id": "test-123",
    "status": "failed",
    "duration_seconds": 450,
    "logs": "Build failed",
    "vulnerabilities": ["CVE-2023-12345"],
    "branch": "main",
    "commit_sha": "abc123",
    "test_coverage_percent": 65.0,
    "is_direct_push": true,
    "pr_approved": false,
    "pr_reviewers_count": 0
  }'
```

#### Get Metrics:
```bash
curl http://localhost:8000/metrics
```

### Using Postman

1. Import the API at: http://localhost:8000/docs
2. Use the built-in Swagger UI to test endpoints
3. All endpoints have interactive forms

### Using Python

```python
import requests

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())

# Analyze pipeline
data = {
    "pipeline_id": "test-123",
    "status": "failed",
    "duration_seconds": 450,
    "logs": "Build failed",
    "vulnerabilities": ["CVE-2023-12345"],
    "branch": "main",
    "commit_sha": "abc123",
    "test_coverage_percent": 65.0,
    "is_direct_push": True,
    "pr_approved": False,
    "pr_reviewers_count": 0
}

response = requests.post("http://localhost:8000/analyze", json=data)
print(response.json())
```

## Expected Test Results

### All Tests Pass:
```
TEST SUMMARY
============================================================
Health Check: ✅ PASSED
Critical Failure Analysis: ✅ PASSED
Success Analysis: ✅ PASSED
Metrics: ✅ PASSED
API Docs: ✅ PASSED

Total: 5/5 tests passed

🎉 All tests passed! The agent is working correctly.
```

## Test Scenarios

### Scenario 1: Critical Security Issue
```json
{
  "vulnerabilities": ["CVE-2023-12345"],
  "status": "failed"
}
```
**Expected**: Critical severity, escalate to supervisor

### Scenario 2: Branch Protection Violation
```json
{
  "branch": "main",
  "is_direct_push": true,
  "pr_approved": false
}
```
**Expected**: Critical severity, block merge

### Scenario 3: Insufficient Test Coverage
```json
{
  "test_coverage_percent": 65.0
}
```
**Expected**: Critical severity (below 80% threshold)

### Scenario 4: All Good
```json
{
  "status": "success",
  "test_coverage_percent": 95.0,
  "branch": "feature/test",
  "is_direct_push": false,
  "pr_approved": true,
  "pr_reviewers_count": 2,
  "vulnerabilities": []
}
```
**Expected**: No anomalies, no escalation

## Troubleshooting Tests

### Tests Fail to Connect
- **Issue**: Connection refused
- **Solution**: Ensure server is running on port 8000
- **Check**: Visit http://localhost:8000/docs

### Import Errors
- **Issue**: Module not found
- **Solution**: Install dependencies
  ```bash
  pip install -r requirements.txt
  pip install requests
  ```

### Memory Errors
- **Issue**: Database locked or corrupted
- **Solution**: Delete `src/memory.db` and `src/memory.json`, they will auto-recreate

### Server Won't Start
- **Issue**: Port already in use
- **Solution**: Kill existing process or use different port
  ```bash
  # Windows
  netstat -ano | findstr :8000
  taskkill /PID <PID> /F
  
  # Or use different port
  python -m uvicorn src.agent:app --port 8001
  ```

## Performance Testing

For load testing:

```bash
# Install locust
pip install locust

# Create locustfile.py
# Run load test
locust -f locustfile.py --host http://localhost:8000
```

## Integration Testing

Test with actual GitHub Actions:
1. Push code to GitHub
2. Trigger workflow in `.github/workflows/guardian-demo.yml`
3. Check agent receives and processes the request

## Next Steps After Testing

Once all tests pass:
1. ✅ Server runs successfully
2. ✅ All endpoints respond correctly  
3. ✅ Anomaly detection works
4. ✅ Metrics are tracked

**You're ready to deploy to Render!** 🚀

See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment instructions.

