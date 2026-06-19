import anthropic
from src.config import ANTHROPIC_API_KEY, MODEL_ID
from src.ui.chat import Message

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def generate_greeting(last_messages: list[Message], system: str = "") -> str:
    """이전 대화 맥락을 바탕으로 재접속 인사 생성."""
    history_text = "\n".join(
        f"{'나' if m['role'] == 'user' else 'JIVIS'}: {m['content']}"
        for m in last_messages[-6:]
    )
    prompt = f"""아래는 이전 대화의 마지막 부분이야:

{history_text}

사용자가 방금 다시 접속했어. 마치 잠깐 자리 비웠다가 돌아온 것처럼, 대화가 끊긴 적 없는 것처럼 자연스럽게 이어줘.

규칙:
- 인사말 절대 금지 ("안녕", "반갑", "어서와" 같은 거)
- 이전 대화 내용이나 분위기를 그대로 이어받아서 반응해
- 예: 밥 먹으러 간다고 했으면 → "밥 맛있게 먹었어?"
- 예: 뭔가 고민하다 끊겼으면 → "근데 아까 그거 어떻게 됐어?"
- 예: 게임 얘기 하다 끊겼으면 → "아까 거기서 이긴 거야 결국?"
- 한두 문장, 그 어투 그대로. 메타 태그 붙이지 마."""

    try:
        response = _client.messages.create(
            model=MODEL_ID,
            max_tokens=200,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    except Exception:
        return None


def get_response(user_input: str, history: list[Message], system: str = "") -> str:
    messages = [{"role": msg["role"], "content": msg["content"]} for msg in history]
    messages.append({"role": "user", "content": user_input})

    try:
        response = _client.messages.create(
            model=MODEL_ID,
            max_tokens=1024,
            system=system,
            messages=messages,
        )
        return response.content[0].text
    except anthropic.AuthenticationError:
        return "⚠️ API 키가 올바르지 않아요. .env 파일의 ANTHROPIC_API_KEY를 확인해주세요."
    except anthropic.RateLimitError:
        return "⚠️ 요청이 너무 많아요. 잠시 후 다시 시도해주세요."
    except Exception as e:
        return f"⚠️ 오류가 발생했어요: {e}"
