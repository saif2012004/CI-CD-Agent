# 🛡️ CI/CD Guardian Agent

**Intelligent CI/CD Pipeline Monitoring & Policy Enforcement**

A modular, production-ready, **standalone** automation tool that safeguards CI/CD pipelines. It makes its own block/allow decision on every pipeline run — no external orchestrator required. Built for the "Fundamentals of Software Project Management" course.

**🌐 Live Deployment:** https://ci-cd-agent.onrender.com  
**📊 API Docs:** https://ci-cd-agent.onrender.com/docs  
**✅ Status:** Production Ready & Deployed

---

## 📋 Overview

The CI/CD Guardian Agent is an intelligent, standalone agent that:

- ✅ **Enforces branch protection** (no direct push to main/master/develop)
- ✅ **Validates pull requests** (minimum approvals required)
- ✅ **Monitors test coverage** (≥80% threshold)
- ✅ **Detects security vulnerabilities** (CVE scanning)
- ✅ **Tracks build health** (failures, duration, anomalies)
- ✅ **Sends real-time notifications** (Slack/Email)
- ✅ **Issues a block/allow verdict** on every run (`block_merge`) plus metrics & logs
- ✅ **Auto-recovers from corruption** (STM + LTM memory system)

---

## 🏗️ Architecture

**Pattern:** Standalone autonomous service  
**Role:** Self-contained policy decision engine  
**Integration:** GitHub Actions / Jenkins  
**Configuration:** YAML-based  
**Memory:** Short-term (JSON) + Long-term (SQLite)

### Project Structure

```
CI-CD-Agent/                       # Repository root
├── .github/workflows/
│   └── test-guardian.yml          # GitHub Actions workflow (runs the test suite)
└── cicd-guardian-agent/           # Application
    ├── src/
    │   ├── agent.py               # Main FastAPI application
    │   ├── policy_enforcer.py     # Branch protection + test coverage
    │   ├── notifier.py            # Slack + Email notifications
    │   ├── github_client.py       # Reads PR state, posts Check Runs & PR comments
    │   ├── memory_manager.py      # STM/LTM with corruption handling
    │   ├── models.py              # Pydantic request/response models
    │   ├── memory.json            # Short-term memory (auto-created, gitignored)
    │   └── memory.db              # Long-term memory (auto-created, gitignored)
    ├── tests/                     # Pytest suite (policy, auth, github, /analyze)
    ├── conftest.py                # Test path setup
    ├── config/
    │   └── rules.yaml             # Fully configurable policies
    ├── logs/
    │   └── agent.log              # Structured logs
    ├── requirements.txt           # Python dependencies
    ├── render.yaml                # Render.com deployment config
    ├── README.md                  # This file
    └── DEPLOYMENT.md              # Deployment guide
```

> **Note:** The GitHub Actions workflow lives at the **repository root**
> (`.github/workflows/`) so GitHub picks it up; its `run` steps execute inside
> `cicd-guardian-agent/`.

---

## 🚀 Quick Start

### Use the Live Deployment (Recommended)

The agent is **already deployed and running** at:
- **Base URL:** https://ci-cd-agent.onrender.com
- **Interactive Docs:** https://ci-cd-agent.onrender.com/docs
- **Health Check:** https://ci-cd-agent.onrender.com/health

### Test the Live Agent

```bash
# Health check
curl https://ci-cd-agent.onrender.com/health

# Get metrics
curl https://ci-cd-agent.onrender.com/metrics

# Analyze a pipeline
curl -X POST https://ci-cd-agent.onrender.com/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_id": "test-123",
    "status": "success",
    "duration_seconds": 120,
    "logs": "Build completed",
    "vulnerabilities": [],
    "branch": "main",
    "commit_sha": "abc123",
    "test_coverage_percent": 75.0,
    "is_direct_push": true,
    "pr_approved": false,
    "pr_reviewers_count": 0
  }'
```

### Run Locally (Optional)

If you want to run the agent on your local machine:

1. **Clone & Install:**
```bash
git clone https://github.com/saif2012004/CI-CD-Agent.git
cd CI-CD-Agent/cicd-guardian-agent
pip install -r requirements.txt
```

2. **Configure** (optional):
Edit `config/rules.yaml` to customize policies.

3. **Run:**
```bash
uvicorn src.agent:app --reload --port 8000
```

Agent will be available at: `http://localhost:8000`

### Environment Variables

All are optional:

| Variable | Purpose |
|----------|---------|
| `PORT` | Port to bind (default `8000`). |
| `SLACK_WEBHOOK_URL` | Slack webhook for notifications; overrides `config/rules.yaml`. |
| `GUARDIAN_API_KEY` | If set, requires an `X-API-Key` header on `/analyze` and `/metrics`. Unset = auth disabled. |
| `GUARDIAN_AGENT_URL` | *(CI secret)* URL the GitHub Actions workflow posts results to. |

---

## 🌐 Deployment

### ✅ Already Deployed on Render!

The agent is **live and running** at:
- **Production URL:** https://ci-cd-agent.onrender.com
- **Status:** Active 24/7
- **Deployment:** Automated via GitHub push
- **Platform:** Render.com (Free Tier)

**Repository:** https://github.com/saif2012004/CI-CD-Agent

### Integrate with Your Repository

To use this agent in your projects:

1. **Add the secret to your repository:**
   - Go to: Your Repo → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `GUARDIAN_AGENT_URL`
   - Value: `https://ci-cd-agent.onrender.com`

2. **Add the workflow file:**
   Copy `.github/workflows/test-guardian.yml` to your repository

3. **Push code and watch the magic!** 🎉

**Detailed deployment guide:** See [DEPLOYMENT.md](DEPLOYMENT.md)

---

## 🔌 API Endpoints

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/analyze` | POST | Analyze pipeline and detect anomalies |
| `/metrics` | GET | Get comprehensive metrics |
| `/health` | GET | Health check with memory status |
| `/docs` | GET | Interactive API documentation |

### 🔐 Authentication

`/analyze` and `/metrics` support **optional** API-key authentication:

- If the `GUARDIAN_API_KEY` environment variable is set on the agent, requests
  to those two endpoints must include a matching `X-API-Key` header (otherwise
  they return `401 Unauthorized`).
- If `GUARDIAN_API_KEY` is **not** set, authentication is disabled — convenient
  for local/demo use.
- `/health` and `/` are always open.

```bash
curl -X POST https://ci-cd-agent.onrender.com/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $GUARDIAN_API_KEY" \
  -d '{ ... }'
```

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
  "block_merge": true,
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
| **Excessive Duration** | Duration > threshold (default 600s, configurable) | 🟡 Medium |

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

2. **Configure via environment variable (recommended):**
   Set `SLACK_WEBHOOK_URL` in your environment (e.g. Render → Environment tab).
   This takes precedence over `config/rules.yaml`, keeping the secret out of
   source control:
   ```bash
   export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
   ```
   Alternatively (not recommended for secrets), set it in `config/rules.yaml`:
   ```yaml
   notifications:
     slack_webhook: null   # leave null and use SLACK_WEBHOOK_URL instead
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

The workflow at `.github/workflows/test-guardian.yml` (repository root) runs on
every push/PR and:

1. **Runs the test suite with coverage** — a test failure **fails the build**
   (the step no longer uses `continue-on-error`, and there is no dummy-coverage
   fallback).

2. **Runs a security scan** (`pip-audit`) to surface CVEs.

3. **Sends the pipeline result to the Guardian Agent**, passing the repo, PR
   number, and a short-lived `github.token`.

4. **The agent acts on GitHub autonomously** (see below).

### 🤖 The agent acts on GitHub (autonomous mode)

When `/analyze` receives GitHub context (`github_repo`, `github_pr_number`,
`github_token`), the agent does the work itself instead of just returning a flag:

- **Reads the *real* PR review state** from GitHub (approvals, reviewers,
  changes-requested) and uses it for policy checks — no more stubbed PR data, so
  a properly approved PR is no longer falsely flagged.
- **Posts a Check Run** named *"CI/CD Guardian"* on the commit: `failure` when
  `block_merge` is true, `neutral` for non-blocking issues, `success` when clean.
  Add this check to your branch-protection rules to **actually gate merges**.
- **Comments its findings** on the pull request (severity table + recommendation).

All GitHub calls are best-effort: if the token is missing or a call fails, the
analysis still completes normally.

### Setup GitHub Actions

1. Add your agent URL as a secret:
   - Repository → Settings → Secrets and variables → Actions
   - New secret: `GUARDIAN_AGENT_URL` = your agent URL

2. The workflow grants `checks: write` + `pull-requests: write` and passes the
   built-in `github.token` to the agent — no PAT required for same-repo runs.

3. *(Optional)* If your agent enforces auth, add a `GUARDIAN_API_KEY` secret
   matching the agent's `GUARDIAN_API_KEY` env var (sent as `X-API-Key`).

4. *(Recommended)* In branch protection, require the **"CI/CD Guardian"** status
   check so blocked merges are actually prevented.

5. Push to trigger the workflow and watch Guardian act on your PR!

> **Security note:** the `github.token` passed to the agent is ephemeral
> (expires when the job ends) and repo-scoped. The workflow never echoes it.

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
- ✅ Build duration under threshold (default 600s, set via
  `build_monitoring.max_duration_seconds` in `rules.yaml`)

### 5. Code Review
- ✅ Minimum reviewers requirement enforced
- ✅ PR must be explicitly approved

---

## 🔧 Development

### Running Tests

The repo ships with a pytest suite (policy enforcement + auth). Run it from the
`cicd-guardian-agent/` directory:

```bash
# Install dev dependencies
pip install -r requirements.txt pytest pytest-cov

# Run the test suite with coverage
pytest --cov=src --cov-report=term
```

These same tests run in CI on every push/PR and fail the build on any failure.

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
3. Verify workflow syntax in `.github/workflows/test-guardian.yml` (note: it
   must live at the **repository root**, not inside `cicd-guardian-agent/`)

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
- [x] Self-contained block/allow verdict
- [x] Render.com deployment

✅ **Code Quality**
- [x] 100% type hints
- [x] Comprehensive error handling
- [x] Structured logging
- [x] Modular architecture
- [x] Full documentation
- [x] Automated pytest suite, enforced in CI
- [x] Optional API-key authentication

---

## 📚 API Documentation

Interactive API documentation available at:
- **Swagger UI:** https://ci-cd-agent.onrender.com/docs
- **ReDoc:** https://ci-cd-agent.onrender.com/redoc

For local development:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## 🔗 Standalone Operation

This agent runs **independently** — it makes its own decision on every pipeline
run and does not require any external orchestrator.

- **Analyze a pipeline:** `POST https://ci-cd-agent.onrender.com/analyze`
- **Health monitoring:** `GET https://ci-cd-agent.onrender.com/health`
- **Metrics collection:** `GET https://ci-cd-agent.onrender.com/metrics`

Each `/analyze` response includes a **`block_merge`** flag — the agent's own
verdict on whether the change should be blocked (set for `critical`/`high`
severity). The GitHub Actions workflow reads this flag and fails the build
accordingly.

---

## 🎓 Course Project Submission

This project fulfills the "Code & Working Prototype" deliverable for the Fundamentals of Software Project Management course.

**Key Requirements Met:**
- ✅ Standalone autonomous agent
- ✅ Modular, intelligent automation
- ✅ CI/CD pipeline integration
- ✅ Compliance enforcement
- ✅ Performance monitoring
- ✅ Configurable notifications
- ✅ Metrics & block/allow verdict
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
**Deployed:** November 30, 2025  
**Status:** ✅ Live & Production Ready  
**Live URL:** https://ci-cd-agent.onrender.com

