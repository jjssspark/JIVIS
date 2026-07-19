import time
import anthropic
from src.config import ANTHROPIC_API_KEY, MODEL_ID
from src.ui.chat import Message

_client = anthropic.Anthropic(
    api_key=ANTHROPIC_API_KEY,
    timeout=60.0,   # 60초 타임아웃
)

PDF_SUMMARY_CHAR_LIMIT = 12000  # 대형 PDF도 토큰 초과/타임아웃 없이 요약하기 위한 상한


def generate_greeting(
    last_messages: list[Message],
    system: str = "",
    elapsed: str = "",
    current_time: str = "",
) -> str:
    """이전 대화 맥락을 바탕으로 재접속 인사 생성."""
    history_text = "\n".join(
        f"{'나' if m['role'] == 'user' else 'JIVIS'}: {m['content']}"
        for m in last_messages[-6:]
    )
    time_info = ""
    if elapsed:
        time_info = f"\n- 마지막 대화로부터 {elapsed}이 지났어."
    if current_time:
        time_info += f"\n- 지금 시각은 {current_time}이야."

    prompt = f"""아래는 이전 대화의 마지막 부분이야:

{history_text}

사용자가 방금 다시 접속했어. 마치 잠깐 자리 비웠다가 돌아온 것처럼, 대화가 끊긴 적 없는 것처럼 자연스럽게 이어줘.
{time_info}

규칙:
- 인사말 절대 금지 ("안녕", "반갑", "어서와" 같은 거)
- 이전 대화 내용이나 분위기를 그대로 이어받아서 반응해
- 시간 정보가 있으면 자연스럽게 활용해. 예: 3시간 지났고 점심 시간대면 → "밥은 먹고 온 거야?"
- 예: 밥 먹으러 간다고 했으면 → "밥 맛있게 먹었어?"
- 예: 뭔가 고민하다 끊겼으면 → "근데 아까 그거 어떻게 됐어?"
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


def generate_fresh_greeting(system: str = "") -> str | None:
    """대화 초기화 직후, 이전 맥락 없이 JIVIS가 먼저 건네는 인사."""
    prompt = (
        "방금 사용자가 대화를 초기화했어. 이전 대화 기록은 없고 완전히 새로 시작하는 상황이야."
        " 짧게 인사하고 자연스럽게 말을 걸어줘. 한두 문장, 메타 태그 붙이지 마."
    )
    try:
        response = _client.messages.create(
            model=MODEL_ID,
            max_tokens=150,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    except Exception:
        return None


def summarize_pdf(chunks: list[str], persona: str = "") -> str:
    """PDF 텍스트 청크를 Claude에 전달해 3~5줄 요약을 생성한다."""
    text = "\n".join(chunks)[:PDF_SUMMARY_CHAR_LIMIT]
    prompt = f"""아래는 PDF에서 추출한 텍스트야:

{text}

이 내용을 핵심만 3~5줄로 요약해줘. 한 줄에 한 문장씩, 줄바꿈으로 구분해서 답해. 다른 설명 없이 요약만 답해."""

    try:
        response = _client.messages.create(
            model=MODEL_ID,
            max_tokens=500,
            system=persona,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    except anthropic.APITimeoutError:
        return "⚠️ 요약 중 응답 시간이 너무 걸렸어. 다시 시도해줘!"
    except Exception as e:
        return f"⚠️ 요약 중 오류가 발생했어요: {e}"


def get_response(user_input: str, history: list[Message], system: str = "") -> str:
    # 최근 10개만 전달 — 토큰 절약 + 타임아웃 방지
    messages = [{"role": m["role"], "content": m["content"]} for m in history[-10:]]
    messages.append({"role": "user", "content": user_input})

    for attempt in range(2):  # 최대 2회 시도
        try:
            response = _client.messages.create(
                model=MODEL_ID,
                max_tokens=1024,
                system=system,
                messages=messages,
            )
            return response.content[0].text
        except anthropic.APITimeoutError:
            if attempt == 0:
                time.sleep(2)
                continue
            return "⚠️ 응답 시간이 너무 걸렸어. 다시 말해줘!"
        except anthropic.AuthenticationError:
            return "⚠️ API 키가 올바르지 않아. .env 파일의 ANTHROPIC_API_KEY를 확인해줘."
        except anthropic.RateLimitError:
            return "⚠️ 요청이 너무 많아. 잠시 후 다시 해줘."
        except Exception as e:
            return f"⚠️ 오류가 발생했어요: {e}"
