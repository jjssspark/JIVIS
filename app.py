import re
import streamlit as st
from src.ui.chat import render_chat, Message
from src.agents.claude_ai import get_response, generate_greeting
from src.memory.memory import load, save, save_history, load_history

st.set_page_config(page_title="JIVIS", page_icon="🤖", layout="wide")

# ── 앱 시작 시 memory.json에서 설정 불러오기 ──────────────
if "memory_loaded" not in st.session_state:
    saved = load()
    st.session_state["user_name"] = saved["user_name"]
    st.session_state["jivis_name"] = saved["jivis_name"]
    st.session_state["personality"] = saved.get("personality", "반말")
    st.session_state["memory_loaded"] = True

    # 이전 대화 히스토리가 있으면 재접속 인사 생성
    last_msgs = load_history()
    if last_msgs:
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
            st.session_state["messages"] = [{"role": "assistant", "content": greeting}]

# ── 사이드바: 초기화 버튼만 ────────────────────────────
with st.sidebar:
    st.title("🤖 JIVIS")
    st.divider()
    if st.button("대화 초기화"):
        st.session_state.messages = []
        save_history([])  # 이전 대화 기록도 초기화
        st.rerun()


# ── 시스템 프롬프트 ────────────────────────────────────────
def _build_system() -> str:
    user = st.session_state["user_name"]
    jivis = st.session_state["jivis_name"]
    style = st.session_state["personality"]

    style_guide = {
        "반말": f"{user}와 친한 친구처럼 반말로 자연스럽게 대화해. 이름을 가끔 불러줘. 이모지 자제해.",
        "존댓말": f"'{user}님'이라고 부르며 친절하게 존댓말로 대화해. 이모지 자제해.",
        "자비스": f"'{user} 님'이라고 부르며 자비스처럼 격식 있고 품위 있게 모셔. 이모지 사용 금지.",
    }.get(style, f"{user}와 반말로 대화해.")

    return f"""너의 이름은 {jivis}야. {user}의 개인 AI 친구야.

[말투]
{style_guide}

[규칙]
- 자기소개나 인사로 시작하지 마. 바로 자연스럽게 반응해.
- 사용자가 이름을 알려주거나 정정하면, 그 이름으로 바로 불러줘.
- 말투 변경 요청이 오면 즉시 그 말투로 바꿔.

[현재 알고 있는 사용자 정보]
- 이름: {user}

[메타 태그 규칙 - 매우 중요]
응답 맨 끝에 아래 태그를 붙여. 사용자가 볼 수 없으니 솔직하게 채워.
- 사용자가 자신의 이름을 알려줬거나 정정했으면: [NAME:실제이름]
- 말투 변경을 요청했으면: [STYLE:반말] 또는 [STYLE:존댓말] 또는 [STYLE:자비스]
- 해당 없으면 태그 생략.

예시) "아 미안, 이제부터 최주연이라고 부를게! [NAME:최주연]"
"""


# ── AI 응답에서 태그 파싱 후 메모리 업데이트 ──────────────
def _parse_and_update(response: str) -> str:
    """응답에서 [NAME:xxx], [STYLE:xxx] 태그를 파싱하고 제거해서 반환."""
    updated = False

    name_match = re.search(r"\[NAME:([^\]]+)\]", response)
    if name_match:
        new_name = name_match.group(1).strip()
        st.session_state["user_name"] = new_name
        updated = True

    style_match = re.search(r"\[STYLE:([^\]]+)\]", response)
    if style_match:
        new_style = style_match.group(1).strip()
        st.session_state["personality"] = new_style
        updated = True

    if updated:
        save({
            "user_name": st.session_state["user_name"],
            "jivis_name": st.session_state["jivis_name"],
            "personality": st.session_state["personality"],
        })

    # 태그 제거 후 반환
    clean = re.sub(r"\s*\[NAME:[^\]]+\]", "", response)
    clean = re.sub(r"\s*\[STYLE:[^\]]+\]", "", clean)
    return clean.strip()


# ── 대화 처리 ─────────────────────────────────────────────
def responder(user_input: str, history: list[Message]) -> str:
    raw = get_response(user_input, history, system=_build_system())
    reply = _parse_and_update(raw)

    # 대화 내역 memory에 저장 (다음 접속 시 이어받기용)
    updated_history = list(history) + [
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": reply},
    ]
    save_history(updated_history)

    return reply


# ── 메인 화면 ─────────────────────────────────────────────
st.header(f"{st.session_state['jivis_name']}와 대화하기")
render_chat(responder)
