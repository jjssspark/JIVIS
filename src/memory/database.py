import os
import sqlite3
from pathlib import Path

_DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "jivis.db"


def _db_path() -> Path:
    """DB 파일 경로. JIVIS_DB_PATH 환경변수가 있으면 그 경로를 쓴다(테스트 격리용)."""
    override = os.environ.get("JIVIS_DB_PATH")
    return Path(override) if override else _DEFAULT_DB_PATH


def init_db() -> None:
    with sqlite3.connect(_db_path()) as conn:
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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                title     TEXT NOT NULL,
                content   TEXT NOT NULL,
                date_ref  TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                task       TEXT NOT NULL,
                done       INTEGER DEFAULT 0,
                due_date   TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # 기존 DB에 컬럼 없으면 추가 (마이그레이션)
        try:
            conn.execute("ALTER TABLE notes ADD COLUMN date_ref TEXT")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE todos ADD COLUMN due_date TEXT")
        except Exception:
            pass


def save_memory(key: str, value: str) -> None:
    with sqlite3.connect(_db_path()) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO memory (key, value) VALUES (?, ?)",
            (key, value),
        )


def load_memory(key: str) -> str | None:
    with sqlite3.connect(_db_path()) as conn:
        row = conn.execute(
            "SELECT value FROM memory WHERE key = ?", (key,)
        ).fetchone()
    return row[0] if row else None


def load_all_memory() -> dict:
    with sqlite3.connect(_db_path()) as conn:
        rows = conn.execute("SELECT key, value FROM memory").fetchall()
    return {k: v for k, v in rows}


def save_message(role: str, content: str) -> None:
    with sqlite3.connect(_db_path()) as conn:
        conn.execute(
            "INSERT INTO conversations (role, content) VALUES (?, ?)",
            (role, content),
        )


def load_recent_messages(limit: int = 20) -> list[dict]:
    with sqlite3.connect(_db_path()) as conn:
        rows = conn.execute(
            "SELECT role, content FROM conversations ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [{"role": r, "content": c} for r, c in reversed(rows)]


def load_last_message_time() -> str | None:
    with sqlite3.connect(_db_path()) as conn:
        row = conn.execute(
            "SELECT timestamp FROM conversations ORDER BY id DESC LIMIT 1"
        ).fetchone()
    return row[0] if row else None


def clear_conversations() -> None:
    with sqlite3.connect(_db_path()) as conn:
        conn.execute("DELETE FROM conversations")


def save_note(title: str, content: str, date_ref: str | None = None) -> None:
    with sqlite3.connect(_db_path()) as conn:
        conn.execute(
            "INSERT INTO notes (title, content, date_ref) VALUES (?, ?, ?)",
            (title, content, date_ref),
        )


def get_notes() -> list[dict]:
    with sqlite3.connect(_db_path()) as conn:
        rows = conn.execute(
            "SELECT id, title, content, date_ref, timestamp FROM notes ORDER BY id DESC"
        ).fetchall()
    return [
        {"id": r[0], "title": r[1], "content": r[2], "date_ref": r[3], "timestamp": r[4]}
        for r in rows
    ]


def delete_note(note_id: int) -> None:
    with sqlite3.connect(_db_path()) as conn:
        conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))


# ── 할 일 (todos) ─────────────────────────────────────────────
def save_todo(task: str, due_date: str | None = None) -> None:
    with sqlite3.connect(_db_path()) as conn:
        # 같은 task가 이미 미완료 상태로 있으면 중복 추가 안 함
        exists = conn.execute(
            "SELECT 1 FROM todos WHERE task = ? AND done = 0",
            (task,),
        ).fetchone()
        if not exists:
            conn.execute("INSERT INTO todos (task, due_date) VALUES (?, ?)", (task, due_date))


def get_todos(only_pending: bool = True) -> list[dict]:
    with sqlite3.connect(_db_path()) as conn:
        if only_pending:
            rows = conn.execute(
                "SELECT id, task, done, due_date, created_at FROM todos WHERE done = 0 ORDER BY due_date ASC, id ASC"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, task, done, due_date, created_at FROM todos ORDER BY due_date ASC, id ASC"
            ).fetchall()
    return [{"id": r[0], "task": r[1], "done": bool(r[2]), "due_date": r[3], "created_at": r[4]} for r in rows]


def done_todo(todo_id: int) -> None:
    with sqlite3.connect(_db_path()) as conn:
        conn.execute("UPDATE todos SET done = 1 WHERE id = ?", (todo_id,))


def delete_todo(todo_id: int) -> None:
    with sqlite3.connect(_db_path()) as conn:
        conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))


def clear_done_todos() -> int:
    """완료된 할 일 전부 삭제. 삭제된 개수 반환."""
    with sqlite3.connect(_db_path()) as conn:
        cur = conn.execute("DELETE FROM todos WHERE done = 1")
        return cur.rowcount


def get_overdue_todos() -> list[dict]:
    """오늘 날짜보다 이전 due_date인 미완료 할 일."""
    from datetime import date
    today = str(date.today())
    with sqlite3.connect(_db_path()) as conn:
        rows = conn.execute(
            "SELECT id, task, due_date FROM todos WHERE done = 0 AND due_date IS NOT NULL AND due_date < ?",
            (today,),
        ).fetchall()
    return [{"id": r[0], "task": r[1], "due_date": r[2]} for r in rows]


def get_today_todos() -> list[dict]:
    """오늘 마감 미완료 할 일."""
    from datetime import date
    today = str(date.today())
    with sqlite3.connect(_db_path()) as conn:
        rows = conn.execute(
            "SELECT id, task FROM todos WHERE done = 0 AND due_date = ?",
            (today,),
        ).fetchall()
    return [{"id": r[0], "task": r[1]} for r in rows]
