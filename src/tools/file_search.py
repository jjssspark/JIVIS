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
    """base_dir(기본값: 홈 디렉터리) 아래에서 파일명 또는 확장자로 파일을 검색해 전체 경로 목록을 반환한다."""
    base_dir = Path(base_dir)
    if not base_dir.exists():
        return []

    ext = _resolve_extension(query)
    if ext:
        matches = (p for p in _iter_files(base_dir) if p.suffix.lower() == f".{ext}")
    else:
        q = query.strip().lower()
        matches = (p for p in _iter_files(base_dir) if q in p.name.lower())

    return sorted(str(p) for p in matches)
