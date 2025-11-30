"""
Policy Enforcer Module
Validates branch protection, test coverage, PR requirements, and build health
"""
from typing import List, Dict, Any, Optional
import logging
from src.models import Anomaly

logger = logging.getLogger(__name__)


class PolicyEnforcer:
    """Enforces CI/CD policies and detects violations"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize policy enforcer with configuration
        
        Args:
            config: Configuration dictionary from rules.yaml
        """
        self.config = config
        self.branch_protection = config.get("branch_protection", {})
        self.test_coverage = config.get("test_coverage", {})
        logger.info("PolicyEnforcer initialized with config")
    
    def analyze_pipeline(
        self,
        status: str,
        duration_seconds: int,
        vulnerabilities: List[str],
        branch: str,
        commit_sha: str,
        logs: str,
        test_coverage_percent: Optional[float] = None,
        is_direct_push: Optional[bool] = None,
        pr_approved: Optional[bool] = None,
        pr_reviewers_count: Optional[int] = None
    ) -> List[Anomaly]:
        """
        Analyze pipeline and detect all anomalies
        
        Returns:
            List of detected anomalies with severity levels
        """
        anomalies: List[Anomaly] = []
        
        # Check build status
        anomalies.extend(self._check_build_status(status))
        
        # Check build duration
        anomalies.extend(self._check_duration(duration_seconds))
        
        # Check vulnerabilities
        anomalies.extend(self._check_vulnerabilities(vulnerabilities))
        
        # Check branch protection
        anomalies.extend(self._check_branch_protection(branch, is_direct_push))
        
        # Check PR approval
        anomalies.extend(self._check_pr_approval(branch, pr_approved, pr_reviewers_count))
        
        # Check test coverage
        anomalies.extend(self._check_test_coverage(test_coverage_percent))
        
        logger.info(f"Analysis complete: {len(anomalies)} anomalies detected")
        return anomalies
    
    def _check_build_status(self, status: str) -> List[Anomaly]:
        """Check if build failed or was aborted"""
        anomalies = []
        if status.lower() == "failed":
            anomalies.append(Anomaly(
                type="build_failure",
                description="Pipeline build failed",
                severity="high"
            ))
        elif status.lower() == "aborted":
            anomalies.append(Anomaly(
                type="build_aborted",
                description="Pipeline build was aborted before completion",
                severity="high"
            ))
        return anomalies
    
    def _check_duration(self, duration_seconds: int) -> List[Anomaly]:
        """Check if build duration exceeds threshold"""
        anomalies = []
        max_duration = 600  # 10 minutes
        if duration_seconds > max_duration:
            anomalies.append(Anomaly(
                type="excessive_duration",
                description=f"Build duration ({duration_seconds}s) exceeds threshold ({max_duration}s)",
                severity="medium"
            ))
        return anomalies
    
    def _check_vulnerabilities(self, vulnerabilities: List[str]) -> List[Anomaly]:
        """Check for security vulnerabilities"""
        anomalies = []
        if vulnerabilities:
            # Any CVE is critical
            for vuln in vulnerabilities:
                anomalies.append(Anomaly(
                    type="security_vulnerability",
                    description=f"Security vulnerability detected: {vuln}",
                    severity="critical"
                ))
        return anomalies
    
    def _check_branch_protection(
        self, 
        branch: str, 
        is_direct_push: Optional[bool]
    ) -> List[Anomaly]:
        """Check branch protection rules"""
        anomalies = []
        protected_branches = self.branch_protection.get("protected_branches", [])
        require_pr = self.branch_protection.get("require_pull_request", True)
        
        if branch in protected_branches:
            if is_direct_push is True and require_pr:
                anomalies.append(Anomaly(
                    type="branch_protection_violation",
                    description=f"Direct push to protected branch '{branch}' is not allowed",
                    severity="critical"
                ))
        
        return anomalies
    
    def _check_pr_approval(
        self,
        branch: str,
        pr_approved: Optional[bool],
        pr_reviewers_count: Optional[int]
    ) -> List[Anomaly]:
        """Check PR approval requirements"""
        anomalies = []
        protected_branches = self.branch_protection.get("protected_branches", [])
        min_approvals = self.branch_protection.get("min_approvals", 1)
        
        if branch in protected_branches:
            # Check if PR was approved
            if pr_approved is False:
                anomalies.append(Anomaly(
                    type="pr_not_approved",
                    description=f"Pull request to '{branch}' was not approved",
                    severity="critical"
                ))
            
            # Check reviewer count
            if pr_reviewers_count is not None and pr_reviewers_count < min_approvals:
                anomalies.append(Anomaly(
                    type="insufficient_reviewers",
                    description=f"PR has {pr_reviewers_count} reviewer(s), minimum {min_approvals} required",
                    severity="high"
                ))
        
        return anomalies
    
    def _check_test_coverage(self, coverage_percent: Optional[float]) -> List[Anomaly]:
        """Check test coverage requirements"""
        anomalies = []
        min_coverage = self.test_coverage.get("minimum_percentage", 80.0)
        
        if coverage_percent is not None and coverage_percent < min_coverage:
            anomalies.append(Anomaly(
                type="insufficient_test_coverage",
                description=f"Test coverage ({coverage_percent}%) is below minimum ({min_coverage}%)",
                severity="critical"
            ))
        
        return anomalies
    
    def calculate_severity(self, anomalies: List[Anomaly]) -> str:
        """
        Calculate overall severity based on anomalies
        
        Rules:
        - Any critical anomaly → critical
        - 3+ anomalies → critical
        - Any high anomaly → high
        - Any medium anomaly → medium
        - Any low anomaly → low
        - No anomalies → none
        """
        if not anomalies:
            return "none"
        
        # Count by severity
        critical_count = sum(1 for a in anomalies if a.severity == "critical")
        high_count = sum(1 for a in anomalies if a.severity == "high")
        medium_count = sum(1 for a in anomalies if a.severity == "medium")
        
        # Any critical anomaly or 3+ anomalies → critical
        if critical_count > 0 or len(anomalies) >= 3:
            return "critical"
        
        if high_count > 0:
            return "high"
        
        if medium_count > 0:
            return "medium"
        
        return "low"
    
    def generate_recommendation(self, anomalies: List[Anomaly], severity: str) -> str:
        """
        Generate actionable recommendation based on anomalies
        
        Args:
            anomalies: List of detected anomalies
            severity: Overall severity level
            
        Returns:
            Detailed recommendation string
        """
        if not anomalies:
            return "Pipeline passed all checks. No action required."
        
        recommendation_parts = []
        
        # Critical header for critical issues
        if severity == "critical":
            recommendation_parts.append("🚨 URGENT: Block merge until issues resolved.")
        
        # Group anomalies by type
        for anomaly in anomalies:
            recommendation_parts.append(f"- {anomaly.description}")
        
        # Add specific actions
        recommendation_parts.append("\nRecommended Actions:")
        
        # Check for specific anomaly types
        anomaly_types = {a.type for a in anomalies}
        
        if "security_vulnerability" in anomaly_types:
            recommendation_parts.append("• Update dependencies to patch security vulnerabilities")
        
        if "branch_protection_violation" in anomaly_types:
            recommendation_parts.append("• Revert direct push and create a pull request instead")
        
        if "insufficient_test_coverage" in anomaly_types:
            recommendation_parts.append("• Add more unit tests to meet coverage requirements")
        
        if "pr_not_approved" in anomaly_types or "insufficient_reviewers" in anomaly_types:
            recommendation_parts.append("• Obtain required PR approvals before merging")
        
        if "build_failure" in anomaly_types:
            recommendation_parts.append("• Fix failing tests and build errors")
        
        if "excessive_duration" in anomaly_types:
            recommendation_parts.append("• Optimize build pipeline to reduce execution time")
        
        return "\n".join(recommendation_parts)

