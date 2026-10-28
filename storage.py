import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "cloudshield.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                file_name TEXT NOT NULL,
                event_type TEXT NOT NULL,
                events_in_window INTEGER NOT NULL DEFAULT 0,
                extension_changed INTEGER NOT NULL DEFAULT 0,
                risk_score INTEGER NOT NULL,
                severity TEXT NOT NULL,
                reasons TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'demo',
                reviewed INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.commit()


def save_event(event):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO events
            (created_at, file_name, event_type, events_in_window, extension_changed,
             risk_score, severity, reasons, source, reviewed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event.get("created_at", ""),
            event.get("file_name", "unknown"),
            event.get("event_type", "unknown"),
            int(event.get("events_in_window", 0)),
            int(bool(event.get("extension_changed", False))),
            int(event.get("risk_score", 0)),
            event.get("severity", "Low"),
            event.get("reasons", ""),
            event.get("source", "demo"),
            int(event.get("reviewed", 0)),
        ))
        conn.commit()


def list_events(limit=100, severity=None):
    with get_connection() as conn:
        if severity in {"Low", "Medium", "High"}:
            rows = conn.execute(
                "SELECT * FROM events WHERE severity = ? ORDER BY id DESC LIMIT ?",
                (severity, limit)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["extension_changed"] = bool(item["extension_changed"])
        item["reviewed"] = bool(item["reviewed"])
        result.append(item)
    return result


def mark_reviewed(event_id):
    with get_connection() as conn:
        conn.execute("UPDATE events SET reviewed = 1 WHERE id = ?", (event_id,))
        conn.commit()


def get_stats():
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        suspicious = conn.execute("SELECT COUNT(*) FROM events WHERE severity IN ('Medium', 'High')").fetchone()[0]
        high = conn.execute("SELECT COUNT(*) FROM events WHERE severity = 'High' AND reviewed = 0").fetchone()[0]
        high_total = conn.execute("SELECT COUNT(*) FROM events WHERE severity = 'High'").fetchone()[0]
        medium = conn.execute("SELECT COUNT(*) FROM events WHERE severity = 'Medium'").fetchone()[0]
        low = conn.execute("SELECT COUNT(*) FROM events WHERE severity = 'Low'").fetchone()[0]
    return {"total": total, "suspicious": suspicious, "high": high, "high_total": high_total, "medium": medium, "low": low}


def clear_demo_events():
    with get_connection() as conn:
        conn.execute("DELETE FROM events WHERE source LIKE 'demo-%' OR source = 'demo'")
        conn.commit()
