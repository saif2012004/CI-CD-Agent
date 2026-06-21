"""
AI Analyzer — optional Groq-powered enrichment.

Uses Groq (Llama 3.3 70B by default) to explain a pipeline's failure in plain
English and suggest concrete remediation, going beyond the rule-based
recommendations. Groq is fast and has a generous free tier, which suits this
synchronous, best-effort enrichment.

It degrades gracefully:
- If GROQ_API_KEY is not set, or the `groq` SDK is not installed, AI analysis
  is disabled and the agent behaves exactly as before.
- Any API error is caught and logged; it never breaks pipeline analysis.
"""
import logging
import os
from typing import Optional, List, Any

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "llama-3.3-70b-versatile"
MAX_LOG_CHARS = 6000


class AIAnalyzer:
    """Optional Groq-backed root-cause + remediation generator."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model or os.getenv("GROQ_MODEL", DEFAULT_MODEL)
        self.timeout = timeout
        self.client = None

        if self.api_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key, timeout=timeout)
                logger.info(f"AIAnalyzer enabled (Groq model: {self.model})")
            except ImportError:
                logger.warning("groq SDK not installed; AI analysis disabled")
            except Exception as e:
                logger.warning(f"Failed to init AIAnalyzer (disabled): {e}")
        else:
            logger.info("GROQ_API_KEY not set; AI analysis disabled")

    @property
    def enabled(self) -> bool:
        return self.client is not None

    def analyze(
        self,
        status: str,
        severity: str,
        anomalies: List[Any],
        logs: str,
    ) -> Optional[str]:
        """
        Return a plain-English root-cause + remediation, or None if disabled
        or the call fails.
        """
        if not self.enabled:
            return None

        try:
            anomaly_lines = "\n".join(
                f"- [{a.severity}] {a.type}: {a.description}" for a in anomalies
            )
            truncated_logs = (logs or "")[-MAX_LOG_CHARS:]
            prompt = (
                "You are a CI/CD incident analyst. Given a pipeline's status, the "
                "policy anomalies detected, and its logs, explain the most likely "
                "root cause and give concrete remediation steps.\n\n"
                f"Pipeline status: {status}\n"
                f"Overall severity: {severity}\n"
                f"Anomalies:\n{anomaly_lines or 'none'}\n\n"
                f"Logs (truncated to last {MAX_LOG_CHARS} chars):\n"
                f"{truncated_logs or 'none'}\n\n"
                "Respond in plain text: a 1-3 sentence root-cause paragraph, then a "
                "line starting with 'Fix:' followed by 1-3 concrete bullet steps. "
                "Be specific and concise."
            )

            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=1024,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}],
            )

            text = (response.choices[0].message.content or "").strip()
            return text or None

        except Exception as e:
            logger.warning(f"AI analysis failed (optional): {e}")
            return None
