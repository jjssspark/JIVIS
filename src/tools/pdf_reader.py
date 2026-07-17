"""PDF 텍스트 추출 모듈 — pypdf 우선, 깨진 텍스트면 PyMuPDF로 재시도"""
import re
from pypdf import PdfReader
import fitz  # PyMuPDF

_READABLE_RE = re.compile(r"[a-zA-Z0-9가-힣ㄱ-ㅎㅏ-ㅣ\s.,!?()\-:;'\"/%]")


def _looks_garbled(text: str) -> bool:
    """추출된 텍스트가 폰트 인코딩 깨짐으로 인한 유니코드 쓰레기인지 휴리스틱으로 판단한다."""
    stripped = text.strip()
    if not stripped:
        return False  # 빈 텍스트는 스캔 이미지 PDF 케이스로 별도 처리됨
    readable = len(_READABLE_RE.findall(stripped))
    return readable / len(stripped) < 0.5


def _extract_with_pymupdf(pdf_path: str) -> str:
    with fitz.open(pdf_path) as doc:
        return "\n".join(page.get_text() for page in doc)


def extract_text(pdf_path: str) -> str:
    """PDF의 모든 페이지에서 텍스트를 추출해 하나의 문자열로 합친다.
    pypdf로 먼저 시도하고, 결과가 깨진 것처럼 보이면 PyMuPDF로 재시도한다."""
    reader = PdfReader(pdf_path)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    if _looks_garbled(text):
        fallback = _extract_with_pymupdf(pdf_path)
        if fallback.strip() and not _looks_garbled(fallback):
            return fallback
    return text


def chunk_text(text: str, size: int = 1000) -> list[str]:
    """텍스트를 size자 단위로 분할한다."""
    return [text[i:i + size] for i in range(0, len(text), size)]
