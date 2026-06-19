"""
memory.py — SQLite 기반 설정 & 대화 기록 관리
모든 영속 데이터는 jivis.db에 저장 (memory.json 더 이상 사용 안 함)
"""
from src.memory.database import (
    save_memory,
    load_memory,
    load_all_memory,
    save_message,
    load_recent_messages,
    clear_conversations,
)

_DEFAULTS = {
    "user_name": "사용자",
    "jivis_name": "JIVIS",
    "personality": "반말",
}


# ── 설정 로드 / 저장 ──────────────────────────────────────

def load() -> dict:
    """DB에서 설정값 로드. 없으면 기본값 반환."""
    saved = load_all_memory()
    return {k: saved.get(k, v) for k, v in _DEFAULTS.items()}


def save(data: dict) -> None:
    """설정값을 DB에 저장."""
    for key, value in data.items():
        save_memory(key, value)


# ── 대화 히스토리 ─────────────────────────────────────────

def save_history(messages: list) -> None:
    """대화 내역을 conversations 테이블에 저장.
    기존 기록은 유지하고 새 메시지만 추가하는 방식이 아니라,
    app.py에서 responder()가 호출할 때마다 개별 메시지 저장.
    이 함수는 bulk upsert 용도로 사용.
    """
    # 현재 DB 기록 수와 비교해서 새 메시지만 추가
    # (responder에서 직접 save_message 호출로 대체 예정)
    pass


def load_history() -> list:
    """재접속 인사용: 최근 대화 10개 반환."""
    return load_recent_messages(limit=10)


def reset_conversations() -> None:
    """대화 초기화."""
    clear_conversations()
