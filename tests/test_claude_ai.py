from unittest.mock import MagicMock, patch
from src.agents.claude_ai import summarize_pdf, PDF_SUMMARY_CHAR_LIMIT, generate_fresh_greeting


def _mock_response(text: str) -> MagicMock:
    response = MagicMock()
    response.content = [MagicMock(text=text)]
    return response


@patch("src.agents.claude_ai._client")
def test_summarize_pdf_returns_claude_response(mock_client):
    mock_client.messages.create.return_value = _mock_response("- 요약 1\n- 요약 2")

    result = summarize_pdf(["첫 번째 청크입니다.", "두 번째 청크입니다."])

    assert result == "- 요약 1\n- 요약 2"


@patch("src.agents.claude_ai._client")
def test_summarize_pdf_sends_joined_chunks_in_prompt(mock_client):
    mock_client.messages.create.return_value = _mock_response("요약")

    summarize_pdf(["안녕하세요", "반갑습니다"])

    sent_prompt = mock_client.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "안녕하세요" in sent_prompt
    assert "반갑습니다" in sent_prompt


@patch("src.agents.claude_ai._client")
def test_summarize_pdf_truncates_over_char_limit(mock_client):
    mock_client.messages.create.return_value = _mock_response("요약")

    huge_chunk = "가" * (PDF_SUMMARY_CHAR_LIMIT + 5000)
    summarize_pdf([huge_chunk])

    sent_prompt = mock_client.messages.create.call_args.kwargs["messages"][0]["content"]
    assert len(sent_prompt) < len(huge_chunk) + 200  # 프롬프트 템플릿 여유분만 허용


@patch("src.agents.claude_ai._client")
def test_summarize_pdf_returns_friendly_message_on_error(mock_client):
    mock_client.messages.create.side_effect = Exception("boom")

    result = summarize_pdf(["청크"])

    assert "오류" in result


@patch("src.agents.claude_ai._client")
def test_generate_fresh_greeting_returns_claude_response(mock_client):
    mock_client.messages.create.return_value = _mock_response("안녕! 새로 시작이네")

    result = generate_fresh_greeting()

    assert result == "안녕! 새로 시작이네"


@patch("src.agents.claude_ai._client")
def test_generate_fresh_greeting_passes_system_persona(mock_client):
    mock_client.messages.create.return_value = _mock_response("안녕")

    generate_fresh_greeting(system="너는 JIVIS야")

    assert mock_client.messages.create.call_args.kwargs["system"] == "너는 JIVIS야"


@patch("src.agents.claude_ai._client")
def test_generate_fresh_greeting_returns_none_on_error(mock_client):
    mock_client.messages.create.side_effect = Exception("boom")

    assert generate_fresh_greeting() is None
