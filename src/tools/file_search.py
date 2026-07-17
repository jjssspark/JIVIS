"""파일 검색 모듈 — JIVIS/documents 폴더에서 pathlib.glob으로 파일명/확장자 검색"""
from pathlib import Path

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


def _resolve_extension(query: str) -> str | None:
    """검색어가 확장자/확장자 별칭이면 실제 확장자를 반환, 아니면 None."""
    q = query.strip().lower().lstrip(".")
    if q in _EXTENSION_ALIASES:
        return _EXTENSION_ALIASES[q]
    if q in _KNOWN_EXTENSIONS:
        return q
    return None


def search_files(query: str, base_dir: Path = DOCUMENTS_DIR) -> list[str]:
    """base_dir(하위 폴더 포함) 안에서 파일명 또는 확장자로 파일을 검색해 이름 목록을 반환한다."""
    base_dir = Path(base_dir)
    if not base_dir.exists():
        return []

    ext = _resolve_extension(query)
    if ext:
        matches = (p for p in base_dir.rglob(f"*.{ext}") if p.is_file() and p.suffix.lower() == f".{ext}")
    else:
        q = query.strip().lower()
        matches = (p for p in base_dir.rglob("*") if p.is_file() and q in p.name.lower())

    return sorted(p.name for p in matches)
