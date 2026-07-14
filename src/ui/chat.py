import streamlit as st
from typing import Callable

Message = dict[str, str]
ResponseHandler = Callable[[str, list[Message]], str]

_CSS = """
<style>
/* 전체 배경 카카오톡 색상 */
.stApp {
    background-color: #97B4C8 !important;
}
section[data-testid="stSidebar"] {
    background-color: #1e1e2e !important;
}
/* 사이드바 텍스트 — 다크 배경 위에서 안 보이던 문제 수정 */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: #f5f5f5 !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] svg,
section[data-testid="stSidebar"] [data-testid="collapsedControl"] svg {
    fill: #f5f5f5 !important;
}

/* 헤더 투명하게 */
header[data-testid="stHeader"] {
    background-color: transparent !important;
}

/* 말풍선 공통 */
.jivis-bubble {
    display: inline-block;
    padding: 10px 14px;
    border-radius: 4px 16px 16px 16px;
    background: #ffffff;
    color: #111111;
    font-size: 15px;
    line-height: 1.6;
    max-width: 100%;
    box-shadow: 0 1px 4px rgba(0,0,0,0.15);
    word-break: break-word;
    white-space: pre-wrap;
}
.user-bubble {
    display: inline-block;
    padding: 10px 14px;
    border-radius: 16px 4px 16px 16px;
    background: #FFEB00;
    color: #111111;
    font-size: 15px;
    line-height: 1.6;
    max-width: 100%;
    box-shadow: 0 1px 4px rgba(0,0,0,0.15);
    word-break: break-word;
    white-space: pre-wrap;
}
.sender-name {
    font-size: 12px;
    font-weight: 700;
    color: #2c2c2c;
    margin-bottom: 4px;
}
.avatar-box {
    width: 42px;
    height: 42px;
    border-radius: 13px;
    background: linear-gradient(135deg, #FFE500 60%, #FFC700 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    flex-shrink: 0;
    box-shadow: 0 2px 6px rgba(0,0,0,0.2);
}

/* Streamlit 컬럼 패딩 제거 */
div[data-testid="column"] > div {
    padding: 0 !important;
}

/* 입력창 */
div[data-testid="stChatInput"] {
    background-color: #ffffff !important;
    border-radius: 24px !important;
}
</style>
"""


def _init_session() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages: list[Message] = []


def _render_message(msg: Message, jivis_name: str) -> None:
    content = (
        msg["content"]
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

    if msg["role"] == "assistant":
        # 왼쪽: 아바타 | 이름 + 말풍선
        col_avatar, col_bubble, col_empty = st.columns([0.08, 0.55, 0.37])
        with col_avatar:
            st.markdown(
                '<div class="avatar-box">🤖</div>',
                unsafe_allow_html=True,
            )
        with col_bubble:
            st.markdown(
                f'<div class="sender-name">{jivis_name}</div>'
                f'<div class="jivis-bubble">{content}</div>',
                unsafe_allow_html=True,
            )
    else:
        # 오른쪽: 빈공간 | 말풍선
        col_empty, col_bubble = st.columns([0.37, 0.63])
        with col_bubble:
            st.markdown(
                f'<div style="text-align:right">'
                f'<div class="user-bubble" style="text-align:left">{content}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )

    # 메시지 간 여백
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)


def _render_history() -> None:
    jivis_name = st.session_state.get("jivis_name", "JIVIS")

    # 채팅창 컨테이너
    st.markdown(
        "<div style='padding: 16px 8px; min-height: 400px;'>",
        unsafe_allow_html=True,
    )
    for msg in st.session_state.messages:
        _render_message(msg, jivis_name)
    st.markdown("</div>", unsafe_allow_html=True)


def render_chat(on_message: ResponseHandler) -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    _init_session()
    _render_history()

    if prompt := st.chat_input("메시지를 입력하세요..."):
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.spinner(""):
            response = on_message(prompt, st.session_state.messages[:-1])

        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()
