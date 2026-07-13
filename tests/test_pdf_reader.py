from src.tools.pdf_reader import extract_text, chunk_text

SAMPLE_PDF = "tests/fixtures/sample.pdf"


def test_extract_text_reads_sample_pdf():
    text = extract_text(SAMPLE_PDF)
    assert "Hello JIVIS" in text


def test_chunk_text_splits_by_size():
    chunks = chunk_text("abcdef", size=2)
    assert chunks == ["ab", "cd", "ef"]


def test_chunk_text_default_size_1000():
    text = "a" * 2500
    chunks = chunk_text(text)
    assert len(chunks) == 3
    assert len(chunks[0]) == 1000
    assert len(chunks[-1]) == 500
