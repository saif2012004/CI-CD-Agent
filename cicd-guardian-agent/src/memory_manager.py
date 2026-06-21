"""
Memory Manager Module
Handles Short-Term Memory (JSON) and Long-Term Memory (SQLite or Postgres).

Long-term memory uses Postgres when DATABASE_URL is set (durable across
restarts / redeploys), and falls back to a local SQLite file otherwise.
Includes corruption detection and auto-recovery for the SQLite backend.
"""
import json
import sqlite3
import logging
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


def detect_backend() -> Tuple[str, Optional[str]]:
    """
    Decide which LTM backend to use based on the DATABASE_URL env var.

    Returns (backend, url) where backend is "postgres" or "sqlite".
    """
    url = os.getenv("DATABASE_URL")
    if url and url.startswith(("postgres://", "postgresql://")):
        return "postgres", url
    return "sqlite", None


def to_paramstyle(sql: str, backend: str) -> str:
    """Translate '?' placeholders to '%s' for the Postgres driver."""
    return sql.replace("?", "%s") if backend == "postgres" else sql


class MemoryManager:
    """Manages agent memory with STM (JSON) and LTM (SQLite/Postgres)."""

    def __init__(self, stm_path: str = "src/memory.json", ltm_path: str = "src/memory.db"):
        """
        Initialize memory manager.

        Args:
            stm_path: Path to short-term memory JSON file.
            ltm_path: Path to SQLite database (ignored when using Postgres).
        """
        self.stm_path = Path(stm_path)
        self.ltm_path = Path(ltm_path)

        # Choose the LTM backend.
        self.backend, self.db_url = detect_backend()
        if self.backend == "postgres":
            try:
                import psycopg  # noqa: F401
            except ImportError:
                logger.error(
                    "DATABASE_URL points at Postgres but psycopg is not installed; "
                    "falling back to SQLite"
                )
                self.backend, self.db_url = "sqlite", None

        # Ensure directories exist (STM is always a file; LTM only for SQLite).
        self.stm_path.parent.mkdir(parents=True, exist_ok=True)
        if self.backend == "sqlite":
            self.ltm_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize memories.
        self.stm = self._load_stm()
        self._init_ltm()

        logger.info(f"MemoryManager initialized (LTM backend: {self.backend})")

    # ------------------------------------------------------------------ STM

    def _load_stm(self) -> Dict[str, Any]:
        """Load short-term memory from JSON file with corruption handling."""
        try:
            if self.stm_path.exists():
                with open(self.stm_path, 'r', encoding='utf-8') as f:
                    stm = json.load(f)
                    logger.info("STM loaded successfully")
                    return stm
        except json.JSONDecodeError as e:
            logger.error(f"STM corrupted, recreating: {e}")
        except Exception as e:
            logger.error(f"Error loading STM: {e}")

        return self._get_default_stm()

    def _get_default_stm(self) -> Dict[str, Any]:
        """Get default STM structure."""
        return {
            "last_pipeline": None,
            "alert_count": 0,
            "last_analyzed": None,
            "total_analyzed": 0,
            "agent_status": "active"
        }

    def _save_stm(self) -> bool:
        """Save short-term memory to JSON file."""
        try:
            with open(self.stm_path, 'w', encoding='utf-8') as f:
                json.dump(self.stm, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save STM: {e}")
            return False

    # ------------------------------------------------------------------ LTM

    def _connect(self):
        """Open a connection to the active LTM backend."""
        if self.backend == "postgres":
            import psycopg
            return psycopg.connect(self.db_url)
        return sqlite3.connect(str(self.ltm_path))

    def _q(self, sql: str) -> str:
        """Adapt placeholder style to the active backend."""
        return to_paramstyle(sql, self.backend)

    def _init_ltm(self) -> None:
        """Initialize the long-term memory database (idempotent)."""
        if self.backend == "postgres":
            pk = "SERIAL PRIMARY KEY"
            bool_default = "BOOLEAN DEFAULT FALSE"
        else:
            pk = "INTEGER PRIMARY KEY AUTOINCREMENT"
            bool_default = "BOOLEAN DEFAULT 0"

        try:
            conn = self._connect()
            cursor = conn.cursor()

            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS incidents (
                    id {pk},
                    pipeline_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    status TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    duration_seconds INTEGER,
                    branch TEXT,
                    commit_sha TEXT,
                    anomaly_count INTEGER,
                    anomalies TEXT,
                    recommendation TEXT,
                    blocked {bool_default}
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_pipeline_id
                ON incidents(pipeline_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_severity
                ON incidents(severity)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON incidents(timestamp)
            """)

            conn.commit()
            conn.close()
            logger.info("LTM database initialized")

        except sqlite3.DatabaseError as e:
            # File-level corruption recovery only applies to SQLite.
            logger.error(f"LTM database corrupted, recreating: {e}")
            try:
                if self.backend == "sqlite" and self.ltm_path.exists():
                    self.ltm_path.unlink()
                    self._init_ltm()
            except Exception as retry_error:
                logger.error(f"Failed to recreate LTM: {retry_error}")

        except Exception as e:
            logger.error(f"Error initializing LTM: {e}")

    def update_stm(self, pipeline_id: str, severity: str) -> None:
        """Update short-term memory with new analysis."""
        try:
            self.stm["last_pipeline"] = pipeline_id
            self.stm["last_analyzed"] = datetime.now(timezone.utc).isoformat()
            self.stm["total_analyzed"] = self.stm.get("total_analyzed", 0) + 1

            if severity in ["critical", "high"]:
                self.stm["alert_count"] = self.stm.get("alert_count", 0) + 1

            self._save_stm()
            logger.debug(f"STM updated for pipeline {pipeline_id}")

        except Exception as e:
            logger.error(f"Error updating STM: {e}")

    def save_incident(
        self,
        pipeline_id: str,
        status: str,
        severity: str,
        duration_seconds: int,
        branch: str,
        commit_sha: str,
        anomalies: List[Any],
        recommendation: str,
        blocked: bool
    ) -> bool:
        """Save incident to long-term memory."""
        try:
            conn = self._connect()
            cursor = conn.cursor()

            anomalies_json = json.dumps([{
                "type": a.type,
                "description": a.description,
                "severity": a.severity
            } for a in anomalies])

            cursor.execute(self._q("""
                INSERT INTO incidents
                (pipeline_id, timestamp, status, severity, duration_seconds,
                 branch, commit_sha, anomaly_count, anomalies, recommendation, blocked)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """), (
                pipeline_id,
                datetime.now(timezone.utc).isoformat(),
                status,
                severity,
                duration_seconds,
                branch,
                commit_sha,
                len(anomalies),
                anomalies_json,
                recommendation,
                blocked
            ))

            conn.commit()
            conn.close()
            logger.debug(f"Incident saved to LTM: {pipeline_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving incident to LTM: {e}")
            return False

    def get_metrics(self) -> Dict[str, Any]:
        """Retrieve comprehensive metrics from LTM."""
        try:
            conn = self._connect()
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM incidents")
            total = cursor.fetchone()[0]

            cursor.execute("""
                SELECT severity, COUNT(*)
                FROM incidents
                GROUP BY severity
            """)
            severity_counts = dict(cursor.fetchall())

            cursor.execute("SELECT AVG(duration_seconds) FROM incidents")
            avg_duration = float(cursor.fetchone()[0] or 0.0)

            cursor.execute("SELECT COUNT(*) FROM incidents WHERE anomaly_count = 0")
            success_count = cursor.fetchone()[0]
            success_rate = (success_count / total * 100) if total > 0 else 100.0

            cursor.execute("""
                SELECT anomalies
                FROM incidents
                WHERE anomaly_count > 0
                ORDER BY timestamp DESC
                LIMIT 100
            """)

            anomaly_counts: Dict[str, int] = {}
            for row in cursor.fetchall():
                try:
                    anomalies = json.loads(row[0])
                    for anomaly in anomalies:
                        atype = anomaly.get("type", "unknown")
                        anomaly_counts[atype] = anomaly_counts.get(atype, 0) + 1
                except Exception:
                    pass

            top_anomalies = [
                {"type": k, "count": v}
                for k, v in sorted(anomaly_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            ]

            conn.close()

            return {
                "total_pipelines_analyzed": total,
                "critical_incidents": severity_counts.get("critical", 0),
                "high_severity_incidents": severity_counts.get("high", 0),
                "medium_severity_incidents": severity_counts.get("medium", 0),
                "low_severity_incidents": severity_counts.get("low", 0),
                "success_rate_percent": round(success_rate, 2),
                "average_duration_seconds": round(avg_duration, 2),
                "last_analysis_timestamp": self.stm.get("last_analyzed"),
                "top_anomalies": top_anomalies
            }

        except Exception as e:
            logger.error(f"Error retrieving metrics: {e}")
            return {
                "total_pipelines_analyzed": 0,
                "critical_incidents": 0,
                "high_severity_incidents": 0,
                "medium_severity_incidents": 0,
                "low_severity_incidents": 0,
                "success_rate_percent": 0.0,
                "average_duration_seconds": 0.0,
                "last_analysis_timestamp": None,
                "top_anomalies": []
            }

    def get_recent_incidents(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return the most recent incidents (newest first) for the dashboard."""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(self._q("""
                SELECT pipeline_id, timestamp, status, severity, branch,
                       commit_sha, anomaly_count, blocked
                FROM incidents
                ORDER BY id DESC
                LIMIT ?
            """), (limit,))
            rows = cursor.fetchall()
            conn.close()

            return [
                {
                    "pipeline_id": r[0],
                    "timestamp": r[1],
                    "status": r[2],
                    "severity": r[3],
                    "branch": r[4],
                    "commit_sha": (r[5] or "")[:8],
                    "anomaly_count": r[6],
                    "blocked": bool(r[7]),
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(f"Error retrieving recent incidents: {e}")
            return []

    def get_trends(self, window: int = 10) -> Dict[str, Any]:
        """
        Detect regressions over recent history by comparing the most recent
        incidents against the preceding ones (duration and block-rate trends).
        """
        empty = {"available": False, "sample_size": 0, "insights": []}
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(self._q("""
                SELECT duration_seconds, blocked
                FROM incidents
                ORDER BY id DESC
                LIMIT ?
            """), (window * 2,))
            rows = cursor.fetchall()
            conn.close()

            if len(rows) < 4:
                return empty

            half = len(rows) // 2
            recent = rows[:half]
            previous = rows[half:]

            def avg_duration(group):
                vals = [r[0] for r in group if r[0] is not None]
                return sum(vals) / len(vals) if vals else 0.0

            def block_rate(group):
                return sum(1 for r in group if r[1]) / len(group) if group else 0.0

            rec_dur, prev_dur = avg_duration(recent), avg_duration(previous)
            rec_block, prev_block = block_rate(recent), block_rate(previous)

            dur_pct = ((rec_dur - prev_dur) / prev_dur * 100) if prev_dur else 0.0
            block_delta = (rec_block - prev_block) * 100  # percentage points

            def direction(pct, threshold=10.0):
                if pct > threshold:
                    return "rising"
                if pct < -threshold:
                    return "falling"
                return "stable"

            dur_dir = direction(dur_pct)
            block_dir = direction(block_delta, threshold=10.0)

            insights = []
            if dur_dir == "rising":
                insights.append(f"⏱️ Build duration is trending up ({dur_pct:+.0f}%).")
            elif dur_dir == "falling":
                insights.append(f"⏱️ Build duration is improving ({dur_pct:+.0f}%).")
            if block_dir == "rising":
                insights.append(f"🚫 Merges are being blocked more often ({block_delta:+.0f} pts).")
            elif block_dir == "falling":
                insights.append(f"✅ Fewer merges blocked recently ({block_delta:+.0f} pts).")
            if not insights:
                insights.append("No significant trend changes detected.")

            return {
                "available": True,
                "sample_size": len(rows),
                "duration": {
                    "direction": dur_dir,
                    "percent_change": round(dur_pct, 1),
                    "recent_avg_seconds": round(rec_dur, 1),
                    "previous_avg_seconds": round(prev_dur, 1),
                },
                "block_rate": {
                    "direction": block_dir,
                    "delta_points": round(block_delta, 1),
                    "recent_percent": round(rec_block * 100, 1),
                    "previous_percent": round(prev_block * 100, 1),
                },
                "insights": insights,
            }
        except Exception as e:
            logger.error(f"Error computing trends: {e}")
            return empty

    def get_memory_status(self) -> Dict[str, str]:
        """Check memory system health."""
        stm_status = "ok" if self.stm_path.exists() else "missing"

        ltm_status = "ok"
        try:
            conn = self._connect()
            conn.close()
        except Exception:
            ltm_status = "corrupted"

        return {
            "stm": stm_status,
            "ltm": ltm_status,
            "ltm_backend": self.backend
        }
