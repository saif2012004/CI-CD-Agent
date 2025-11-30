# 🚀 Quick Real Repository Test

## TL;DR - Fastest Way to Test with Real Repo

### 1. Start Your Local Agent (if not running)

```bash
python -m uvicorn src.agent:app --port 8000
```

### 2. Expose with ngrok

```bash
# Download ngrok from: https://ngrok.com/download
ngrok http 8000
```

Copy the URL shown (e.g., `https://abc123.ngrok-free.app`)

### 3. Add to Any GitHub Repository

Create `.github/workflows/guardian-test.yml`:

```yaml
name: Guardian Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Send to Guardian
        run: |
          curl -X POST ${{ secrets.GUARDIAN_AGENT_URL || 'YOUR_NGROK_URL_HERE' }}/analyze \
            -H "Content-Type: application/json" \
            -d '{
              "pipeline_id": "${{ github.run_id }}",
              "status": "success",
              "duration_seconds": 30,
              "logs": "Test run",
              "vulnerabilities": [],
              "branch": "${{ github.ref_name }}",
              "commit_sha": "${{ github.sha }}",
              "test_coverage_percent": 85.0,
              "is_direct_push": ${{ github.event_name == '\''push'\'' }},
              "pr_approved": false,
              "pr_reviewers_count": 0
            }'
```

### 4. Push and Watch

```bash
git add .github/workflows/guardian-test.yml
git commit -m "Add Guardian Agent"
git push
```

Check:
- GitHub Actions tab (see the workflow run)
- Your terminal with the agent (see incoming request)
- http://localhost:8000/metrics (see the analysis)

---

## Test Different Scenarios

### Test 1: Direct Push to Main (Should Trigger Warning)

```bash
git checkout main
echo "test" >> test.txt
git commit -am "Test direct push"
git push origin main
```

**Watch for:**
- 🚨 Branch protection violation
- Agent logs show critical alert

### Test 2: Pull Request (Cleaner)

```bash
git checkout -b feature/test
echo "feature" >> feature.txt
git commit -am "Add feature"
git push origin feature/test

# Create PR on GitHub
```

**Watch for:**
- ✅ No branch violation
- Analysis completes successfully

### Test 3: Low Coverage Simulation

Modify the workflow to set coverage to 60%:

```yaml
"test_coverage_percent": 60.0,
```

Push and watch:
- 🚨 Coverage violation detected

---

## View Results

**In GitHub Actions:**
- Go to Actions tab
- Click on your workflow run
- See Guardian Agent analysis

**In Your Terminal:**
- Watch real-time logs
- See anomaly detection

**Via API:**
```bash
curl http://localhost:8000/metrics
```

---

## Production Testing (After Render Deployment)

Replace ngrok URL with your Render URL:

```bash
# In GitHub repository settings
Settings → Secrets → Actions → New secret
Name: GUARDIAN_AGENT_URL
Value: https://cicd-guardian-agent.onrender.com
```

Then use in workflow:

```yaml
${{ secrets.GUARDIAN_AGENT_URL }}/analyze
```

---

That's it! You're now testing with a real repository! 🎉

See [REAL_REPO_TESTING.md](REAL_REPO_TESTING.md) for detailed scenarios.

