"""JIVIS 할 일 관리 앱 — jivis.db와 직접 연동"""
import streamlit as st
from src.memory.database import init_db, get_todos, save_todo, done_todo, delete_todo

st.set_page_config(page_title="JIVIS 할 일", page_icon="✅", layout="centered")
init_db()

st.title("✅ JIVIS 할 일")
st.divider()

# ── 새 할 일 추가 ───────────────────────────────────────────
with st.form("add_todo", clear_on_submit=True):
    col1, col2, col3 = st.columns([3, 1.5, 1])
    with col1:
        new_task = st.text_input("할 일", placeholder="오늘 할 일을 입력해...")
    with col2:
        due_date = st.date_input("날짜 (선택)", value=None)
    with col3:
        st.write("")
        st.write("")
        submitted = st.form_submit_button("추가 ➕", use_container_width=True)

    if submitted and new_task.strip():
        save_todo(new_task.strip(), str(due_date) if due_date else None)
        st.rerun()

st.divider()

# ── 할 일 목록 ──────────────────────────────────────────────
todos = get_todos(only_pending=False)
pending = [t for t in todos if not t["done"]]
done_list = [t for t in todos if t["done"]]

if not todos:
    st.info("할 일이 없어~ 여유 있는 하루 보내!")
else:
    # 미완료
    if pending:
        st.subheader(f"📋 할 일 ({len(pending)}개)")
        for t in pending:
            col1, col2, col3 = st.columns([0.08, 0.72, 0.2])
            with col1:
                if st.checkbox("", key=f"done_{t['id']}"):
                    done_todo(t["id"])
                    st.rerun()
            with col2:
                date_str = f"  `📅 {t['due_date']}`" if t.get("due_date") else ""
                st.markdown(f"**{t['task']}**{date_str}")
            with col3:
                if st.button("🗑️", key=f"del_{t['id']}", help="삭제"):
                    delete_todo(t["id"])
                    st.rerun()

    # 완료된 항목
    if done_list:
        with st.expander(f"✅ 완료된 항목 ({len(done_list)}개)"):
            for t in done_list:
                col1, col2 = st.columns([0.8, 0.2])
                with col1:
                    date_str = f"  `📅 {t['due_date']}`" if t.get("due_date") else ""
                    st.markdown(f"~~{t['task']}~~{date_str}")
                with col2:
                    if st.button("🗑️", key=f"del_done_{t['id']}", help="삭제"):
                        delete_todo(t["id"])
                        st.rerun()

# ── 하단 새로고침 ────────────────────────────────────────────
st.divider()
if st.button("🔄 새로고침"):
    st.rerun()
