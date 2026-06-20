import sqlite3
from pathlib import Path

_DB_PATH = Path(__file__).parent.parent.parent / "jivis.db"


def init_db() -> None:
    with sqlite3.connect(_DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                role      TEXT NOT NULL,
                content   TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)


def save_memory(key: str, value: str) -> None:
    with sqlite3.connect(_DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO memory (key, value) VALUES (?, ?)",
            (key, value),
        )


def load_memory(key: str) -> str | None:
    with sqlite3.connect(_DB_PATH) as conn:
        row = conn.execute(
            "SELECT value FROM memory WHERE key = ?", (key,)
        ).fetchone()
    return row[0] if row else None


def load_all_memory() -> dict:
    with sqlite3.connect(_DB_PATH) as conn:
        rows = conn.execute("SELECT key, value FROM memory").fetchall()
    return {k: v for k, v in rows}


def save_message(role: str, content: str) -> None:
    with sqlite3.connect(_DB_PATH) as conn:
        conn.execute(
            "INSERT INTO conversations (role, content) VALUES (?, ?)",
            (role, content),
        )


def load_recent_messages(limit: int = 20) -> list[dict]:
    with sqlite3.connect(_DB_PATH) as conn:
        rows = conn.execute(
            "SELECT role, content FROM conversations ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [{"role": r, "content": c} for r, c in reversed(rows)]


def load_last_message_time() -> str | None:
    with sqlite3.connect(_DB_PATH) as conn:
        row = conn.execute(
            "SELECT timestamp FROM conversations ORDER BY id DESC LIMIT 1"
        ).fetchone()
    return row[0] if row else None


def clear_conversations() -> None:
    with sqlite3.connect(_DB_PATH) as conn:
        conn.execute("DELETE FROM conversations")
