"""Day10 통합 테스트 — 메모/할일/PDF/파일검색을 실제 jivis.db와 분리된 임시 DB에서 검증."""
from unittest.mock import MagicMock, patch
import pytest
from src.memory.database import (
    init_db,
    save_note,
    get_notes,
    delete_note,
    save_todo,
    get_todos,
    done_todo,
    clear_done_todos,
)
from src.tools.pdf_reader import extract_text, chunk_text
from src.agents.claude_ai import summarize_pdf
from src.tools.file_search import search_files

SAMPLE_PDF = "tests/fixtures/sample.pdf"


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """각 테스트마다 실제 jivis.db 대신 임시 DB 파일을 쓰도록 격리."""
    monkeypatch.setenv("JIVIS_DB_PATH", str(tmp_path / "test_jivis.db"))
    init_db()


def test_note_save_list_delete_roundtrip():
    save_note("운동", "30분 런닝", "2026-07-20")

    notes = get_notes()
    assert len(notes) == 1
    assert notes[0]["title"] == "운동"

    delete_note(notes[0]["id"])
    assert get_notes() == []


def test_todo_save_done_clear_roundtrip():
    save_todo("파이썬 공부", "2026-07-20")

    pending = get_todos(only_pending=True)
    assert len(pending) == 1

    done_todo(pending[0]["id"])
    assert get_todos(only_pending=True) == []

    cleared = clear_done_todos()
    assert cleared == 1


def test_pdf_extract_chunk_and_search_documents_pipeline(tmp_path):
    text = extract_text(SAMPLE_PDF)
    chunks = chunk_text(text)
    assert len(chunks) > 0

    (tmp_path / "sample.pdf").write_bytes(b"x")
    assert search_files("sample", base_dir=tmp_path) == [str(tmp_path / "sample.pdf")]


@patch("src.agents.claude_ai._client")
def test_pdf_summarize_uses_extracted_text(mock_client):
    response = MagicMock()
    response.content = [MagicMock(text="- 요약")]
    mock_client.messages.create.return_value = response

    text = extract_text(SAMPLE_PDF)
    chunks = chunk_text(text)
    result = summarize_pdf(chunks)

    assert result == "- 요약"
    sent_prompt = mock_client.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "Hello JIVIS" in sent_prompt
