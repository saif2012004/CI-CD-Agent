# 🚀 QUICK START GUIDE

## Prerequisites
- Python 3.11+ installed
- Internet connection for installing packages

---

## ⚡ Fast Start (3 Steps)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Start Server
```bash
python -m uvicorn src.agent:app --reload --port 8000
```

### Step 3: Test It
Open http://localhost:8000/docs in your browser! 🎉

---

## 🖥️ Platform-Specific Instructions

### Windows

**Option 1: Double-click batch files**
1. Double-click `run_server.bat` to start server
2. Open new terminal and double-click `run_tests.bat` to run tests

**Option 2: Command line**
```cmd
# Install
pip install -r requirements.txt

# Run server
python -m uvicorn src.agent:app --reload --port 8000

# Test (in new terminal)
pip install requests
python test_agent.py
```

### Linux / Mac

**Make scripts executable:**
```bash
chmod +x setup.sh run_server.sh run_tests.sh
```

**Run:**
```bash
# Setup
./setup.sh

# Start server
./run_server.sh

# Test (in new terminal)
./run_tests.sh
```

---

## 🧪 Verify Installation

Once the server is running, visit these URLs:

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics

---

## 🎯 Quick Test

Run this command in another terminal:

```bash
curl http://localhost:8000/health
```

You should see:
```json
{
  "status": "healthy",
  "agent_name": "CI/CD Guardian Agent",
  "version": "1.0.0",
  ...
}
```

---

## 🔥 Test with Sample Pipeline

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

Expected: Response with detected anomalies and critical severity!

---

## 🚀 Deploy to Render (Free Hosting)

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin YOUR_GITHUB_URL
git push -u origin main
```

### 2. Deploy on Render
1. Go to https://render.com
2. Click "New" → "Web Service"
3. Connect your GitHub repo
4. Render auto-detects settings from `render.yaml`
5. Click "Create Web Service"
6. Wait 2-3 minutes for deployment

### 3. Your Agent is Live! 🎉
```
https://cicd-guardian-agent.onrender.com
```

---

## 📁 Project Structure

```
cicd-guardian-agent/
├── src/
│   ├── agent.py              # Main FastAPI app
│   ├── policy_enforcer.py    # Policy rules
│   ├── notifier.py           # Notifications
│   ├── memory_manager.py     # Memory system
│   └── models.py             # Data models
├── config/
│   └── rules.yaml            # Configuration
├── test_agent.py             # Test suite
├── run_server.bat            # Windows start script
├── run_tests.bat             # Windows test script
├── run_server.sh             # Linux/Mac start script
├── run_tests.sh              # Linux/Mac test script
├── requirements.txt          # Dependencies
├── render.yaml               # Render deployment config
├── DEPLOYMENT.md             # Deployment guide
├── TESTING.md                # Testing guide
└── README.md                 # Full documentation
```

---

## 🛠️ Troubleshooting

### "Module not found" error
```bash
pip install -r requirements.txt
```

### Port already in use
```bash
# Use a different port
python -m uvicorn src.agent:app --port 8001
```

### Can't access from browser
- Check if server is running (look for "Uvicorn running on...")
- Try http://127.0.0.1:8000/docs instead
- Ensure no firewall is blocking the port

---

## 📚 Documentation

- **Full README**: [README.md](README.md)
- **Deployment Guide**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Testing Guide**: [TESTING.md](TESTING.md)

---

## ✅ Checklist

Before deploying to Render:

- [ ] Server runs locally without errors
- [ ] Can access http://localhost:8000/docs
- [ ] Health check returns 200 OK
- [ ] Test suite passes (all 5 tests)
- [ ] Code committed to Git
- [ ] Pushed to GitHub

---

## 🎓 What This Agent Does

- ✅ Monitors CI/CD pipelines
- ✅ Detects security vulnerabilities
- ✅ Enforces branch protection
- ✅ Validates test coverage (≥80%)
- ✅ Checks PR approvals
- ✅ Sends notifications
- ✅ Tracks metrics
- ✅ Auto-escalates critical issues

---

## 🤝 Need Help?

1. Check [TESTING.md](TESTING.md) for detailed testing instructions
2. Check [DEPLOYMENT.md](DEPLOYMENT.md) for deployment help
3. Review logs in `logs/agent.log`
4. Check terminal output for errors

---

## 🎯 Next Steps

1. ✅ Run server locally → `python -m uvicorn src.agent:app --reload --port 8000`
2. ✅ Test with browser → http://localhost:8000/docs
3. ✅ Run test suite → `python test_agent.py`
4. ✅ Deploy to Render → Follow [DEPLOYMENT.md](DEPLOYMENT.md)
5. ✅ Configure notifications → Edit `config/rules.yaml`
6. ✅ Integrate with GitHub Actions → Add agent URL to secrets

---

**Made with 🛡️ for Software Project Management**

**Ready to deploy!** 🚀

