import re
import streamlit as st
from src.ui.chat import render_chat, Message
from src.agents.claude_ai import get_response, generate_greeting
from src.agents.persona import get_persona_prompt
from src.memory.memory import load, save
from src.memory.database import (
    init_db,
    save_memory,
    load_all_memory,
    save_message,
    load_recent_messages,
    clear_conversations,
)
from src.memory.emotion import get_emotion_prompt

st.set_page_config(page_title="JIVIS", page_icon="🤖", layout="wide")
init_db()

_LABEL_MAP = {
    "goal": "목표",
    "hobby": "취미",
    "study_style": "공부 방식",
    "current_project": "현재 프로젝트",
}
_MODE_ICONS = {"친구": "👫", "공부코치": "📚", "프로젝트멘토": "💻"}


# ── 시스템 프롬프트 ────────────────────────────────────────────
def _build_system(user_input: str = "") -> str:
    user = st.session_state["user_name"]
    jivis = st.session_state["jivis_name"]
    mode = st.session_state.get("mode", "친구")

    persona_text = get_persona_prompt(mode, user)

    long_mem = load_all_memory()
    user_facts = {k: v for k, v in long_mem.items() if k in _LABEL_MAP}
    memory_section = ""
    if user_facts:
        lines = "\n".join(f"- {_LABEL_MAP[k]}: {v}" for k, v in user_facts.items())
        memory_section = f"\n[사용자 정보]\n{lines}"

    emotion_section = ""
    if user_input:
        ep = get_emotion_prompt(user_input)
        if ep:
            emotion_section = f"\n[현재 감정 상태]\n{ep}"

    return f"""너의 이름은 {jivis}야. {user}의 개인 AI야.

{persona_text}

[규칙]
- 자기소개나 인사로 시작하지 마. 바로 자연스럽게 반응해.
- 사용자가 이름을 알려주거나 정정하면, 그 이름으로 바로 불러줘.
- 사용자의 목표, 취미, 공부 방식, 현재 프로젝트를 언급하면 기억해.
{memory_section}{emotion_section}

[메타 태그 규칙 - 중요]
응답 맨 끝에 해당하는 태그만 붙여. 사용자에게 안 보여.
- 이름 변경: [NAME:이름]
- 새 사실 저장: [MEMORY:key:value]
  사용 가능한 key: goal / hobby / study_style / current_project
  예) [MEMORY:goal:백엔드 개발자] [MEMORY:hobby:독서]
- 해당 없으면 태그 생략.
"""


# ── 메타 태그 파싱 + 메모리 업데이트 ─────────────────────────
def _parse_and_update(response: str) -> str:
    name_match = re.search(r"\[NAME:([^\]]+)\]", response)
    if name_match:
        st.session_state["user_name"] = name_match.group(1).strip()
        save({
            "user_name": st.session_state["user_name"],
            "jivis_name": st.session_state["jivis_name"],
        })

    for mem_match in re.finditer(r"\[MEMORY:([^:\]]+):([^\]]+)\]", response):
        save_memory(mem_match.group(1).strip(), mem_match.group(2).strip())

    clean = re.sub(r"\s*\[NAME:[^\]]+\]", "", response)
    clean = re.sub(r"\s*\[MEMORY:[^\]]+\]", "", clean)
    return clean.strip()


# ── 대화 처리 ─────────────────────────────────────────────────
def responder(user_input: str, history: list[Message]) -> str:
    save_message("user", user_input)
    raw = get_response(user_input, history, system=_build_system(user_input))
    reply = _parse_and_update(raw)
    save_message("assistant", reply)
    return reply


# ── 앱 시작 시 설정 + 대화 기록 로드 ─────────────────────────
if "memory_loaded" not in st.session_state:
    saved = load()
    st.session_state["user_name"] = saved["user_name"]
    st.session_state["jivis_name"] = saved["jivis_name"]
    st.session_state.setdefault("mode", "친구")
    st.session_state["memory_loaded"] = True

    last_msgs = load_recent_messages(limit=20)
    if last_msgs:
        st.session_state["messages"] = list(last_msgs)
        greeting = generate_greeting(last_msgs, system=_build_system())
        if greeting:
            st.session_state["messages"].append(
                {"role": "assistant", "content": greeting}
            )

# ── 사이드바 ───────────────────────────────────────────────────
with st.sidebar:
    st.title("🤖 JIVIS")
    st.divider()

    selected_mode = st.radio(
        "JIVIS 모드",
        ["친구", "공부코치", "프로젝트멘토"],
        key="mode",
    )
    st.caption(f"{_MODE_ICONS[selected_mode]} 현재 모드: {selected_mode}")
    st.divider()

    long_mem = load_all_memory()
    user_facts = {k: v for k, v in long_mem.items() if k in _LABEL_MAP}
    if user_facts:
        st.caption("📌 기억하고 있어요")
        for k, v in user_facts.items():
            st.caption(f"• {_LABEL_MAP[k]}: {v}")
        st.divider()

    if st.button("대화 초기화"):
        st.session_state.messages = []
        clear_conversations()
        st.rerun()


# ── 메인 화면 ─────────────────────────────────────────────────
st.header(f"{st.session_state['jivis_name']}와 대화하기")
render_chat(responder)
