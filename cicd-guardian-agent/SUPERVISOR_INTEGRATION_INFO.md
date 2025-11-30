# CI/CD Guardian Agent - Supervisor Integration Guide

## Agent Information

**Agent Name:** CI/CD Guardian Agent  
**Agent ID:** cicd-guardian-001  
**Agent Type:** CI/CD Monitoring & Policy Enforcement  
**Deployed URL:** https://ci-cd-agent.onrender.com  
**Status:** ✅ Active and Running

---

## Endpoints for Supervisor Integration

### 1. Registration Endpoint
**URL:** `POST https://ci-cd-agent.onrender.com/register`  
**Purpose:** Get agent capabilities, endpoints, and metadata  
**Authentication:** None required  
**Response:** JSON with agent details, capabilities, and available endpoints

**Example:**
```bash
curl -X POST https://ci-cd-agent.onrender.com/register
```

**Response:**
```json
{
  "agent_id": "cicd-guardian-001",
  "agent_type": "CI/CD Monitoring & Policy Enforcement",
  "capabilities": [
    "Branch protection enforcement",
    "Pull request validation",
    "Test coverage monitoring (≥80%)",
    "Security vulnerability detection",
    "Build health monitoring",
    "Real-time anomaly detection",
    "Metrics and reporting"
  ],
  "endpoints": {
    "analyze": "https://ci-cd-agent.onrender.com/analyze",
    "metrics": "https://ci-cd-agent.onrender.com/metrics",
    "health": "https://ci-cd-agent.onrender.com/health",
    "docs": "https://ci-cd-agent.onrender.com/docs"
  },
  "status": "active",
  "metadata": {
    "version": "1.0.0",
    "architecture": "Supervisor-Worker",
    "escalation_severity": ["critical", "high"]
  }
}
```

---

### 2. Health Check Endpoint
**URL:** `GET https://ci-cd-agent.onrender.com/health`  
**Purpose:** Monitor agent health and availability  
**Frequency:** Can be called every 30-60 seconds  

**Example:**
```bash
curl https://ci-cd-agent.onrender.com/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-30T07:30:00Z",
  "memory_status": {
    "stm": "ok",
    "ltm": "ok"
  },
  "config_loaded": true,
  "uptime_seconds": 3600.5
}
```

---

### 3. Metrics Endpoint
**URL:** `GET https://ci-cd-agent.onrender.com/metrics`  
**Purpose:** Retrieve agent performance and analysis metrics  
**Frequency:** Can be called every 5-10 minutes  

**Example:**
```bash
curl https://ci-cd-agent.onrender.com/metrics
```

**Response:**
```json
{
  "total_pipelines_analyzed": 15,
  "critical_incidents": 3,
  "high_severity_incidents": 5,
  "medium_severity_incidents": 4,
  "low_severity_incidents": 3,
  "success_rate_percent": 85.5,
  "average_duration_seconds": 120.3,
  "last_analysis_timestamp": "2025-11-30T07:25:00Z",
  "top_anomalies": [
    {"type": "branch_protection_violation", "count": 5},
    {"type": "insufficient_test_coverage", "count": 4},
    {"type": "pr_not_approved", "count": 3}
  ]
}
```

---

### 4. Analysis Endpoint (Core Functionality)
**URL:** `POST https://ci-cd-agent.onrender.com/analyze`  
**Purpose:** Analyze CI/CD pipeline and detect policy violations  
**Content-Type:** `application/json`

**Request Payload:**
```json
{
  "pipeline_id": "unique-pipeline-id",
  "status": "success|failed|aborted",
  "duration_seconds": 120,
  "logs": "Pipeline execution logs",
  "vulnerabilities": ["CVE-2023-1234", "CVE-2023-5678"],
  "branch": "main",
  "commit_sha": "abc123def456",
  "test_coverage_percent": 75.0,
  "is_direct_push": true,
  "pr_approved": false,
  "pr_reviewers_count": 0
}
```

**Example:**
```bash
curl -X POST https://ci-cd-agent.onrender.com/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_id": "test-123",
    "status": "success",
    "duration_seconds": 120,
    "logs": "Test pipeline",
    "vulnerabilities": [],
    "branch": "main",
    "commit_sha": "abc123",
    "test_coverage_percent": 75.0,
    "is_direct_push": true,
    "pr_approved": false,
    "pr_reviewers_count": 0
  }'
```

**Response:**
```json
{
  "pipeline_id": "test-123",
  "status": "success",
  "anomalies": [
    {
      "type": "branch_protection_violation",
      "description": "Direct push to protected branch 'main' is not allowed",
      "severity": "critical"
    },
    {
      "type": "insufficient_test_coverage",
      "description": "Test coverage (75.0%) is below minimum (80%)",
      "severity": "critical"
    }
  ],
  "severity": "critical",
  "recommendation": "Block merge until issues resolved...",
  "timestamp": "2025-11-30T07:30:00Z",
  "escalate_to_supervisor": true
}
```

---

## Escalation Logic

The agent will set `"escalate_to_supervisor": true` when:
- **Severity is "critical"** - Requires immediate attention
- **Severity is "high"** - Requires attention soon

The supervisor should monitor these escalations and take appropriate action.

---

## Policies Enforced by This Agent

1. **Branch Protection:** No direct pushes to main/master/develop branches
2. **PR Approval:** Pull requests require minimum 1 approval
3. **Test Coverage:** Minimum 80% code coverage required
4. **Build Duration:** Alerts if build exceeds 600 seconds
5. **Security:** Zero tolerance for known CVE vulnerabilities

---

## API Documentation

**Interactive Docs:** https://ci-cd-agent.onrender.com/docs  
**Root Endpoint:** https://ci-cd-agent.onrender.com/

---

## Technical Details

- **Framework:** FastAPI (Python)
- **Deployment:** Render.com (Free tier)
- **Uptime:** May sleep after 15 min inactivity (first request wakes it ~30s)
- **Response Time:** < 1 second (when awake)
- **Rate Limiting:** None currently

---

## Support & Contact

**Repository:** https://github.com/saif2012004/CI-CD-Agent  
**Test Repository:** https://github.com/saif2012004/test-cicd-guardian  
**Group:** [Your Group Name/Number]  
**Contact:** [Your Email/Contact Info]

---

## Integration Checklist for Supervisor Team

- [ ] Call `/register` endpoint to discover agent
- [ ] Store agent metadata and endpoints
- [ ] Set up periodic health checks (`/health`)
- [ ] Set up periodic metrics collection (`/metrics`)
- [ ] Configure task delegation to `/analyze` endpoint
- [ ] Monitor `escalate_to_supervisor` flag in responses
- [ ] Handle escalations for critical/high severity issues

---

## Test the Integration

You can test our agent anytime with:

```bash
# Health check
curl https://ci-cd-agent.onrender.com/health

# Get metrics
curl https://ci-cd-agent.onrender.com/metrics

# Test analysis (will detect 4 policy violations)
curl -X POST https://ci-cd-agent.onrender.com/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_id": "supervisor-test-001",
    "status": "success",
    "duration_seconds": 100,
    "logs": "Test from supervisor",
    "vulnerabilities": [],
    "branch": "main",
    "commit_sha": "test123",
    "test_coverage_percent": 70.0,
    "is_direct_push": true,
    "pr_approved": false,
    "pr_reviewers_count": 0
  }'
```

---

## Notes

- Our agent is deployed on Render's free tier, so it may take ~30 seconds to wake up if it's been idle
- The agent is fully functional and ready for integration
- All endpoints return JSON responses
- No authentication required for testing/demo purposes

**The agent is live and ready for your supervisor to integrate!** 🚀

