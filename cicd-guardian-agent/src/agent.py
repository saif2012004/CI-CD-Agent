"""
CI/CD Guardian Agent - Main FastAPI Application
Standalone autonomous agent for CI/CD pipeline monitoring and policy enforcement
"""
from fastapi import FastAPI, HTTPException, Request, Depends, Header, status
from fastapi.responses import JSONResponse, HTMLResponse
from contextlib import asynccontextmanager
import logging
import yaml
import time
from pathlib import Path
from typing import Dict, Any, Optional
import os

from src.models import (
    PipelineAnalysisRequest,
    PipelineAnalysisResponse,
    MetricsResponse,
    HealthResponse
)
from src.policy_enforcer import PolicyEnforcer
from src.notifier import Notifier
from src.memory_manager import MemoryManager
from src.github_client import GitHubClient
from src.dashboard import DASHBOARD_HTML

# Configure logging
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "agent.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Global state
START_TIME = time.time()
CONFIG: Dict[str, Any] = {}
POLICY_ENFORCER: PolicyEnforcer = None
NOTIFIER: Notifier = None
MEMORY: MemoryManager = None


async def verify_api_key(x_api_key: Optional[str] = Header(default=None)) -> None:
    """
    Optional API-key authentication.

    If the GUARDIAN_API_KEY environment variable is set, requests to
    protected endpoints must send a matching X-API-Key header. If it is
    not set, authentication is disabled (convenient for local/demo use).
    """
    expected = os.getenv("GUARDIAN_API_KEY")
    if not expected:
        return  # Auth disabled
    if x_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "API-Key"},
        )


def load_config() -> Dict[str, Any]:
    """Load configuration from rules.yaml"""
    try:
        config_path = Path("config/rules.yaml")
        if not config_path.exists():
            logger.error("Configuration file not found")
            return get_default_config()
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        logger.info("Configuration loaded successfully")
        return config
    
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return get_default_config()


def get_default_config() -> Dict[str, Any]:
    """Return default configuration"""
    return {
        "branch_protection": {
            "protected_branches": ["main", "master", "develop"],
            "require_pull_request": True,
            "min_approvals": 1
        },
        "test_coverage": {
            "minimum_percentage": 80
        },
        "notifications": {
            "slack_webhook": None,
            "email_smtp": None,
            "alert_on": ["critical", "high"]
        }
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize agent components on startup."""
    global CONFIG, POLICY_ENFORCER, NOTIFIER, MEMORY

    logger.info("🛡️  CI/CD Guardian Agent starting up...")

    # Load configuration
    CONFIG = load_config()

    # Initialize components
    POLICY_ENFORCER = PolicyEnforcer(CONFIG)
    NOTIFIER = Notifier(CONFIG.get("notifications", {}))
    MEMORY = MemoryManager()

    logger.info("✅ CI/CD Guardian Agent ready")
    yield


# Initialize FastAPI app
app = FastAPI(
    title="CI/CD Guardian Agent",
    description="Intelligent CI/CD pipeline monitoring and policy enforcement agent",
    version="1.0.0",
    lifespan=lifespan
)


def _build_pr_comment(severity, anomalies, recommendation, block_merge) -> str:
    """Format the agent's findings as a Markdown PR comment."""
    verdict = "🚫 **Merge blocked**" if block_merge else "⚠️ **Issues found (non-blocking)**"
    lines = [
        "## 🛡️ CI/CD Guardian",
        "",
        f"{verdict} — overall severity: **{severity.upper()}**",
        "",
        "| Severity | Issue |",
        "|----------|-------|",
    ]
    for a in anomalies:
        lines.append(f"| {a.severity} | {a.description} |")
    lines += ["", "### Recommendation", "", recommendation]
    return "\n".join(lines)


@app.post("/analyze", response_model=PipelineAnalysisResponse, dependencies=[Depends(verify_api_key)])
async def analyze_pipeline(request: PipelineAnalysisRequest):
    """
    Core endpoint: Analyze pipeline and detect anomalies
    
    Detects:
    - Build failures/aborts
    - Excessive duration
    - Security vulnerabilities
    - Branch protection violations
    - PR approval issues
    - Insufficient test coverage
    
    Returns comprehensive analysis with severity and recommendations
    """
    try:
        logger.info(f"Analyzing pipeline: {request.pipeline_id}")

        # Resolve optional GitHub integration so the agent can act on its own.
        gh_client = None
        token = request.github_token or os.getenv("GITHUB_TOKEN")
        if token and request.github_repo:
            gh_client = GitHubClient(token, request.github_repo)

        # Prefer real PR review data from GitHub over caller-supplied values.
        pr_approved = request.pr_approved
        pr_reviewers_count = request.pr_reviewers_count
        if gh_client and request.github_pr_number:
            review_status = gh_client.get_pr_review_status(request.github_pr_number)
            if review_status:
                if pr_approved is None:
                    pr_approved = review_status["approved"]
                if pr_reviewers_count is None:
                    pr_reviewers_count = review_status["reviewers_count"]
                logger.info(f"Resolved real PR review status: {review_status}")

        # Perform policy analysis
        anomalies = POLICY_ENFORCER.analyze_pipeline(
            status=request.status,
            duration_seconds=request.duration_seconds,
            vulnerabilities=request.vulnerabilities,
            branch=request.branch,
            commit_sha=request.commit_sha,
            logs=request.logs,
            test_coverage_percent=request.test_coverage_percent,
            is_direct_push=request.is_direct_push,
            pr_approved=pr_approved,
            pr_reviewers_count=pr_reviewers_count
        )
        
        # Calculate overall severity
        severity = POLICY_ENFORCER.calculate_severity(anomalies)
        
        # Generate recommendation
        recommendation = POLICY_ENFORCER.generate_recommendation(anomalies, severity)
        
        # Determine the agent's own verdict: should this change be blocked?
        block_merge = severity in ["critical", "high"]
        
        # Update memory
        MEMORY.update_stm(request.pipeline_id, severity)
        MEMORY.save_incident(
            pipeline_id=request.pipeline_id,
            status=request.status,
            severity=severity,
            duration_seconds=request.duration_seconds,
            branch=request.branch,
            commit_sha=request.commit_sha,
            anomalies=anomalies,
            recommendation=recommendation,
            blocked=block_merge
        )
        
        # Send notifications if needed
        if anomalies:
            notification_result = NOTIFIER.send_notifications(
                pipeline_id=request.pipeline_id,
                severity=severity,
                anomalies=anomalies,
                recommendation=recommendation,
                branch=request.branch,
                commit_sha=request.commit_sha
            )
            logger.info(f"Notification sent: {notification_result}")
        
        # Build response
        response = PipelineAnalysisResponse(
            pipeline_id=request.pipeline_id,
            status=request.status,
            anomalies=anomalies,
            severity=severity,
            recommendation=recommendation,
            block_merge=block_merge
        )

        # Act on GitHub: post a Check Run (gates merges) and comment findings.
        if gh_client:
            if not anomalies:
                conclusion = "success"
                title = "All policy checks passed"
            elif block_merge:
                conclusion = "failure"
                title = f"{severity.upper()} - {len(anomalies)} issue(s) found"
            else:
                conclusion = "neutral"
                title = f"{severity.upper()} - {len(anomalies)} issue(s) found"
            gh_client.post_check_run(request.commit_sha, conclusion, title, recommendation)
            if request.github_pr_number and anomalies:
                gh_client.post_pr_comment(
                    request.github_pr_number,
                    _build_pr_comment(severity, anomalies, recommendation, block_merge),
                )

        logger.info(f"Analysis complete: {severity} severity, {len(anomalies)} anomalies")
        return response
    
    except Exception as e:
        logger.error(f"Error analyzing pipeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/metrics", response_model=MetricsResponse, dependencies=[Depends(verify_api_key)])
async def get_metrics():
    """
    Get comprehensive metrics

    Returns:
    - Total pipelines analyzed
    - Incident counts by severity
    - Success rate
    - Average duration
    - Top anomalies
    """
    try:
        metrics = MEMORY.get_metrics()
        return MetricsResponse(**metrics)
    
    except Exception as e:
        logger.error(f"Error retrieving metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {str(e)}")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    
    Returns:
    - Service status
    - Memory status
    - Configuration status
    - Uptime
    """
    try:
        uptime = time.time() - START_TIME
        memory_status = MEMORY.get_memory_status()
        
        return HealthResponse(
            status="healthy",
            memory_status=memory_status,
            config_loaded=bool(CONFIG),
            uptime_seconds=round(uptime, 2)
        )
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            memory_status={"stm": "error", "ltm": "error"},
            config_loaded=False,
            uptime_seconds=0.0
        )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Serve the human-facing metrics dashboard (HTML)."""
    return HTMLResponse(content=DASHBOARD_HTML)


@app.get("/dashboard/data", dependencies=[Depends(verify_api_key)])
async def dashboard_data():
    """JSON feed for the dashboard: aggregate metrics + recent incidents."""
    try:
        metrics = MEMORY.get_metrics()
        metrics["ltm_backend"] = MEMORY.get_memory_status().get("ltm_backend")
        return {
            "metrics": metrics,
            "recent": MEMORY.get_recent_incidents(limit=20),
        }
    except Exception as e:
        logger.error(f"Error building dashboard data: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard data failed: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with agent information"""
    return {
        "agent": "CI/CD Guardian",
        "status": "active",
        "version": "1.0.0",
        "documentation": "/docs",
        "endpoints": {
            "analyze": "/analyze",
            "metrics": "/metrics",
            "health": "/health",
            "dashboard": "/dashboard"
        }
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "path": str(request.url)
        }
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

