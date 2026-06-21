"""
Notifier Module
Handles Slack and Email notifications for critical/high severity incidents
"""
import logging
import json
import os
from typing import Dict, Any, List, Optional
import urllib.request
import urllib.error
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class Notifier:
    """Handles notification delivery via multiple channels"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize notifier with configuration
        
        Args:
            config: Notification configuration from rules.yaml
        """
        self.config = config
        # Environment variable takes precedence so secrets stay out of rules.yaml
        self.slack_webhook = os.getenv("SLACK_WEBHOOK_URL") or config.get("slack_webhook")
        self.discord_webhook = os.getenv("DISCORD_WEBHOOK_URL") or config.get("discord_webhook")
        self.teams_webhook = os.getenv("TEAMS_WEBHOOK_URL") or config.get("teams_webhook")
        self.email_config = config.get("email_smtp")
        self.alert_on = config.get("alert_on", ["critical", "high"])
        logger.info(f"Notifier initialized. Alert levels: {self.alert_on}")
    
    def should_notify(self, severity: str) -> bool:
        """Check if notification should be sent for given severity"""
        return severity in self.alert_on
    
    def send_notifications(
        self,
        pipeline_id: str,
        severity: str,
        anomalies: List[Any],
        recommendation: str,
        branch: str,
        commit_sha: str
    ) -> Dict[str, bool]:
        """
        Send notifications across all configured channels
        
        Returns:
            Dictionary with notification status for each channel
        """
        if not self.should_notify(severity):
            logger.info(f"Severity '{severity}' does not require notification")
            return {"notified": False}
        
        results = {}
        
        # Send Slack notification
        if self.slack_webhook:
            results["slack"] = self._send_slack_notification(
                pipeline_id, severity, anomalies, recommendation, branch, commit_sha
            )
        
        # Send Discord notification
        if self.discord_webhook:
            results["discord"] = self._send_webhook_text(
                self.discord_webhook,
                {"content": self._plain_message(pipeline_id, severity, anomalies, recommendation, branch, commit_sha)},
                channel="discord",
            )

        # Send Microsoft Teams notification
        if self.teams_webhook:
            results["teams"] = self._send_webhook_text(
                self.teams_webhook,
                {"text": self._plain_message(pipeline_id, severity, anomalies, recommendation, branch, commit_sha)},
                channel="teams",
            )

        # Send Email notification
        if self.email_config:
            results["email"] = self._send_email_notification(
                pipeline_id, severity, anomalies, recommendation, branch, commit_sha
            )

        return results

    def _plain_message(self, pipeline_id, severity, anomalies, recommendation, branch, commit_sha) -> str:
        """Build a plain-text alert body shared by Discord/Teams."""
        anomaly_text = "\n".join(f"• {a.description}" for a in anomalies)
        return (
            f"🛡️ CI/CD Guardian Alert — {severity.upper()}\n"
            f"Pipeline: {pipeline_id} | Branch: {branch} | Commit: {commit_sha[:8]}\n\n"
            f"Anomalies:\n{anomaly_text}\n\n"
            f"Recommendation:\n{recommendation}"
        )

    def _send_webhook_text(self, url: str, payload: Dict[str, Any], channel: str) -> bool:
        """POST a simple JSON payload to a webhook (Discord/Teams). Best-effort."""
        try:
            if not url or not url.startswith("http"):
                logger.info(f"{channel} webhook not configured - skipping")
                return False
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                # Discord returns 204, Teams returns 200
                ok = response.status in (200, 204)
                if ok:
                    logger.info(f"{channel} notification sent")
                else:
                    logger.warning(f"{channel} notification failed: status {response.status}")
                return ok
        except Exception as e:
            logger.warning(f"{channel} notification error (this is optional): {e}")
            return False
    
    def _send_slack_notification(
        self,
        pipeline_id: str,
        severity: str,
        anomalies: List[Any],
        recommendation: str,
        branch: str,
        commit_sha: str
    ) -> bool:
        """Send notification to Slack"""
        try:
            # Skip if webhook is not configured or invalid
            if not self.slack_webhook or self.slack_webhook == "None" or not self.slack_webhook.startswith("http"):
                logger.info("Slack webhook not configured - skipping notification")
                return False
            # Color coding based on severity
            color_map = {
                "critical": "#FF0000",  # Red
                "high": "#FF8C00",      # Orange
                "medium": "#FFD700",    # Yellow
                "low": "#1E90FF"        # Blue
            }
            
            color = color_map.get(severity, "#808080")
            
            # Build Slack message
            fields = [
                {
                    "title": "Pipeline ID",
                    "value": pipeline_id,
                    "short": True
                },
                {
                    "title": "Severity",
                    "value": severity.upper(),
                    "short": True
                },
                {
                    "title": "Branch",
                    "value": branch,
                    "short": True
                },
                {
                    "title": "Commit",
                    "value": commit_sha[:8],
                    "short": True
                },
                {
                    "title": "Anomalies Detected",
                    "value": str(len(anomalies)),
                    "short": False
                }
            ]
            
            # Add anomaly details
            anomaly_text = "\n".join([f"• {a.description}" for a in anomalies])
            
            payload = {
                "attachments": [
                    {
                        "fallback": f"CI/CD Guardian Alert: {severity.upper()} severity incident",
                        "color": color,
                        "title": "🛡️ CI/CD Guardian Alert",
                        "fields": fields,
                        "text": f"*Anomalies:*\n{anomaly_text}\n\n*Recommendation:*\n{recommendation}",
                        "footer": "CI/CD Guardian Agent",
                        "ts": int(__import__("time").time())
                    }
                ]
            }
            
            # Send to Slack
            req = urllib.request.Request(
                self.slack_webhook,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    logger.info(f"Slack notification sent for {pipeline_id}")
                    return True
                else:
                    logger.warning(f"Slack notification failed with status {response.status}")
                    return False
        
        except urllib.error.URLError as e:
            logger.warning(f"Failed to send Slack notification (this is optional): {e}")
            return False
        except Exception as e:
            logger.warning(f"Slack notification error (this is optional): {e}")
            return False
    
    def _send_email_notification(
        self,
        pipeline_id: str,
        severity: str,
        anomalies: List[Any],
        recommendation: str,
        branch: str,
        commit_sha: str
    ) -> bool:
        """Send notification via email"""
        try:
            if not self.email_config:
                return False
            
            # Extract email config
            smtp_server = self.email_config.get("server")
            smtp_port = self.email_config.get("port", 587)
            smtp_user = self.email_config.get("username")
            smtp_password = self.email_config.get("password")
            from_email = self.email_config.get("from_email")
            to_emails = self.email_config.get("to_emails", [])
            
            if not all([smtp_server, smtp_user, smtp_password, from_email, to_emails]):
                logger.warning("Email configuration incomplete")
                return False
            
            # Build email content
            subject = f"[CI/CD Guardian] {severity.upper()} Alert - {pipeline_id}"
            
            body = f"""
CI/CD Guardian Alert

Pipeline ID: {pipeline_id}
Severity: {severity.upper()}
Branch: {branch}
Commit: {commit_sha}

Anomalies Detected ({len(anomalies)}):
"""
            
            for anomaly in anomalies:
                body += f"\n• {anomaly.description}"
            
            body += f"\n\nRecommendation:\n{recommendation}"
            body += "\n\n---\nCI/CD Guardian Agent"
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = ", ".join(to_emails)
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email notification sent for {pipeline_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False

