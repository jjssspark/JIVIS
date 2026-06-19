import re
import streamlit as st
from src.ui.chat import render_chat, Message
from src.agents.claude_ai import get_response, generate_greeting
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

# ── DB 초기화 ──────────────────────────────────────────────────
init_db()

# ── 앱 시작 시 설정 + 대화 기록 로드 ─────────────────────────
if "memory_loaded" not in st.session_state:
    saved = load()
    st.session_state["user_name"] = saved["user_name"]
    st.session_state["jivis_name"] = saved["jivis_name"]
    st.session_state["personality"] = saved.get("personality", "반말")
    st.session_state["memory_loaded"] = True

    last_msgs = load_recent_messages(limit=20)
    if last_msgs:
        st.session_state["messages"] = list(last_msgs)
        user = saved["user_name"]
        jivis = saved["jivis_name"]
        style = saved.get("personality", "반말")
        style_guide = {
            "반말": f"{user}와 친한 친구처럼 반말로 자연스럽게 대화해. 이모지 자제해.",
            "존댓말": f"'{user}님'이라고 부르며 친절하게 존댓말로 대화해. 이모지 자제해.",
            "자비스": f"'{user} 님'이라고 부르며 자비스처럼 격식 있고 품위 있게 모셔.",
        }.get(style, f"{user}와 반말로 대화해.")
        boot_system = f"너의 이름은 {jivis}야. {user}의 개인 AI 친구야.\n[말투]\n{style_guide}"
        greeting = generate_greeting(last_msgs, system=boot_system)
        if greeting:
            st.session_state.setdefault("messages", []).append(
                {"role": "assistant", "content": greeting}
            )

# ── 사이드바 ───────────────────────────────────────────────────
with st.sidebar:
    st.title("🤖 JIVIS")
    st.divider()

    long_mem = load_all_memory()
    if long_mem:
        label_map = {
            "goal": "목표",
            "hobby": "취미",
            "study_style": "공부 방식",
            "current_project": "현재 프로젝트",
        }
        st.caption("📌 기억하고 있어요")
        for k, v in long_mem.items():
            st.caption(f"• {label_map.get(k, k)}: {v}")
        st.divider()

    if st.button("대화 초기화"):
        st.session_state.messages = []
        clear_conversations()
        st.rerun()


# ── 시스템 프롬프트 ────────────────────────────────────────────
def _build_system(user_input: str = "") -> str:
    user = st.session_state["user_name"]
    jivis = st.session_state["jivis_name"]
    style = st.session_state["personality"]

    style_guide = {
        "반말": f"{user}와 친한 친구처럼 반말로 자연스럽게 대화해. 이름을 가끔 불러줘. 이모지 자제해.",
        "존댓말": f"'{user}님'이라고 부르며 친절하게 존댓말로 대화해. 이모지 자제해.",
        "자비스": f"'{user} 님'이라고 부르며 자비스처럼 격식 있고 품위 있게 모셔. 이모지 사용 금지.",
    }.get(style, f"{user}와 반말로 대화해.")

    # 장기 기억 주입
    long_mem = load_all_memory()
    memory_section = ""
    if long_mem:
        label_map = {
            "goal": "목표",
            "hobby": "취미",
            "study_style": "공부 방식",
            "current_project": "현재 프로젝트",
        }
        lines = "\n".join(f"- {label_map.get(k, k)}: {v}" for k, v in long_mem.items())
        memory_section = f"\n[기억하고 있는 사용자 정보]\n{lines}"

    # 감정 컨텍스트
    emotion_section = ""
    if user_input:
        ep = get_emotion_prompt(user_input)
        if ep:
            emotion_section = f"\n[현재 감정 상태]\n{ep}"

    return f"""너의 이름은 {jivis}야. {user}의 개인 AI 친구야.

[말투]
{style_guide}

[규칙]
- 자기소개나 인사로 시작하지 마. 바로 자연스럽게 반응해.
- 사용자가 이름을 알려주거나 정정하면, 그 이름으로 바로 불러줘.
- 말투 변경 요청이 오면 즉시 그 말투로 바꿔.
- 사용자의 목표, 취미, 공부 방식, 현재 프로젝트를 언급하면 기억해.
{memory_section}{emotion_section}

[메타 태그 규칙 - 중요]
응답 맨 끝에 해당하는 태그만 붙여. 사용자에게 안 보여.
- 이름 변경: [NAME:이름]
- 말투 변경: [STYLE:반말] 또는 [STYLE:존댓말] 또는 [STYLE:자비스]
- 새 사실 저장: [MEMORY:key:value]
  사용 가능한 key: goal / hobby / study_style / current_project
  예) [MEMORY:goal:백엔드 개발자] [MEMORY:hobby:독서]
- 해당 없으면 태그 생략.
"""


# ── 메타 태그 파싱 + 메모리 업데이트 ─────────────────────────
def _parse_and_update(response: str) -> str:
    updated = False

    name_match = re.search(r"\[NAME:([^\]]+)\]", response)
    if name_match:
        st.session_state["user_name"] = name_match.group(1).strip()
        updated = True

    style_match = re.search(r"\[STYLE:([^\]]+)\]", response)
    if style_match:
        st.session_state["personality"] = style_match.group(1).strip()
        updated = True

    if updated:
        save({
            "user_name": st.session_state["user_name"],
            "jivis_name": st.session_state["jivis_name"],
            "personality": st.session_state["personality"],
        })

    for mem_match in re.finditer(r"\[MEMORY:([^:\]]+):([^\]]+)\]", response):
        save_memory(mem_match.group(1).strip(), mem_match.group(2).strip())

    clean = re.sub(r"\s*\[NAME:[^\]]+\]", "", response)
    clean = re.sub(r"\s*\[STYLE:[^\]]+\]", "", clean)
    clean = re.sub(r"\s*\[MEMORY:[^\]]+\]", "", clean)
    return clean.strip()


# ── 대화 처리 ─────────────────────────────────────────────────
def responder(user_input: str, history: list[Message]) -> str:
    save_message("user", user_input)
    raw = get_response(user_input, history, system=_build_system(user_input))
    reply = _parse_and_update(raw)
    save_message("assistant", reply)
    return reply


# ── 메인 화면 ─────────────────────────────────────────────────
st.header(f"{st.session_state['jivis_name']}와 대화하기")
render_chat(responder)
