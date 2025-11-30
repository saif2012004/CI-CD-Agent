# 🧪 Testing with Real Repository

## Overview

This guide shows you how to test the CI/CD Guardian Agent with a real GitHub repository and actual CI/CD pipelines.

---

## 🏠 Option 1: Testing Locally (Before Deployment)

### Step 1: Expose Your Local Server

Since GitHub Actions runs in the cloud, you need to expose your local server using one of these methods:

#### Method A: Using ngrok (Recommended for Testing)

1. **Install ngrok:**
   - Download from: https://ngrok.com/download
   - Sign up for free account
   - Install ngrok

2. **Start your Guardian Agent:**
   ```bash
   python -m uvicorn src.agent:app --port 8000
   ```

3. **In a new terminal, expose with ngrok:**
   ```bash
   ngrok http 8000
   ```

4. **Copy the ngrok URL:**
   ```
   Forwarding https://abc123.ngrok-free.app -> http://localhost:8000
   ```

#### Method B: Using localtunnel

1. **Install localtunnel:**
   ```bash
   npm install -g localtunnel
   ```

2. **Start your Guardian Agent:**
   ```bash
   python -m uvicorn src.agent:app --port 8000
   ```

3. **Expose with localtunnel:**
   ```bash
   lt --port 8000 --subdomain my-guardian
   ```

### Step 2: Configure GitHub Repository

1. **Go to your test repository on GitHub**
   - Can be any repository (or create a new test one)

2. **Add the workflow file:**
   - Copy `.github/workflows/test-guardian.yml` to your repository

3. **Add GitHub Secret:**
   - Go to: Repository → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `GUARDIAN_AGENT_URL`
   - Value: Your ngrok/localtunnel URL (e.g., `https://abc123.ngrok-free.app`)
   - Click "Add secret"

### Step 3: Test the Integration

1. **Make a test commit:**
   ```bash
   # In your test repository
   echo "Test commit" >> README.md
   git add README.md
   git commit -m "Test Guardian Agent"
   git push origin main
   ```

2. **Watch GitHub Actions:**
   - Go to your repository → Actions tab
   - Watch the workflow run
   - Check the "Send analysis to Guardian Agent" step

3. **Check Your Local Agent:**
   - Look at your terminal running the agent
   - Check logs: `logs/agent.log`
   - Visit: http://localhost:8000/metrics

---

## 🌐 Option 2: Testing with Deployed Agent (Production)

### Step 1: Deploy to Render

Follow the [DEPLOYMENT.md](DEPLOYMENT.md) guide to deploy your agent to Render.

Your agent will be at: `https://cicd-guardian-agent.onrender.com`

### Step 2: Configure GitHub Repository

1. **Add GitHub Secret:**
   - Repository → Settings → Secrets → Actions
   - Name: `GUARDIAN_AGENT_URL`
   - Value: `https://cicd-guardian-agent.onrender.com`

2. **Add the workflow:**
   - Copy `.github/workflows/test-guardian.yml` to your repository
   - Commit and push

### Step 3: Test the Integration

1. **Push a commit to trigger the workflow**

2. **Check the workflow results:**
   - GitHub Actions tab → Latest run
   - See Guardian Agent analysis results

3. **Check your deployed agent:**
   - Visit: `https://cicd-guardian-agent.onrender.com/metrics`
   - See the analysis data

---

## 🧪 Test Scenarios

### Scenario 1: Clean Build (Should Pass)

Create a feature branch with good practices:

```bash
git checkout -b feature/test-clean
echo "Good code" >> test.py
git add test.py
git commit -m "Add clean feature"
git push origin feature/test-clean

# Create PR
gh pr create --title "Clean feature" --body "Testing clean build"
```

**Expected Result:**
- ✅ Build succeeds
- ✅ No anomalies detected
- ✅ No escalation

### Scenario 2: Direct Push to Main (Should Fail)

```bash
git checkout main
echo "Bad practice" >> file.txt
git add file.txt
git commit -m "Direct push to main"
git push origin main
```

**Expected Result:**
- 🚨 Branch protection violation detected
- 🚨 Critical severity
- 🚨 Escalate to supervisor
- ❌ Workflow should fail

### Scenario 3: Low Test Coverage (Should Warn)

Modify the workflow to simulate low coverage:

```yaml
# In .github/workflows/test-guardian.yml
# Manually set coverage to 60%
COVERAGE="60.0"
```

**Expected Result:**
- 🚨 Insufficient test coverage detected
- 🚨 Critical severity
- ❌ Workflow fails

### Scenario 4: Security Vulnerabilities

Install vulnerable packages:

```bash
pip install requests==2.6.0  # Old version with CVEs
pip-audit --format json
```

**Expected Result:**
- 🚨 Security vulnerabilities detected
- 🚨 CVEs listed
- 🚨 Critical severity

---

## 📊 Monitoring Test Results

### 1. GitHub Actions Output

Check the workflow logs:
```
✅ Guardian Agent analysis complete!
📊 Analysis Results:
  - Severity: critical
  - Anomalies detected: 3
  - Escalate to supervisor: True

🚨 CRITICAL ISSUES DETECTED - Blocking merge!

📋 Issues found:
  - [critical] Direct push to protected branch 'main' is not allowed
  - [critical] Test coverage (60%) is below minimum (80%)
  - [high] Build failure detected
```

### 2. Agent Logs

Check your agent's logs:

```bash
# Local
tail -f logs/agent.log

# Render
# Go to Render dashboard → Your service → Logs
```

### 3. Metrics Dashboard

Visit the metrics endpoint:

```bash
# Local
curl http://localhost:8000/metrics

# Deployed
curl https://cicd-guardian-agent.onrender.com/metrics
```

### 4. API Documentation

Test manually via Swagger UI:

```bash
# Local
http://localhost:8000/docs

# Deployed
https://cicd-guardian-agent.onrender.com/docs
```

---

## 🔧 Advanced Testing

### Testing with Multiple Repositories

1. Add the workflow to multiple repositories
2. Use the same Guardian Agent URL
3. Monitor all pipelines from one agent
4. Check aggregated metrics

### Testing Different CI/CD Platforms

#### Jenkins

```groovy
// Jenkinsfile
post {
    always {
        sh """
        curl -X POST $GUARDIAN_URL/analyze \
          -H 'Content-Type: application/json' \
          -d '{
            "pipeline_id": "${BUILD_ID}",
            "status": "${currentBuild.result}",
            "duration_seconds": ${currentBuild.duration / 1000},
            "branch": "${BRANCH_NAME}",
            "commit_sha": "${GIT_COMMIT}"
          }'
        """
    }
}
```

#### GitLab CI

```yaml
# .gitlab-ci.yml
after_script:
  - |
    curl -X POST $GUARDIAN_URL/analyze \
      -H "Content-Type: application/json" \
      -d "{
        \"pipeline_id\": \"$CI_PIPELINE_ID\",
        \"status\": \"$CI_JOB_STATUS\",
        \"branch\": \"$CI_COMMIT_REF_NAME\",
        \"commit_sha\": \"$CI_COMMIT_SHA\"
      }"
```

---

## 🐛 Troubleshooting

### Issue: GitHub Actions can't reach local agent

**Solution:**
- Ensure ngrok/localtunnel is running
- Check the URL is correct in GitHub secrets
- Verify your local agent is running
- Check firewall settings

### Issue: "Connection refused" in workflow

**Solution:**
```bash
# Test the URL manually
curl https://your-ngrok-url.ngrok-free.app/health

# If it fails, restart ngrok and update GitHub secret
```

### Issue: Agent receives data but shows errors

**Solution:**
- Check agent logs: `logs/agent.log`
- Verify payload format matches expected schema
- Test with the Swagger UI first: `/docs`

### Issue: Workflow runs but no data in metrics

**Solution:**
- Check if the workflow step completed
- Verify the agent URL in GitHub secrets
- Check agent is actually receiving requests (check logs)
- Look for errors in GitHub Actions logs

---

## 📈 Measuring Success

After running multiple test scenarios, verify:

1. **Agent Health:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Total Pipelines Analyzed:**
   ```bash
   curl http://localhost:8000/metrics | jq '.total_pipelines_analyzed'
   ```

3. **Anomaly Detection Rate:**
   - Check metrics for detected anomalies
   - Verify false positives/negatives

4. **Response Time:**
   - Check workflow execution time
   - Ensure agent responds within 30 seconds

---

## 🎯 Next Steps

After successful testing:

1. ✅ Deploy to Render (permanent URL)
2. ✅ Add workflow to production repositories
3. ✅ Configure Slack notifications
4. ✅ Set up monitoring/alerting
5. ✅ Document your team's policies in `config/rules.yaml`

---

## 📚 Related Documentation

- [DEPLOYMENT.md](DEPLOYMENT.md) - Deploy to Render
- [TESTING.md](TESTING.md) - Local testing guide
- [QUICKSTART.md](QUICKSTART.md) - Quick setup guide
- [README.md](README.md) - Full documentation

---

**Happy Testing! 🎉**

Your CI/CD Guardian Agent is now protecting your pipelines in real-time!

