"""
Persistent log storage using SQLite with auto-rotation (max 10,000 entries).
"""
import sqlite3
import os
import json
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger("logs_store")

DB_PATH = os.path.expanduser("/root/.whatsapp_ai_logs.db")
MAX_ENTRIES = 10000

_local = threading.local()


def _get_conn() -> sqlite3.Connection:
    """Get thread-local database connection."""
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _init_db(_local.conn)
    return _local.conn


def _init_db(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL,
            level TEXT NOT NULL,
            source TEXT NOT NULL,
            message TEXT NOT NULL,
            details TEXT,
            traceback TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_source ON logs(source)")
    conn.commit()


def add_log(level: str, source: str, message: str, details=None, traceback: str = None):
    """Add a log entry. Auto-rotates if over MAX_ENTRIES."""
    try:
        conn = _get_conn()
        details_json = json.dumps(details) if details is not None else None
        conn.execute(
            "INSERT INTO logs (timestamp, level, source, message, details, traceback) VALUES (?, ?, ?, ?, ?, ?)",
            (time.time(), level, source, message[:500], details_json, traceback)
        )
        conn.commit()
        _rotate_if_needed(conn)
    except Exception as e:
        logger.error(f"Failed to write log: {e}")


def _rotate_if_needed(conn: sqlite3.Connection):
    """Delete oldest entries if over MAX_ENTRIES."""
    try:
        count = conn.execute("SELECT COUNT(*) FROM logs").fetchone()[0]
        if count > MAX_ENTRIES:
            to_delete = count - MAX_ENTRIES
            conn.execute(
                "DELETE FROM logs WHERE id IN (SELECT id FROM logs ORDER BY timestamp ASC LIMIT ?)",
                (to_delete,)
            )
            conn.execute("VACUUM")
            conn.commit()
    except Exception as e:
        logger.error(f"Rotation failed: {e}")


def get_logs(
    page: int = 1,
    per_page: int = 50,
    level: Optional[str] = None,
    source: Optional[str] = None,
    search: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> dict:
    """Get paginated logs with filters."""
    conn = _get_conn()
    conditions = []
    params = []

    if level:
        conditions.append("level = ?")
        params.append(level.upper())
    if source:
        conditions.append("source = ?")
        params.append(source.lower())
    if search:
        conditions.append("message LIKE ?")
        params.append(f"%{search}%")
    if from_date:
        try:
            ts = datetime.fromisoformat(from_date).timestamp()
            conditions.append("timestamp >= ?")
            params.append(ts)
        except:
            pass
    if to_date:
        try:
            ts = datetime.fromisoformat(to_date).timestamp()
            conditions.append("timestamp <= ?")
            params.append(ts)
        except:
            pass

    where = " WHERE " + " AND ".join(conditions) if conditions else ""

    count = conn.execute(f"SELECT COUNT(*) FROM logs{where}", params).fetchone()[0]
    total_pages = max(1, (count + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    offset = (page - 1) * per_page

    rows = conn.execute(
        f"SELECT * FROM logs{where} ORDER BY timestamp DESC LIMIT ? OFFSET ?",
        params + [per_page, offset]
    ).fetchall()

    entries = []
    for row in rows:
        entry = dict(row)
        entry["datetime"] = datetime.fromtimestamp(entry["timestamp"]).isoformat()
        if entry["details"]:
            try:
                entry["details"] = json.loads(entry["details"])
            except:
                pass
        entries.append(entry)

    return {
        "entries": entries,
        "page": page,
        "per_page": per_page,
        "total": count,
        "total_pages": total_pages,
    }


def get_log_by_id(log_id: int) -> Optional[dict]:
    """Get single log entry."""
    conn = _get_conn()
    row = conn.execute("SELECT * FROM logs WHERE id = ?", (log_id,)).fetchone()
    if not row:
        return None
    entry = dict(row)
    entry["datetime"] = datetime.fromtimestamp(entry["timestamp"]).isoformat()
    if entry["details"]:
        try:
            entry["details"] = json.loads(entry["details"])
        except:
            pass
    return entry


def clear_logs():
    """Delete all logs."""
    conn = _get_conn()
    conn.execute("DELETE FROM logs")
    conn.execute("VACUUM")
    conn.commit()


def get_log_stats() -> dict:
    """Get log statistics."""
    conn = _get_conn()
    by_level = {}
    by_source = {}
    total = 0
    last_24h = 0
    cutoff = time.time() - 86400

    rows = conn.execute("SELECT level, source, timestamp FROM logs").fetchall()
    for row in rows:
        total += 1
        by_level[row["level"]] = by_level.get(row["level"], 0) + 1
        by_source[row["source"]] = by_source.get(row["source"], 0) + 1
        if row["timestamp"] >= cutoff:
            last_24h += 1

    return {
        "total_logs": total,
        "last_24h_count": last_24h,
        "by_level": by_level,
        "by_source": by_source,
        "unique_sources": list(by_source.keys()),
    }
