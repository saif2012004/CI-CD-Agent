"""
CI/CD Guardian Agent - Main FastAPI Application
Supervisor-Worker Architecture: Worker Agent for CI/CD Pipeline Monitoring
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import logging
import yaml
import time
from pathlib import Path
from typing import Dict, Any
import os

from src.models import (
    PipelineAnalysisRequest,
    PipelineAnalysisResponse,
    MetricsResponse,
    HealthResponse,
    AgentRegistrationResponse
)
from src.policy_enforcer import PolicyEnforcer
from src.notifier import Notifier
from src.memory_manager import MemoryManager

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

# Initialize FastAPI app
app = FastAPI(
    title="CI/CD Guardian Agent",
    description="Intelligent CI/CD pipeline monitoring and policy enforcement agent",
    version="1.0.0"
)

# Global state
START_TIME = time.time()
CONFIG: Dict[str, Any] = {}
POLICY_ENFORCER: PolicyEnforcer = None
NOTIFIER: Notifier = None
MEMORY: MemoryManager = None


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


@app.on_event("startup")
async def startup_event():
    """Initialize agent on startup"""
    global CONFIG, POLICY_ENFORCER, NOTIFIER, MEMORY
    
    logger.info("🛡️  CI/CD Guardian Agent starting up...")
    
    # Load configuration
    CONFIG = load_config()
    
    # Initialize components
    POLICY_ENFORCER = PolicyEnforcer(CONFIG)
    NOTIFIER = Notifier(CONFIG.get("notifications", {}))
    MEMORY = MemoryManager()
    
    logger.info("✅ CI/CD Guardian Agent ready")


@app.post("/analyze", response_model=PipelineAnalysisResponse)
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
            pr_approved=request.pr_approved,
            pr_reviewers_count=request.pr_reviewers_count
        )
        
        # Calculate overall severity
        severity = POLICY_ENFORCER.calculate_severity(anomalies)
        
        # Generate recommendation
        recommendation = POLICY_ENFORCER.generate_recommendation(anomalies, severity)
        
        # Determine if escalation needed
        escalate = severity in ["critical", "high"]
        
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
            escalated=escalate
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
            escalate_to_supervisor=escalate
        )
        
        logger.info(f"Analysis complete: {severity} severity, {len(anomalies)} anomalies")
        return response
    
    except Exception as e:
        logger.error(f"Error analyzing pipeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    Get comprehensive metrics for supervisor
    
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


@app.post("/register", response_model=AgentRegistrationResponse)
async def register_with_supervisor(request: Request):
    """
    Registration endpoint for supervisor integration
    
    Returns complete agent metadata and capabilities
    """
    try:
        # Get base URL from request
        base_url = str(request.base_url).rstrip('/')
        
        response = AgentRegistrationResponse(
            agent_id="cicd-guardian-001",
            agent_type="CI/CD Monitoring & Policy Enforcement",
            capabilities=[
                "Branch protection enforcement",
                "Pull request validation",
                "Test coverage monitoring (≥80%)",
                "Security vulnerability detection",
                "Build health monitoring",
                "Slack/Email notifications",
                "Real-time anomaly detection",
                "Metrics and reporting"
            ],
            endpoints={
                "analyze": f"{base_url}/analyze",
                "metrics": f"{base_url}/metrics",
                "health": f"{base_url}/health",
                "docs": f"{base_url}/docs"
            },
            status="active",
            metadata={
                "version": "1.0.0",
                "architecture": "Supervisor-Worker",
                "policies_enforced": [
                    "No direct push to main/master/develop",
                    "Minimum 1 PR approval required",
                    "Test coverage ≥80%",
                    "Build duration threshold: 600s",
                    "Zero vulnerabilities (CVEs)"
                ],
                "notification_channels": ["slack", "email"],
                "memory_system": ["STM (JSON)", "LTM (SQLite)"],
                "escalation_severity": ["critical", "high"]
            }
        )
        
        logger.info("Agent registered with supervisor")
        return response
    
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


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
            "register": "/register"
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

