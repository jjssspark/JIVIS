import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, InvalidArgument
from src.config import GEMINI_API_KEY, MODEL_ID
from src.ui.chat import Message

genai.configure(api_key=GEMINI_API_KEY)


def get_response(user_input: str, history: list[Message]) -> str:
    """
    Gemini API를 호출해서 응답을 반환한다.
    history: 이전 대화 기록 (user_input 직전까지)
    """
    # Streamlit Message 형식 → Gemini 형식으로 변환
    # Gemini는 "assistant" 대신 "model"을 사용함
    gemini_history = []
    for msg in history:
        role = "model" if msg["role"] == "assistant" else "user"
        gemini_history.append({"role": role, "parts": [msg["content"]]})

    try:
        model = genai.GenerativeModel(MODEL_ID)
        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(user_input)
        return response.text
    except ResourceExhausted:
        return "⚠️ API 요청 한도를 초과했어요. 잠시 후 다시 시도해주세요."
    except InvalidArgument:
        return "⚠️ API 키가 올바르지 않아요. .env 파일의 GEMINI_API_KEY를 확인해주세요."
    except Exception as e:
        return f"⚠️ 오류가 발생했어요: {e}"
