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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                title     TEXT NOT NULL,
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


def save_note(title: str, content: str) -> None: # 메모 넣는 도구
    with sqlite3.connect(_DB_PATH) as conn: # 서랍장 문을 열고, 끝나면 자동으로 닫아준다. 이거 빼먹으면 연결계속 쌓여서 앱이 느려지거나 파일이 잠기는 버그
        conn.execute(
            "INSERT INTO notes (title, content) VALUES (?, ?)",
            (title, content), # 보안사고 방지를 위한 SQL 인젝션 방지 코드
        )


def get_notes() -> list[dict]: # 꺼내는 도구
    with sqlite3.connect(_DB_PATH) as conn:
        rows = conn.execute(
            "SELECT id, title, content, timestamp FROM notes ORDER BY id DESC" # 최신 메모가 제일 위로 오게
        ).fetchall()
    return [
        {"id": r[0], "title": r[1], "content": r[2], "timestamp": r[3]} # 결과를 딕셔너리 리스트 형태로 바꿔주는 이유 : 나중에 UI에 뿌리거나, API로 다른 프로그램에 보낼 때 이 형태가 제일 다루기 쉬움
        for r in rows
    ]
