import json
import re
from pathlib import Path

# 프로젝트 루트 기준으로 memory.json 경로 고정
_MEMORY_FILE = Path(__file__).parent.parent.parent / "memory.json"

_DEFAULT: dict = {
    "user_name": "사용자",
    "jivis_name": "JIVIS",
    "personality": "비서 (존댓말)",
}


def load() -> dict:
    """memory.json을 읽어서 반환한다. 파일이 없으면 기본값을 반환한다."""
    if not _MEMORY_FILE.exists():
        return _DEFAULT.copy()

    with open(_MEMORY_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 혹시 누락된 키가 있으면 기본값으로 채움
    return {**_DEFAULT, **data}


def save(data: dict) -> None:
    """설정을 memory.json에 저장한다."""
    with open(_MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_history(messages: list) -> None:
    """마지막 대화 내역 저장 (최대 10개)."""
    data = load()
    data["last_messages"] = messages[-10:]
    save(data)


def load_history() -> list:
    """저장된 마지막 대화 내역 반환."""
    data = load()
    return data.get("last_messages", [])


def extract_name(text: str) -> str | None:
    """
    사용자 메시지에서 이름을 감지한다.
    예) "내 이름은 tina야", "나는 지수야", "지수라고 불러" → 이름 반환
    감지 못하면 None 반환.
    """
    patterns = [
        r"내\s*이름[은는이가]?\s*([가-힣a-zA-Z0-9]{2,5})[이야라]",  # 내 이름은 박지수야
        r"내\s*이름[은는이가]?\s*([가-힣a-zA-Z0-9]{2,5})\s*$",      # 내 이름은 박지수
        r"나[는은]\s*([가-힣a-zA-Z0-9]{2,5})[이야]야",               # 나는 박지수야
        r"나\s+([가-힣a-zA-Z0-9]{2,5})[이야]야",                    # 나 박지수야
        r"([가-힣a-zA-Z0-9]{2,5})(?:라고|이라고)\s*불러",            # 박지수라고 불러
        r"([가-힣a-zA-Z0-9]{2,5})(?:라고|이라고)\s*해줘",            # 박지수라고 해줘
        r"([가-힣a-zA-Z0-9]{2,5})(?:라고|이라고)\s*부르",            # 박지수라고 불러줘
        r"이름이\s*([가-힣a-zA-Z0-9]{2,5})[이야라]",                # 이름이 박지수야
        r"아\s*내?\s*이름\s*([가-힣a-zA-Z0-9]{2,5})[이야라]",       # 아 내 이름 박지수야
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            candidate = match.group(1)
            # 너무 짧거나 일반 단어 걸러내기
            stopwords = {"이름", "뭐야", "뭐", "없어", "맞아", "아니", "응", "네", "예"}
            if candidate not in stopwords:
                return candidate
    return None
