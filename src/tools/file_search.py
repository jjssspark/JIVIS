"""파일 검색 모듈 — 실제 로컬 파일 시스템(기본값: 홈 디렉터리)에서 파일명/확장자로 검색"""
import os
from pathlib import Path

HOME_DIR = Path.home()
DOCUMENTS_DIR = Path(__file__).parent.parent.parent / "documents"

_EXTENSION_ALIASES = {
    "파이썬": "py",
    "피디에프": "pdf",
    "워드": "docx",
    "문서": "docx",
    "엑셀": "xlsx",
    "이미지": "png",
    "사진": "png",
    "텍스트": "txt",
}

_KNOWN_EXTENSIONS = {"py", "pdf", "docx", "xlsx", "csv", "txt", "png", "jpg", "jpeg", "md"}

# 정확한 파일명이 아니라 구어체로 물어볼 때 의미 없는 토큰 (검색어에서 제외)
# 문서 종류를 가리키는 범용 단어("강의자료", "파일" 등)도 포함 — 이런 단어는 너무 흔해서
# 실제 검색 의도(예: "이산수학")와 무관한 파일까지 매칭시켜 정확도를 떨어뜨리기 때문
_FILLER_TOKENS = {
    "같은거", "같은", "비슷한거", "비슷한", "관련", "그런거", "이런거", "저런거", "거",
    "파일", "자료", "강의자료", "강의노트", "문서", "노트", "보고서", "슬라이드",
    "발표자료", "리포트", "사진", "이미지",
}

# 홈 디렉터리 전체를 훑을 때 시간이 오래 걸리거나 의미 없는 결과만 나오는 폴더 제외
_SKIP_DIR_NAMES = {
    "Library", "Applications", "System", "Public",
    "node_modules", "__pycache__", "venv",
}


def _resolve_extension(query: str) -> str | None:
    """검색어가 확장자/확장자 별칭이면 실제 확장자를 반환, 아니면 None."""
    q = query.strip().lower().lstrip(".")
    if q in _EXTENSION_ALIASES:
        return _EXTENSION_ALIASES[q]
    if q in _KNOWN_EXTENSIONS:
        return q
    return None


def _iter_files(base_dir: Path):
    """숨김 폴더(.으로 시작)와 알려진 무거운 폴더는 건너뛰고 파일만 순회."""
    for root, dirnames, filenames in os.walk(base_dir):
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in _SKIP_DIR_NAMES]
        for name in filenames:
            yield Path(root) / name


def search_files(query: str, base_dir: Path = HOME_DIR) -> list[str]:
    """base_dir(기본값: 홈 디렉터리) 아래에서 파일명 또는 확장자로 파일을 검색해 전체 경로 목록을 반환한다.
    검색어가 여러 단어면 토큰 단위로 쪼개서, 파일명에 더 많은 토큰이 포함될수록 상위로 정렬한다
    (정확한 파일명이 아니라 "이산수학 강의자료 같은거"처럼 구어체로 물어봐도 찾을 수 있게)."""
    base_dir = Path(base_dir)
    if not base_dir.exists():
        return []

    ext = _resolve_extension(query)
    if ext:
        matches = sorted(str(p) for p in _iter_files(base_dir) if p.suffix.lower() == f".{ext}")
        return matches

    tokens = [t for t in query.strip().lower().split() if t not in _FILLER_TOKENS]
    if not tokens:
        return []

    scored: list[tuple[int, Path]] = []
    for p in _iter_files(base_dir):
        name = p.name.lower()
        score = sum(1 for t in tokens if t in name)
        if score > 0:
            scored.append((score, p))
    scored.sort(key=lambda item: (-item[0], str(item[1])))
    return [str(p) for _, p in scored]
