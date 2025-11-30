# 🛡️ CI/CD Guardian Agent

**Intelligent CI/CD Pipeline Monitoring & Policy Enforcement**

A modular, production-ready automation tool that safeguards CI/CD pipelines using Supervisor-Worker architecture. Built for the "Fundamentals of Software Project Management" course.

---

## 📋 Overview

The CI/CD Guardian Agent is an intelligent worker agent that:

- ✅ **Enforces branch protection** (no direct push to main/master/develop)
- ✅ **Validates pull requests** (minimum approvals required)
- ✅ **Monitors test coverage** (≥80% threshold)
- ✅ **Detects security vulnerabilities** (CVE scanning)
- ✅ **Tracks build health** (failures, duration, anomalies)
- ✅ **Sends real-time notifications** (Slack/Email)
- ✅ **Provides metrics & logs** for Supervisor escalation
- ✅ **Auto-recovers from corruption** (STM + LTM memory system)

---

## 🏗️ Architecture

**Pattern:** Supervisor-Worker  
**Role:** Worker Agent  
**Integration:** GitHub Actions / Jenkins  
**Configuration:** YAML-based  
**Memory:** Short-term (JSON) + Long-term (SQLite)

### Project Structure

```
cicd-guardian-agent/
├── src/
│   ├── agent.py              # Main FastAPI application
│   ├── policy_enforcer.py    # Branch protection + test coverage
│   ├── notifier.py           # Slack + Email notifications
│   ├── memory_manager.py     # STM/LTM with corruption handling
│   ├── models.py             # Pydantic request/response models
│   ├── memory.json           # Short-term memory
│   └── memory.db             # Long-term memory (auto-created)
├── config/
│   └── rules.yaml            # Fully configurable policies
├── logs/
│   └── agent.log             # Structured logs
├── .github/workflows/
│   └── guardian-demo.yml     # Live demo workflow
├── requirements.txt          # Python dependencies
├── render.yaml               # Render.com deployment config
├── register_with_supervisor.py  # Registration script
└── README.md                 # This file
```

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone repository
cd cicd-guardian-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Edit `config/rules.yaml` to customize policies:

```yaml
branch_protection:
  protected_branches: [main, master, develop]
  require_pull_request: true
  min_approvals: 1

test_coverage:
  minimum_percentage: 80

notifications:
  slack_webhook: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
  alert_on: [critical, high]
```

### 3. Run Locally

```bash
# Start the agent
uvicorn src.agent:app --reload --port 8000
```

Agent will be available at: `http://localhost:8000`

### 4. Test the Agent

```bash
# Health check
curl http://localhost:8000/health

# Register with Supervisor
python register_with_supervisor.py

# Analyze a pipeline
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

---

## 🌐 Deployment

### Option 1: Render.com (Recommended - Free & Permanent)

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/cicd-guardian-agent.git
   git push -u origin main
   ```

2. **Deploy on Render:**
   - Go to [render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Render will auto-detect `render.yaml`
   - Click "Create Web Service"

3. **Get your permanent URL:**
   ```
   https://cicd-guardian-agent.onrender.com
   ```

4. **Configure GitHub Actions:**
   - Go to your repository settings → Secrets
   - Add secret: `GUARDIAN_AGENT_URL` = your Render URL

### Option 2: ngrok (Temporary URL for Testing)

```bash
# In terminal 1 - Run agent
uvicorn src.agent:app --port 8000

# In terminal 2 - Expose with ngrok
ngrok http 8000
```

Copy the ngrok URL and use it in your GitHub Actions workflow.

---

## 🔌 API Endpoints

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/analyze` | POST | Analyze pipeline and detect anomalies |
| `/metrics` | GET | Get comprehensive metrics |
| `/health` | GET | Health check with memory status |
| `/register` | POST | Register with Supervisor |
| `/docs` | GET | Interactive API documentation |

### POST /analyze

**Request:**
```json
{
  "pipeline_id": "build-12345",
  "status": "failed|success|aborted",
  "duration_seconds": 450,
  "logs": "Build output...",
  "vulnerabilities": ["CVE-2023-12345"],
  "branch": "main",
  "commit_sha": "a1b2c3d4",
  "test_coverage_percent": 65.0,
  "is_direct_push": true,
  "pr_approved": false,
  "pr_reviewers_count": 0
}
```

**Response:**
```json
{
  "pipeline_id": "build-12345",
  "status": "failed",
  "anomalies": [
    {
      "type": "security_vulnerability",
      "description": "Security vulnerability detected: CVE-2023-12345",
      "severity": "critical"
    },
    {
      "type": "branch_protection_violation",
      "description": "Direct push to protected branch 'main' is not allowed",
      "severity": "critical"
    },
    {
      "type": "insufficient_test_coverage",
      "description": "Test coverage (65%) is below minimum (80%)",
      "severity": "critical"
    }
  ],
  "severity": "critical",
  "recommendation": "🚨 URGENT: Block merge until issues resolved.\n- Security vulnerability detected: CVE-2023-12345\n- Direct push to protected branch 'main' is not allowed\n- Test coverage (65%) is below minimum (80%)\n\nRecommended Actions:\n• Update dependencies to patch security vulnerabilities\n• Revert direct push and create a pull request instead\n• Add more unit tests to meet coverage requirements",
  "escalate_to_supervisor": true,
  "timestamp": "2025-11-29T10:30:00Z"
}
```

### GET /metrics

```json
{
  "total_pipelines_analyzed": 42,
  "critical_incidents": 8,
  "high_severity_incidents": 12,
  "medium_severity_incidents": 7,
  "low_severity_incidents": 3,
  "success_rate_percent": 28.57,
  "average_duration_seconds": 387.5,
  "last_analysis_timestamp": "2025-11-29T10:30:00Z",
  "top_anomalies": [
    {"type": "insufficient_test_coverage", "count": 15},
    {"type": "branch_protection_violation", "count": 8},
    {"type": "build_failure", "count": 6}
  ]
}
```

---

## 🔍 Anomaly Detection

The agent detects the following anomalies:

| Anomaly Type | Detection Criteria | Severity |
|--------------|-------------------|----------|
| **Security Vulnerability** | Any CVE detected | 🔴 Critical |
| **Branch Protection Violation** | Direct push to protected branch | 🔴 Critical |
| **Insufficient Test Coverage** | Coverage < 80% | 🔴 Critical |
| **PR Not Approved** | PR to protected branch not approved | 🔴 Critical |
| **Build Failure** | Pipeline status = failed | 🟠 High |
| **Build Aborted** | Pipeline status = aborted | 🟠 High |
| **Insufficient Reviewers** | PR reviewers < minimum required | 🟠 High |
| **Excessive Duration** | Duration > 600 seconds | 🟡 Medium |

### Severity Calculation

- **Critical:** Any CVE OR any critical anomaly OR 3+ anomalies
- **High:** Any high-severity anomaly
- **Medium:** Any medium-severity anomaly
- **Low:** Any low-severity anomaly
- **None:** No anomalies detected

---

## 🔔 Notifications

### Slack Integration

1. **Create Slack Webhook:**
   - Go to https://api.slack.com/messaging/webhooks
   - Create a new webhook for your workspace
   - Copy the webhook URL

2. **Configure in `config/rules.yaml`:**
   ```yaml
   notifications:
     slack_webhook: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
     alert_on: [critical, high]
   ```

3. **Notifications will include:**
   - Pipeline ID and severity
   - Branch and commit SHA
   - All detected anomalies
   - Actionable recommendations
   - Color-coded by severity

### Email Integration (Optional)

```yaml
notifications:
  email_smtp:
    server: "smtp.gmail.com"
    port: 587
    username: "your-email@gmail.com"
    password: "your-app-password"
    from_email: "cicd-guardian@example.com"
    to_emails:
      - "team@example.com"
```

---

## 🧪 GitHub Actions Integration

The `.github/workflows/guardian-demo.yml` provides a complete live demo:

1. **Simulates critical failure scenario:**
   - Build failure
   - Security vulnerabilities (CVE-2023-12345, CVE-2023-54321)
   - Direct push to main branch
   - Low test coverage (65%)
   - No PR approval

2. **Sends to Guardian Agent for analysis**

3. **Displays results with color-coded severity**

4. **Blocks merge if critical issues detected**

### Setup GitHub Actions

1. Add your agent URL as a secret:
   - Repository → Settings → Secrets → Actions
   - New secret: `GUARDIAN_AGENT_URL` = your agent URL

2. Push to trigger workflow:
   ```bash
   git push origin main
   ```

3. Watch the action run and see Guardian in action!

---

## 💾 Memory System

### Short-Term Memory (STM)

**File:** `src/memory.json`  
**Purpose:** Quick access to recent pipeline data

```json
{
  "last_pipeline": "build-12345",
  "alert_count": 3,
  "last_analyzed": "2025-11-29T10:30:00Z",
  "total_analyzed": 42,
  "agent_status": "active"
}
```

### Long-Term Memory (LTM)

**File:** `src/memory.db` (SQLite)  
**Purpose:** Full incident history and metrics

**Tables:**
- `incidents`: Complete pipeline analysis records
- `metrics`: Aggregated statistics

**Features:**
- Auto-created on first run
- Auto-recovery from corruption
- Indexed for fast queries
- Persistent across restarts

---

## 📊 Policies Enforced

The agent enforces the following policies (configurable via `rules.yaml`):

### 1. Branch Protection
- ❌ No direct push to `main`, `master`, or `develop`
- ✅ All changes must go through pull requests
- ✅ PRs must have minimum 1 approval

### 2. Test Coverage
- ✅ Minimum 80% code coverage required
- 🚨 Blocks merge if below threshold

### 3. Security
- ✅ Zero vulnerabilities (CVEs) allowed
- 🚨 Critical severity for any security issue

### 4. Build Health
- ✅ No failed or aborted builds
- ✅ Build duration < 600 seconds (10 minutes)

### 5. Code Review
- ✅ Minimum reviewers requirement enforced
- ✅ PR must be explicitly approved

---

## 🔧 Development

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-cov httpx

# Run tests (when test suite is added)
pytest tests/ -v --cov=src
```

### Code Quality

- ✅ 100% type hints (Python 3.11+)
- ✅ Comprehensive error handling
- ✅ Structured logging
- ✅ Modular architecture
- ✅ Clean, documented code

### Adding Custom Policies

1. Edit `src/policy_enforcer.py`
2. Add new check method
3. Add to `analyze_pipeline()` method
4. Update `config/rules.yaml` with new settings

---

## 🎯 Use Cases

### For Development Teams
- Enforce code quality standards
- Prevent accidental direct commits
- Ensure adequate test coverage
- Track build health trends

### For DevOps Teams
- Monitor CI/CD pipeline health
- Detect security vulnerabilities early
- Automate policy enforcement
- Reduce manual code review burden

### For Project Managers
- Get visibility into build quality
- Track team compliance metrics
- Identify process bottlenecks
- Make data-driven decisions

---

## 📈 Metrics Dashboard

Access comprehensive metrics via `/metrics`:

- **Total Pipelines Analyzed:** Overall activity
- **Incident Counts:** By severity level
- **Success Rate:** Percentage of passing pipelines
- **Average Duration:** Build performance
- **Top Anomalies:** Most common issues
- **Last Analysis:** Real-time status

---

## 🐛 Troubleshooting

### Agent won't start
```bash
# Check Python version (requires 3.11+)
python --version

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check logs
tail -f logs/agent.log
```

### Memory corruption
The agent auto-recovers! If you see corruption warnings:
- STM will be recreated with defaults
- LTM will be recreated with empty tables
- All data is logged before recovery

### Notifications not sending
1. Verify webhook URL in `config/rules.yaml`
2. Test webhook manually:
   ```bash
   curl -X POST YOUR_WEBHOOK_URL \
     -H "Content-Type: application/json" \
     -d '{"text": "Test message"}'
   ```
3. Check logs for error details

### GitHub Actions not triggering
1. Ensure `GUARDIAN_AGENT_URL` secret is set
2. Check agent is publicly accessible
3. Verify workflow syntax in `.github/workflows/guardian-demo.yml`

---

## 🏆 Features Checklist

✅ **Core Functionality**
- [x] Branch protection enforcement
- [x] Test coverage monitoring (≥80%)
- [x] Security vulnerability detection
- [x] Build health monitoring
- [x] PR validation (approvals, reviewers)

✅ **Notifications**
- [x] Slack integration
- [x] Email support
- [x] Configurable alert levels
- [x] Color-coded severity

✅ **Memory & Persistence**
- [x] Short-term memory (JSON)
- [x] Long-term memory (SQLite)
- [x] Corruption auto-recovery
- [x] Metrics aggregation

✅ **Integration**
- [x] GitHub Actions workflow
- [x] FastAPI REST API
- [x] Supervisor registration
- [x] Render.com deployment

✅ **Code Quality**
- [x] 100% type hints
- [x] Comprehensive error handling
- [x] Structured logging
- [x] Modular architecture
- [x] Full documentation

---

## 📚 API Documentation

Interactive API documentation available at:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## 🎓 Course Project Submission

This project fulfills the "Code & Working Prototype" deliverable for the Fundamentals of Software Project Management course.

**Key Requirements Met:**
- ✅ Supervisor-Worker architecture
- ✅ Modular, intelligent automation
- ✅ CI/CD pipeline integration
- ✅ Compliance enforcement
- ✅ Performance monitoring
- ✅ Configurable notifications
- ✅ Metrics for escalation
- ✅ Python + FastAPI implementation
- ✅ YAML configuration
- ✅ Lightweight & scalable
- ✅ Production-ready code

---

## 🤝 Contributing

This is a course project, but suggestions are welcome:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## 📄 License

This project is created for educational purposes as part of the "Fundamentals of Software Project Management" course.

---

## 📧 Support

For issues or questions:
- Check the troubleshooting section
- Review logs in `logs/agent.log`
- Test with `/health` endpoint
- Verify configuration in `config/rules.yaml`

---

## 🌟 Acknowledgments

Built with:
- **FastAPI** - Modern Python web framework
- **Pydantic** - Data validation
- **SQLite** - Lightweight database
- **YAML** - Configuration management
- **GitHub Actions** - CI/CD integration

---

**Made with 🛡️ for Software Project Management**  
**Deadline: Nov 30, 2025**  
**Status: ✅ Production Ready**

