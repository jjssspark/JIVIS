import re
import subprocess
import sys
from datetime import datetime
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
    load_last_message_time,
    clear_conversations,
    save_note,
    get_notes,
    delete_note,
    save_todo,
    get_todos,
    done_todo,
    delete_todo,
)
from src.tools.mac_notes import (
    create_note as mac_create,
    update_note as mac_update,
    delete_note_by_title as mac_delete,
)
from src.tools.date_utils import get_date_context
from src.memory.emotion import get_emotion_prompt

st.set_page_config(page_title="JIVIS", page_icon="🤖", layout="wide")
init_db()

_LABEL_MAP = {
    "goal": "목표",
    "hobby": "취미",
    "study_style": "공부 방식",
    "current_project": "현재 프로젝트",
}


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

    now = datetime.now()
    hour = now.hour
    if 5 <= hour < 12:
        period = "오전"
    elif 12 <= hour < 14:
        period = "점심 시간대"
    elif 14 <= hour < 18:
        period = "오후"
    elif 18 <= hour < 22:
        period = "저녁"
    else:
        period = "밤"
    weekdays = ["월", "화", "수", "목", "금", "토", "일"]
    weekday = weekdays[now.weekday()]
    time_section = (
        f"\n[현재 날짜/시간]\n"
        f"오늘은 {now.strftime('%Y년 %m월 %d일')} ({weekday}요일), "
        f"지금은 {now.strftime('%H:%M')} ({period})이야. "
        f"대화 흐름상 자연스러우면 날짜/시간대를 반영해도 돼."
    )

    return f"""너의 이름은 {jivis}야. {user}의 개인 AI야.

{persona_text}
{time_section}

[규칙]
- 자기소개나 인사로 시작하지 마. 바로 자연스럽게 반응해.
- 사용자가 이름을 알려주거나 정정하면, 그 이름으로 바로 불러줘.
- 사용자의 목표, 취미, 공부 방식, 현재 프로젝트를 언급하면 기억해.
{memory_section}{emotion_section}

[메타 태그 규칙 - 중요]
응답 맨 끝에 해당하는 태그만 붙여. 사용자에게 안 보여.
- 이름 변경: [NAME:이름]
- 모드 자동 전환: [MODE:친구] 또는 [MODE:공부코치] 또는 [MODE:프로젝트멘토]
  사용자가 공부/학습 얘기를 하면 [MODE:공부코치], 개발/프로젝트 얘기를 하면 [MODE:프로젝트멘토],
  일상 대화면 [MODE:친구]. 현재 모드({mode})와 다를 때만 붙여.
- 새 사실 저장: [MEMORY:key:value]
  사용 가능한 key: goal / hobby / study_style / current_project
  예) [MEMORY:goal:백엔드 개발자] [MEMORY:hobby:독서]
- 메모 저장: [NOTE:제목:내용:날짜] (날짜 없으면 [NOTE:제목:내용])
  "메모해줘", "기억해줘", "적어줘" 감지 시 붙여.
  날짜 표현(내일, 다음주 등)이 있으면 아래 날짜 레퍼런스 보고 YYYY-MM-DD로 변환해서 붙여.
  예) [NOTE:운동:내일 30분 런닝:2026-07-09]
- 메모 수정: [NOTE_UPDATE:제목:새내용]
  사용자가 기존 메모를 수정하고 싶다고 하면 붙여.
  예) [NOTE_UPDATE:운동:내일 1시간 런닝]
- 할 일 추가: [TODO:내용:날짜] (날짜 없으면 [TODO:내용])
  "해야 해", "할 일 추가해줘", "~하기로 했어" 감지 시 붙여.
  날짜 표현이 있으면 YYYY-MM-DD로 변환해서 붙여.
  예) [TODO:파이썬 공부 2시간:2026-07-09]
- 할 일 완료: [DONE:id]
  "완료했어", "다 했어", "끝냈어" 감지 시 해당 id 붙여.
  예) [DONE:1]
- 해당 없으면 태그 생략.

[날짜 레퍼런스]
{get_date_context()}
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

    mode_match = re.search(r"\[MODE:([^\]]+)\]", response)
    if mode_match:
        new_mode = mode_match.group(1).strip()
        if new_mode in ("친구", "공부코치", "프로젝트멘토"):
            st.session_state["mode"] = new_mode

    for mem_match in re.finditer(r"\[MEMORY:([^:\]]+):([^\]]+)\]", response):
        save_memory(mem_match.group(1).strip(), mem_match.group(2).strip())

    for note_match in re.finditer(r"\[NOTE:([^:\]]+):([^:\]]+)(?::([^\]]+))?\]", response):
        title    = note_match.group(1).strip()
        body     = note_match.group(2).strip()
        date_ref = note_match.group(3).strip() if note_match.group(3) else None
        save_note(title, body, date_ref)
        label = f"{title}" + (f" ({date_ref})" if date_ref else "")
        mac_create(label, body)  # macOS 메모앱에도 생성 + 열기

    for upd_match in re.finditer(r"\[NOTE_UPDATE:([^:\]]+):([^\]]+)\]", response):
        title = upd_match.group(1).strip()
        new_body = upd_match.group(2).strip()
        mac_update(title, new_body)  # 메모앱에서 수정 + 열기

    for todo_match in re.finditer(r"\[TODO:([^:\]]+)(?::([^\]]+))?\]", response):
        task     = todo_match.group(1).strip()
        due_date = todo_match.group(2).strip() if todo_match.group(2) else None
        save_todo(task, due_date)

    for done_match in re.finditer(r"\[DONE:(\d+)\]", response):
        done_todo(int(done_match.group(1)))

    clean = re.sub(r"\s*\[NAME:[^\]]+\]", "", response)
    clean = re.sub(r"\s*\[MODE:[^\]]+\]", "", clean)
    clean = re.sub(r"\s*\[MEMORY:[^\]]+\]", "", clean)
    clean = re.sub(r"\s*\[NOTE:[^\]]+\]", "", clean)
    clean = re.sub(r"\s*\[NOTE_UPDATE:[^\]]+\]", "", clean)
    clean = re.sub(r"\s*\[TODO:[^\]]+\]", "", clean)
    clean = re.sub(r"\s*\[DONE:[^\]]+\]", "", clean)
    return clean.strip()


# ── 메모 조회/삭제 처리 ───────────────────────────────────────
def _handle_note_command(user_input: str) -> str | None:
    """'메모 보여줘' / '메모 삭제' 같은 명령을 감지해서 직접 처리. 해당 없으면 None."""
    text = user_input.strip()

    # 메모 조회
    if any(k in text for k in ("메모 보여", "메모 알려", "메모 목록", "메모 뭐 있어", "메모 뭐있어")):
        notes = get_notes()
        if not notes:
            return "아직 저장된 메모가 없어~"
        lines = []
        for n in notes:
            date_str = f" 📅{n['date_ref']}" if n.get("date_ref") else ""
            lines.append(f"{n['id']}. [{n['title']}]{date_str} {n['content']}")
        return "저장된 메모야:\n" + "\n".join(lines)

    # 메모 삭제 — "메모 삭제", "메모 지워줘" + 선택적 제목/id
    if any(k in text for k in ("메모 삭제", "메모 지워", "메모 없애")):
        notes = get_notes()
        if not notes:
            return "삭제할 메모가 없어!"

        target = None

        # id 숫자 명시 ex) "1번 메모 지워"
        id_match = re.search(r"(\d+)\s*번", text)
        if id_match:
            note_id = int(id_match.group(1))
            target = next((n for n in notes if n["id"] == note_id), None)
        else:
            # 제목 키워드로 찾기
            for note in notes:
                if note["title"] in text or note["content"][:10] in text:
                    target = note
                    break
            # 마지막 메모 삭제
            if not target:
                target = notes[0]

        delete_note(target["id"])
        mac_delete(target["title"])  # macOS 메모앱에서도 삭제
        return f"[{target['title']}] 메모 삭제했어! 메모앱에서도 지웠어."

    return None


# ── 할 일 조회/완료/삭제 처리 ────────────────────────────────
def _handle_todo_command(user_input: str) -> str | None:
    text = user_input.strip()

    # 할 일 조회 → 네이티브 창 열기
    if any(k in text for k in ("할 일 보여", "할 일 목록", "할 일 뭐야", "할 일 알려", "해야 할 거", "투두")):
        # 네이티브 할 일 창 실행 (백그라운드)
        todo_script = str(__import__("pathlib").Path(__file__).parent / "todo_window.py")
        subprocess.Popen([sys.executable, todo_script])
        todos = get_todos(only_pending=True)
        if not todos:
            return "할 일 창 열었어~ 지금 할 일 목록은 비어 있어 ㅎ"
        lines = []
        for t in todos:
            date_str = f" 📅{t['due_date']}" if t.get("due_date") else ""
            lines.append(f"{t['id']}.{date_str} {t['task']}")
        return "할 일 창 열었어!\n" + "\n".join(lines)

    # 완료 처리 — "1번 완료", "첫 번째 다 했어"
    if any(k in text for k in ("완료", "다 했어", "끝냈어", "했어")):
        id_match = re.search(r"(\d+)\s*번", text)
        if id_match:
            done_todo(int(id_match.group(1)))
            return f"{id_match.group(1)}번 할 일 완료 처리했어! 👍"
        # 번호 없으면 가장 오래된 미완료 항목 완료
        todos = get_todos(only_pending=True)
        if todos:
            done_todo(todos[0]["id"])
            return f"[{todos[0]['task']}] 완료했어! 고생했다 ㅎㅎ"

    # 삭제
    if any(k in text for k in ("할 일 삭제", "할 일 지워", "투두 삭제", "투두 지워")):
        id_match = re.search(r"(\d+)\s*번", text)
        todos = get_todos(only_pending=False)
        if not todos:
            return "삭제할 할 일이 없어!"
        if id_match:
            todo_id = int(id_match.group(1))
            target = next((t for t in todos if t["id"] == todo_id), None)
        else:
            target = todos[0]
        if target:
            delete_todo(target["id"])
            return f"[{target['task']}] 할 일 삭제했어."

    return None


# ── 대화 처리 ─────────────────────────────────────────────────
def responder(user_input: str, history: list[Message]) -> str:
    save_message("user", user_input)

    # 메모 명령어 우선 처리
    note_reply = _handle_note_command(user_input)
    if note_reply:
        save_message("assistant", note_reply)
        return note_reply

    # 할 일 명령어 처리
    todo_reply = _handle_todo_command(user_input)
    if todo_reply:
        save_message("assistant", todo_reply)
        return todo_reply

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

        elapsed_str = ""
        last_ts = load_last_message_time()
        if last_ts:
            try:
                last_dt = datetime.strptime(last_ts, "%Y-%m-%d %H:%M:%S")
                diff = datetime.now() - last_dt
                total_min = int(diff.total_seconds() / 60)
                if total_min < 1:
                    elapsed_str = ""
                elif total_min < 60:
                    elapsed_str = f"{total_min}분"
                else:
                    h, m = divmod(total_min, 60)
                    elapsed_str = f"{h}시간" if m == 0 else f"{h}시간 {m}분"
            except ValueError:
                pass

        now = datetime.now()
        greeting = generate_greeting(
            last_msgs,
            system=_build_system(),
            elapsed=elapsed_str,
            current_time=now.strftime("%H:%M"),
        )
        if greeting:
            st.session_state["messages"].append(
                {"role": "assistant", "content": greeting}
            )

# ── 사이드바 ───────────────────────────────────────────────────
with st.sidebar:
    st.title("🤖 JIVIS")
    st.divider()

    if st.button("대화 초기화"):
        st.session_state.messages = []
        clear_conversations()
        st.rerun()


# ── 메인 화면 ─────────────────────────────────────────────────
st.header(f"{st.session_state['jivis_name']}와 대화하기")
render_chat(responder)
