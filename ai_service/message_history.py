"""
Message history storage using SQLite.
"""
import sqlite3
import os
import time
import json
import threading
from datetime import datetime
from typing import Optional

DB_PATH = os.path.expanduser("/root/.whatsapp_ai_messages.db")

_local = threading.local()


def _get_conn() -> sqlite3.Connection:
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _init_db(_local.conn)
    return _local.conn


def _init_db(conn: sqlite3.Connection):
    conn.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT NOT NULL,
        from_phone TEXT,
        to_phone TEXT,
        content TEXT NOT NULL,
        timestamp REAL NOT NULL,
        direction TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'sent',
        metadata TEXT
    )""")
    for idx in ["idx_msg_phone", "idx_msg_timestamp", "idx_msg_direction"]:
        conn.execute(f"CREATE INDEX IF NOT EXISTS {idx} ON messages({idx.replace('idx_msg_', '')})")
    conn.commit()


def add_message(phone: str, content: str, direction: str, status: str = "sent", from_phone: str = None, to_phone: str = None, metadata: dict = None, sender: str = None):
    try:
        conn = _get_conn()
        conn.execute("INSERT INTO messages (phone, from_phone, to_phone, content, timestamp, direction, status, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (phone, from_phone or phone, to_phone or phone, content[:1000], time.time(), direction, status, json.dumps(metadata) if metadata else None))
        conn.commit()
    except Exception as e:
        print(f"Failed to store message: {e}")


def get_messages(page: int = 1, per_page: int = 50, phone: Optional[str] = None, direction: Optional[str] = None, status: Optional[str] = None) -> dict:
    conn = _get_conn()
    conditions, params = [], []
    if phone:
        conditions.append("(phone = ? OR from_phone = ? OR to_phone = ?)")
        params.extend([phone, phone, phone])
    if direction:
        conditions.append("direction = ?"), params.append(direction)
    if status:
        conditions.append("status = ?"), params.append(status)
    where = " WHERE " + " AND ".join(conditions) if conditions else ""
    count = conn.execute(f"SELECT COUNT(*) FROM messages{where}", params).fetchone()[0]
    total_pages = max(1, (count + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    offset = (page - 1) * per_page
    rows = conn.execute(f"SELECT * FROM messages{where} ORDER BY timestamp DESC LIMIT ? OFFSET ?", params + [per_page, offset]).fetchall()
    entries = []
    for row in rows:
        entry = dict(row)
        entry["datetime"] = datetime.fromtimestamp(entry["timestamp"]).isoformat()
        if entry["metadata"]:
            try: entry["metadata"] = json.loads(entry["metadata"])
            except: pass
        entries.append(entry)
    return {"entries": entries, "page": page, "per_page": per_page, "total": count, "total_pages": total_pages}


def get_conversation(phone: str, limit: int = 50) -> list:
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM messages WHERE phone = ? OR from_phone = ? OR to_phone = ? ORDER BY timestamp DESC LIMIT ?", (phone, phone, phone, limit)).fetchall()
    entries = []
    for row in rows:
        entry = dict(row)
        entry["datetime"] = datetime.fromtimestamp(entry["timestamp"]).isoformat()
        if entry["metadata"]:
            try: entry["metadata"] = json.loads(entry["metadata"])
            except: pass
        entries.append(entry)
    return entries


def clear_messages():
    conn = _get_conn()
    conn.execute("DELETE FROM messages")
    conn.execute("VACUUM")
    conn.commit()


def get_active_conversations() -> list:
    conn = _get_conn()
    rows = conn.execute("SELECT phone, COUNT(*) as count, MAX(timestamp) as last_message FROM messages GROUP BY phone ORDER BY last_message DESC LIMIT 100").fetchall()
    return [dict(r) for r in rows]


def get_message_stats() -> dict:
    conn = _get_conn()
    total = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    incoming = conn.execute("SELECT COUNT(*) FROM messages WHERE direction='incoming'").fetchone()[0]
    outgoing = conn.execute("SELECT COUNT(*) FROM messages WHERE direction='outgoing'").fetchone()[0]
    blocked = conn.execute("SELECT COUNT(*) FROM messages WHERE status='blocked'").fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM messages WHERE status='pending'").fetchone()[0]
    approved = conn.execute("SELECT COUNT(*) FROM messages WHERE status='approved'").fetchone()[0]
    return {"total": total, "incoming": incoming, "outgoing": outgoing, "blocked": blocked, "pending": pending, "approved": approved}
