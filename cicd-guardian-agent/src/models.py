"""
Pydantic models for CI/CD Guardian Agent
Defines request/response schemas with comprehensive validation
"""
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone


def _utc_now_iso() -> str:
    """Timezone-aware UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


class PipelineAnalysisRequest(BaseModel):
    """Request model for pipeline analysis"""
    pipeline_id: str = Field(..., description="Unique pipeline identifier")
    status: str = Field(..., description="Pipeline status: success, failed, or aborted")
    duration_seconds: int = Field(..., ge=0, description="Pipeline execution duration in seconds")
    logs: str = Field(..., description="Pipeline logs or output")
    vulnerabilities: List[str] = Field(default_factory=list, description="List of detected vulnerabilities")
    branch: str = Field(..., description="Git branch name")
    commit_sha: str = Field(..., description="Git commit SHA")
    test_coverage_percent: Optional[float] = Field(None, ge=0, le=100, description="Test coverage percentage")
    is_direct_push: Optional[bool] = Field(None, description="Whether this was a direct push to branch")
    pr_approved: Optional[bool] = Field(None, description="Whether PR was approved")
    pr_reviewers_count: Optional[int] = Field(None, ge=0, description="Number of PR reviewers")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "pipeline_id": "build-12345",
                "status": "failed",
                "duration_seconds": 450,
                "logs": "Error: Unit tests failed...",
                "vulnerabilities": ["CVE-2023-12345"],
                "branch": "main",
                "commit_sha": "a1b2c3d4",
                "test_coverage_percent": 65.0,
                "is_direct_push": True,
                "pr_approved": False,
                "pr_reviewers_count": 0
            }
        }
    )


class Anomaly(BaseModel):
    """Individual anomaly detected in pipeline"""
    type: str = Field(..., description="Type of anomaly")
    description: str = Field(..., description="Detailed description")
    severity: str = Field(..., description="Severity level: critical, high, medium, low")


class PipelineAnalysisResponse(BaseModel):
    """Response model for pipeline analysis"""
    pipeline_id: str
    status: str
    anomalies: List[Anomaly]
    severity: str = Field(..., description="Overall severity: critical, high, medium, low, none")
    recommendation: str = Field(..., description="Action recommendation")
    timestamp: str = Field(default_factory=_utc_now_iso)
    block_merge: bool = Field(..., description="The agent's verdict: whether this change should be blocked from merging")


class MetricsResponse(BaseModel):
    """Response model for metrics endpoint"""
    total_pipelines_analyzed: int
    critical_incidents: int
    high_severity_incidents: int
    medium_severity_incidents: int
    low_severity_incidents: int
    success_rate_percent: float
    average_duration_seconds: float
    last_analysis_timestamp: Optional[str]
    top_anomalies: List[Dict[str, Any]]


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Service health status")
    timestamp: str = Field(default_factory=_utc_now_iso)
    memory_status: Dict[str, str]
    config_loaded: bool
    uptime_seconds: float

