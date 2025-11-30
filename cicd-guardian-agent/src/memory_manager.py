"""
Memory Manager Module
Handles Short-Term Memory (JSON) and Long-Term Memory (SQLite)
Includes corruption detection and auto-recovery
"""
import json
import sqlite3
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class MemoryManager:
    """Manages agent memory with STM and LTM"""
    
    def __init__(self, stm_path: str = "src/memory.json", ltm_path: str = "src/memory.db"):
        """
        Initialize memory manager
        
        Args:
            stm_path: Path to short-term memory JSON file
            ltm_path: Path to long-term memory SQLite database
        """
        self.stm_path = Path(stm_path)
        self.ltm_path = Path(ltm_path)
        
        # Ensure directories exist
        self.stm_path.parent.mkdir(parents=True, exist_ok=True)
        self.ltm_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize memories
        self.stm = self._load_stm()
        self._init_ltm()
        
        logger.info("MemoryManager initialized")
    
    def _load_stm(self) -> Dict[str, Any]:
        """Load short-term memory from JSON file with corruption handling"""
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
        
        # Return default STM structure
        return self._get_default_stm()
    
    def _get_default_stm(self) -> Dict[str, Any]:
        """Get default STM structure"""
        return {
            "last_pipeline": None,
            "alert_count": 0,
            "last_analyzed": None,
            "total_analyzed": 0,
            "agent_status": "active"
        }
    
    def _save_stm(self) -> bool:
        """Save short-term memory to JSON file"""
        try:
            with open(self.stm_path, 'w', encoding='utf-8') as f:
                json.dump(self.stm, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save STM: {e}")
            return False
    
    def _init_ltm(self) -> None:
        """Initialize long-term memory SQLite database"""
        try:
            conn = sqlite3.connect(str(self.ltm_path))
            cursor = conn.cursor()
            
            # Create incidents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                    escalated BOOLEAN DEFAULT 0
                )
            """)
            
            # Create metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    total_analyzed INTEGER,
                    critical_count INTEGER,
                    high_count INTEGER,
                    medium_count INTEGER,
                    low_count INTEGER,
                    avg_duration REAL
                )
            """)
            
            # Create index for faster queries
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
            logger.error(f"LTM database corrupted, recreating: {e}")
            # Remove corrupted database
            try:
                if self.ltm_path.exists():
                    self.ltm_path.unlink()
                # Retry initialization
                self._init_ltm()
            except Exception as retry_error:
                logger.error(f"Failed to recreate LTM: {retry_error}")
        
        except Exception as e:
            logger.error(f"Error initializing LTM: {e}")
    
    def update_stm(self, pipeline_id: str, severity: str) -> None:
        """Update short-term memory with new analysis"""
        try:
            self.stm["last_pipeline"] = pipeline_id
            self.stm["last_analyzed"] = datetime.utcnow().isoformat()
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
        escalated: bool
    ) -> bool:
        """Save incident to long-term memory"""
        try:
            conn = sqlite3.connect(str(self.ltm_path))
            cursor = conn.cursor()
            
            # Serialize anomalies
            anomalies_json = json.dumps([{
                "type": a.type,
                "description": a.description,
                "severity": a.severity
            } for a in anomalies])
            
            cursor.execute("""
                INSERT INTO incidents 
                (pipeline_id, timestamp, status, severity, duration_seconds, 
                 branch, commit_sha, anomaly_count, anomalies, recommendation, escalated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pipeline_id,
                datetime.utcnow().isoformat(),
                status,
                severity,
                duration_seconds,
                branch,
                commit_sha,
                len(anomalies),
                anomalies_json,
                recommendation,
                escalated
            ))
            
            conn.commit()
            conn.close()
            logger.debug(f"Incident saved to LTM: {pipeline_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving incident to LTM: {e}")
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retrieve comprehensive metrics from LTM"""
        try:
            conn = sqlite3.connect(str(self.ltm_path))
            cursor = conn.cursor()
            
            # Total pipelines analyzed
            cursor.execute("SELECT COUNT(*) FROM incidents")
            total = cursor.fetchone()[0]
            
            # Count by severity
            cursor.execute("""
                SELECT severity, COUNT(*) 
                FROM incidents 
                GROUP BY severity
            """)
            severity_counts = dict(cursor.fetchall())
            
            # Average duration
            cursor.execute("SELECT AVG(duration_seconds) FROM incidents")
            avg_duration = cursor.fetchone()[0] or 0.0
            
            # Success rate (no anomalies)
            cursor.execute("SELECT COUNT(*) FROM incidents WHERE anomaly_count = 0")
            success_count = cursor.fetchone()[0]
            success_rate = (success_count / total * 100) if total > 0 else 100.0
            
            # Top anomalies
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
                except:
                    pass
            
            # Convert to list of dicts sorted by count
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
    
    def get_memory_status(self) -> Dict[str, str]:
        """Check memory system health"""
        stm_status = "ok" if self.stm_path.exists() else "missing"
        ltm_status = "ok" if self.ltm_path.exists() else "missing"
        
        # Test LTM connectivity
        try:
            conn = sqlite3.connect(str(self.ltm_path))
            conn.close()
        except Exception:
            ltm_status = "corrupted"
        
        return {
            "stm": stm_status,
            "ltm": ltm_status
        }

