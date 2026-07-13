"""PDF 텍스트 추출 모듈 — pypdf 기반"""
from pypdf import PdfReader


def extract_text(pdf_path: str) -> str:
    """PDF의 모든 페이지에서 텍스트를 추출해 하나의 문자열로 합친다."""
    reader = PdfReader(pdf_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def chunk_text(text: str, size: int = 1000) -> list[str]:
    """텍스트를 size자 단위로 분할한다."""
    return [text[i:i + size] for i in range(0, len(text), size)]
