# 🎯 Testing Your Guardian Agent with a Real Repository

## ✅ Your agent is currently running at: http://localhost:8000

---

## 🚀 Quick Start - 3 Methods

### Method 1: Test with curl (Easiest - No GitHub needed)

```bash
# Windows
setup_real_test.bat

# Linux/Mac
chmod +x setup_real_test.sh
./setup_real_test.sh
```

Choose option `c` for curl testing.

---

### Method 2: Test with Your Existing Repository

1. **Copy the workflow file to your repository:**
   ```bash
   # Copy this file to your test repository
   cp .github/workflows/test-guardian.yml YOUR_REPO/.github/workflows/
   ```

2. **Expose your local agent:**
   ```bash
   # Download ngrok: https://ngrok.com/download
   ngrok http 8000
   ```
   Copy the URL (e.g., `https://abc123.ngrok-free.app`)

3. **Add GitHub Secret:**
   - Go to your repository on GitHub
   - Settings → Secrets and variables → Actions
   - New repository secret:
     - Name: `GUARDIAN_AGENT_URL`
     - Value: Your ngrok URL

4. **Push a commit:**
   ```bash
   cd YOUR_REPO
   git add .github/workflows/test-guardian.yml
   git commit -m "Add Guardian Agent"
   git push origin main
   ```

5. **Watch the results:**
   - GitHub Actions tab (see workflow run)
   - Your terminal (see incoming requests to agent)
   - http://localhost:8000/metrics (see aggregated data)

---

### Method 3: Test with This Repository (Self-Test)

This repository already has the workflow configured!

1. **Ensure agent is running:**
   ```bash
   python -m uvicorn src.agent:app --port 8000
   ```

2. **Expose with ngrok:**
   ```bash
   ngrok http 8000
   ```

3. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Test Guardian Agent"
   git push origin main
   ```

4. **Add the ngrok URL as a GitHub Secret:**
   - Go to this repository on GitHub
   - Settings → Secrets → GUARDIAN_AGENT_URL → Your ngrok URL

5. **Watch the workflow run in Actions tab!**

---

## 🎮 Test Scenarios

### Scenario 1: Clean Build (All Good ✅)

```bash
git checkout -b feature/clean-code
echo "# Clean code" > clean.py
git add clean.py
git commit -m "Add clean feature"
git push origin feature/clean-code
```

**Expected:**
- ✅ No anomalies
- ✅ Build passes
- ✅ No escalation

### Scenario 2: Direct Push to Main (Violation 🚨)

```bash
git checkout main
echo "# Bad practice" > direct.py
git add direct.py
git commit -m "Direct push to main"
git push origin main
```

**Expected:**
- 🚨 Branch protection violation
- 🚨 Critical severity
- ❌ Workflow fails

### Scenario 3: Simulate Low Coverage (Warning 🚨)

Edit `.github/workflows/test-guardian.yml` and change coverage to 60:

```yaml
COVERAGE="60.0"
```

**Expected:**
- 🚨 Test coverage violation
- 🚨 Critical severity

---

## 📊 Check Results

### In GitHub Actions:
- Go to Actions tab
- Click on latest workflow run
- See Guardian Agent analysis output

### In Your Terminal:
- Watch real-time logs from the agent
- See incoming POST requests

### Via Metrics API:
```bash
curl http://localhost:8000/metrics | jq
```

### Via Web UI:
http://localhost:8000/docs

---

## 🌐 For Production Testing

After deploying to Render:

1. **Update GitHub Secret:**
   ```
   GUARDIAN_AGENT_URL = https://cicd-guardian-agent.onrender.com
   ```

2. **No need for ngrok!** The agent is permanently accessible.

3. **All your repositories** can use the same agent URL.

---

## 📚 Documentation

- **REAL_REPO_TESTING.md** - Detailed testing guide
- **QUICK_REAL_TEST.md** - Quick reference
- **DEPLOYMENT.md** - Deploy to Render
- **.github/workflows/test-guardian.yml** - GitHub Actions workflow

---

## 🐛 Troubleshooting

**Issue: GitHub Actions can't reach agent**
- Solution: Make sure ngrok is running and URL is correct

**Issue: No data showing in metrics**
- Solution: Check agent logs, verify workflow completed

**Issue: Workflow fails immediately**
- Solution: Check GitHub Actions logs for errors

**Quick test without GitHub:**
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_id": "test-123",
    "status": "failed",
    "duration_seconds": 300,
    "logs": "Test",
    "vulnerabilities": ["CVE-2023-12345"],
    "branch": "main",
    "commit_sha": "abc123",
    "test_coverage_percent": 65,
    "is_direct_push": true,
    "pr_approved": false,
    "pr_reviewers_count": 0
  }'
```

---

## 🎯 Summary

You now have **3 options** to test with a real repository:

1. ✅ **curl** - Immediate testing, no GitHub needed
2. ✅ **ngrok + GitHub** - Test with real CI/CD workflows
3. ✅ **Render** - Production testing with permanent URL

Choose the one that fits your needs! 🚀

**Your agent is ready at: http://localhost:8000** 🛡️

