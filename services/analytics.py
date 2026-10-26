"""Analytics and metrics collection service using SQLite."""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any


class AnalyticsStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        conn = self._connect()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token TEXT NOT NULL,
                    user_id INTEGER,
                    source_host TEXT,
                    status TEXT NOT NULL,
                    send_type TEXT,
                    file_size INTEGER,
                    download_seconds REAL,
                    upload_seconds REAL,
                    retry_count INTEGER DEFAULT 0,
                    error_category TEXT,
                    created_at REAL NOT NULL,
                    completed_at REAL
                );
                CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_at);
                CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
                CREATE INDEX IF NOT EXISTS idx_jobs_user ON jobs(user_id);

                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    user_id INTEGER,
                    metadata TEXT,
                    created_at REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at);
                CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);

                CREATE TABLE IF NOT EXISTS resource_samples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cpu_percent REAL,
                    memory_mb REAL,
                    disk_used_mb REAL,
                    disk_free_mb REAL,
                    created_at REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_resources_created ON resource_samples(created_at);
            """)
            conn.commit()
        finally:
            conn.close()

    def record_job_created(self, token: str, user_id: int, source_host: str) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO jobs (token, user_id, source_host, status, created_at) VALUES (?, ?, ?, 'queued', ?)",
                (token, user_id, source_host, time.time()),
            )
            conn.commit()
        finally:
            conn.close()

    def record_job_completed(self, token: str, status: str, send_type: str = None,
                            file_size: int = None, download_seconds: float = None,
                            upload_seconds: float = None, error_category: str = None,
                            retry_count: int = 0) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """UPDATE jobs SET status=?, send_type=?, file_size=?, download_seconds=?,
                   upload_seconds=?, error_category=?, retry_count=?, completed_at=?
                   WHERE token=?""",
                (status, send_type, file_size, download_seconds, upload_seconds,
                 error_category, retry_count, time.time(), token),
            )
            conn.commit()
        finally:
            conn.close()

    def record_event(self, event_type: str, user_id: int = None, metadata: str = None) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO events (event_type, user_id, metadata, created_at) VALUES (?, ?, ?, ?)",
                (event_type, user_id, metadata, time.time()),
            )
            conn.commit()
        finally:
            conn.close()

    def record_resource_sample(self, cpu_percent: float, memory_mb: float,
                              disk_used_mb: float, disk_free_mb: float) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO resource_samples (cpu_percent, memory_mb, disk_used_mb, disk_free_mb, created_at) VALUES (?, ?, ?, ?, ?)",
                (cpu_percent, memory_mb, disk_used_mb, disk_free_mb, time.time()),
            )
            conn.commit()
        finally:
            conn.close()

    def get_overview_stats(self) -> dict[str, Any]:
        conn = self._connect()
        try:
            total_jobs = conn.execute("SELECT COUNT(*) as c FROM jobs").fetchone()["c"]
            successful = conn.execute("SELECT COUNT(*) as c FROM jobs WHERE status='completed'").fetchone()["c"]
            failed = conn.execute("SELECT COUNT(*) as c FROM jobs WHERE status='failed'").fetchone()["c"]
            cancelled = conn.execute("SELECT COUNT(*) as c FROM jobs WHERE status='cancelled'").fetchone()["c"]
            queued = conn.execute("SELECT COUNT(*) as c FROM jobs WHERE status='queued'").fetchone()["c"]
            active = conn.execute("SELECT COUNT(*) as c FROM jobs WHERE status='processing'").fetchone()["c"]
            total_bytes = conn.execute("SELECT COALESCE(SUM(file_size), 0) as s FROM jobs").fetchone()["s"]
            avg_duration = conn.execute("SELECT COALESCE(AVG(download_seconds + upload_seconds), 0) as a FROM jobs WHERE status='completed'").fetchone()["a"]
            total_users = conn.execute("SELECT COUNT(DISTINCT user_id) as c FROM jobs").fetchone()["c"]
            
            return {
                "total_jobs": total_jobs,
                "successful": successful,
                "failed": failed,
                "cancelled": cancelled,
                "queued": queued,
                "active": active,
                "total_bytes": total_bytes,
                "avg_duration": avg_duration,
                "total_users": total_users,
            }
        finally:
            conn.close()

    def get_jobs(self, limit: int = 50, offset: int = 0, status: str = None) -> list[dict]:
        conn = self._connect()
        try:
            if status:
                rows = conn.execute(
                    "SELECT * FROM jobs WHERE status=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (status, limit, offset),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (limit, offset),
                ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_daily_stats(self, days: int = 7) -> list[dict]:
        conn = self._connect()
        try:
            cutoff = time.time() - (days * 86400)
            rows = conn.execute(
                """SELECT date(created_at, 'unixepoch') as day,
                          COUNT(*) as total,
                          SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as success,
                          SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed
                   FROM jobs
                   WHERE created_at >= ?
                   GROUP BY day
                   ORDER BY day""",
                (cutoff,),
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def cleanup_old_records(self, retention_days: int = 30) -> int:
        conn = self._connect()
        try:
            cutoff = time.time() - (retention_days * 86400)
            cursor = conn.execute("DELETE FROM jobs WHERE created_at < ?", (cutoff,))
            conn.execute("DELETE FROM events WHERE created_at < ?", (cutoff,))
            conn.execute("DELETE FROM resource_samples WHERE created_at < ?", (cutoff,))
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()
