import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
import streamlit as st
from src.ui.chat import render_chat, Message
from src.agents.claude_ai import get_response, generate_greeting, generate_fresh_greeting, summarize_pdf
from src.agents.persona import get_persona_prompt
from src.memory.memory import load, save
from src.tools.pdf_reader import extract_text, chunk_text
from src.tools.file_search import search_files
from src.memory.database import (
    init_db,
    save_memory,
    load_all_memory,
    save_message,
    load_recent_messages,
    load_last_message_time,
    search_messages,
    clear_conversations,
    save_note,
    get_notes,
    delete_note,
    save_todo,
    get_todos,
    done_todo,
    delete_todo,
    clear_done_todos,
    get_overdue_todos,
    get_today_todos,
)
from src.tools.mac_notes import (
    create_note as mac_create,
    update_note as mac_update,
    delete_note_by_title as mac_delete,
)
from src.tools.date_utils import get_date_context, format_elapsed
from src.memory.emotion import get_emotion_prompt

st.set_page_config(page_title="JIVIS", page_icon="🤖", layout="wide")
init_db()

_PDF_QA_CHAR_LIMIT = 8000  # 시스템 프롬프트에 주입할 PDF 내용 상한 (토큰 절약)

_LABEL_MAP = {
    "goal": "목표",
    "hobby": "취미",
    "study_style": "공부 방식",
    "current_project": "현재 프로젝트",
}


# ── 시스템 프롬프트 ────────────────────────────────────────────
def _build_system(user_input: str = "", elapsed: str = "") -> str:
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

    pdf_section = ""
    if st.session_state.get("pdf_filename"):
        pdf_name = st.session_state["pdf_filename"]
        pdf_chunks = st.session_state.get("pdf_context") or []
        chunk_count = len(pdf_chunks)
        if chunk_count > 0:
            preview = "\n".join(pdf_chunks)[:_PDF_QA_CHAR_LIMIT]
            pdf_section = (
                f"\n[현재 PDF 내용 — '{pdf_name}'에서 추출한 텍스트]\n{preview}\n"
                "위 내용은 사용자가 업로드한 PDF에서 실제로 추출한 텍스트야."
                " 사용자가 이 PDF 내용에 대해 질문하면 위 텍스트를 근거로 답해."
            )
        else:
            pdf_section = (
                f"\n[현재 PDF 보고 있어]\n"
                f"사용자가 '{pdf_name}' 파일을 업로드했고 시스템이 파일 자체는 받았는데,"
                " 텍스트 추출에 실패했어(스캔 이미지 PDF이거나 글자가 그림으로 되어 있을 가능성이 커)."
                " '파일을 못 받았다'고 말하지 말고, '파일은 받았는데 텍스트 추출이 안 됐다,"
                " 스캔본이면 이미지라서 글자를 못 읽는다'고 정확히 설명해."
            )

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
    elapsed_note = f" 마지막 대화로부터 {elapsed}이 지났어." if elapsed else ""
    time_section = (
        f"\n[현재 날짜/시간]\n"
        f"오늘은 {now.strftime('%Y년 %m월 %d일')} ({weekday}요일), "
        f"지금은 {now.strftime('%H:%M')} ({period})이야.{elapsed_note} "
        f"대화 흐름상 자연스러우면 날짜/시간대를 반영해도 돼. "
        f"경과 시간을 물어보면 위 정보를 근거로 정확히 답해 — 모른다고 하지 마."
    )

    # 할 일 컨텍스트 (전체 미완료 목록 + 기한 초과)
    todo_section = ""
    all_pending = get_todos(only_pending=True)
    overdue = get_overdue_todos()
    if all_pending:
        items = "\n".join(f"- [id:{t['id']}] {t['task']}" + (f" (마감:{t['due_date']})" if t.get("due_date") else "") for t in all_pending)
        todo_section += f"\n[현재 저장된 미완료 할 일 — 절대 [TODO:] 태그로 다시 추가하지 마]\n{items}"
    if overdue:
        items = ", ".join(f"{t['task']}({t['due_date']})" for t in overdue)
        todo_section += f"\n[기한 초과 할 일 ⚠️]\n{items}"
    if todo_section:
        todo_section += "\n대화 흐름상 자연스러우면 할 일을 가볍게 언급해도 돼. 단, 이미 있는 항목은 절대 [TODO:]로 재추가 금지."

    # 공부 플래너 섹션
    study_section = ""
    study_keys = {k: long_mem[k] for k in ("goal", "study_style", "current_project") if k in long_mem}
    if study_keys:
        lines = []
        if "goal" in study_keys:
            lines.append(f"- 목표: {study_keys['goal']}")
        if "study_style" in study_keys:
            lines.append(f"- 공부 방식: {study_keys['study_style']}")
        if "current_project" in study_keys:
            lines.append(f"- 현재 프로젝트: {study_keys['current_project']}")
        study_section = (
            "\n[공부 플래너]\n"
            + "\n".join(lines)
            + "\n사용자가 '오늘 뭐 공부해?', '공부 추천', '뭐 할까?' 등을 물으면"
            " 위 정보 기반으로 오늘 할 구체적인 학습 항목 2~3개를 추천해."
            " 추천 후 '할 일에 추가할까?' 라고 물어봐."
            " 사용자가 원하면 [TODO:학습내용:오늘날짜] 태그로 추가해."
        )

    return f"""너의 이름은 {jivis}야. {user}의 개인 AI야.

{persona_text}
{time_section}

[규칙]
- 자기소개나 인사로 시작하지 마. 바로 자연스럽게 반응해.
- 사용자가 이름을 알려주거나 정정하면, 그 이름으로 바로 불러줘.
- 사용자의 목표, 취미, 공부 방식, 현재 프로젝트를 언급하면 기억해.
{memory_section}{emotion_section}{pdf_section}{todo_section}{study_section}

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
  주의: 이 태그를 실제로 붙여야만 진짜 저장됨 — "추가했어"라고 말만 하고 태그를 빠뜨리면
  아무 일도 안 일어나니 절대 태그 없이 "추가했어"라고 답하지 마.
  날짜를 물어봤는데 사용자가 "오늘로", "응", "어" 같은 짧은 대답으로 확인해주면,
  직전에 물어본 그 할 일 내용에 오늘 날짜를 붙여 바로 [TODO:] 태그를 완성해 —
  다시 되묻지 말고 그 자리에서 확정해.
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


# ── 대화 시간 조회 처리 ───────────────────────────────────────
def _handle_time_lookup_command(user_input: str) -> str | None:
    """'마지막 대화 언제야?' / 'OO 얘기 언제 했어?' 같은 시간 조회 질문을 직접 처리. 해당 없으면 None."""
    text = user_input.strip()
    if "언제" not in text:
        return None

    # "마지막 대화/메시지가 언제야?"
    if re.search(r"마지막\s*(?:대화|메시지|얘기)", text):
        last_ts = load_last_message_time()
        if not last_ts:
            return "아직 저장된 대화 기록이 없어."
        elapsed = format_elapsed(last_ts)
        elapsed_note = f" ({elapsed} 전)" if elapsed else " (방금 전)"
        return f"마지막 대화는 {last_ts}였어{elapsed_note}."

    # "OO 얘기/대화 언제 했어?" — 대화 내용 검색
    match = re.search(r"(.+?)\s*(?:얘기|대화|말)\s*(?:한|했)?\s*(?:거|건|게)?\s*언제", text)
    if match:
        keyword = match.group(1).strip()
        if keyword:
            found = search_messages(keyword, limit=3)
            if not found:
                return f"'{keyword}' 관련 대화 기록을 못 찾았어."
            lines = "\n".join(f"- [{m['timestamp']}] {m['content'][:40]}" for m in found)
            return f"'{keyword}' 관련 대화 기록이야:\n{lines}"

    return None


# ── PDF 요약 처리 ─────────────────────────────────────────────
def _handle_pdf_command(user_input: str) -> str | None:
    """'PDF 요약해줘' 같은 요약 명령을 감지해서 summarize_pdf 호출. 해당 없으면 None."""
    if "요약" not in user_input.strip():
        return None
    pdf_chunks = st.session_state.get("pdf_context")
    if not pdf_chunks:
        return None  # PDF 없으면 일반 대화로 넘겨서 자연스럽게 안내
    persona = get_persona_prompt(st.session_state.get("mode", "친구"), st.session_state["user_name"])
    return summarize_pdf(pdf_chunks, persona=persona)


# ── 파일 검색 처리 ─────────────────────────────────────────────
_MAX_FILE_SEARCH_RESULTS = 20  # 홈 디렉터리 전체 검색이라 결과가 많을 수 있어 상한 설정

# "파일"이라는 단어 없이도("이산수학 강의자료 같은거 찾아줘") 트리거되도록,
# 파일/문서 관련 단어가 하나라도 있으면 검색으로 인식 (없으면 일반 대화로 넘겨 오탐 방지)
_FILE_SEARCH_ANCHORS = (
    "파일", "폴더", "자료", "강의자료", "강의노트", "문서", "보고서", "슬라이드",
    "발표자료", "리포트", "ppt", "pdf", "hwp", "docx", "엑셀", "이미지", "사진",
    "folder", "file", "image", "photo", "document",
)

def _handle_file_search_command(user_input: str) -> str | None:
    """'OO 파일/자료 찾아줘/검색해줘' 명령을 감지해서 로컬 파일 시스템에서 검색. 해당 없으면 None."""
    text = user_input.strip()
    match = re.search(r"(.+?)\s*(?:찾아|검색해)(?:줘|줄래|봐)?", text)
    if not match:
        return None
    if not any(anchor in text.lower() for anchor in _FILE_SEARCH_ANCHORS):
        return None  # 파일/문서 관련 단어 없으면 일반 대화로 넘김 (오탐 방지)
    query = match.group(1).strip()
    if not query:
        return None
    results = search_files(query)
    if not results:
        return f"'{query}' 관련 파일을 못 찾았어."

    # Finder에서 첫 번째 결과 위치를 열어줌 — 실패해도 조용히 넘기지 않고 응답에 그대로 드러냄
    try:
        opened = subprocess.run(["open", "-R", results[0]], capture_output=True, text=True, timeout=5)
        finder_note = "Finder에서 첫 번째 파일 위치 열었어" if opened.returncode == 0 else f"Finder 열기 실패({opened.stderr.strip()})"
    except Exception as e:
        finder_note = f"Finder 열기 실패({e})"

    home = str(Path.home())
    shown = [p.replace(home, "~") for p in results[:_MAX_FILE_SEARCH_RESULTS]]
    lines = "\n".join(f"- {p}" for p in shown)
    more = len(results) - len(shown)
    suffix = f"\n...외 {more}개 더 있어" if more > 0 else ""
    return f"'{query}' 검색 결과 ({len(results)}개), {finder_note}:\n{lines}{suffix}"


# ── 공부 플래너 처리 ──────────────────────────────────────────
def _handle_study_command(user_input: str) -> str | None:
    """공부 추천 명령 감지 — 메모리 없으면 먼저 알려줌."""
    text = user_input.strip()
    if not any(k in text for k in ("공부", "학습", "뭐 할까", "뭐 배울", "오늘 계획")):
        return None
    if not any(k in text for k in ("추천", "뭐", "어떤", "계획", "할까")):
        return None

    mem = load_all_memory()
    missing = [k for k in ("goal", "study_style") if k not in mem]
    if missing:
        labels = {"goal": "목표", "study_style": "공부 방식"}
        missing_str = ", ".join(labels[k] for k in missing)
        return (
            f"맞춤 추천을 하려면 네 {missing_str}을 알아야 해!\n"
            f"예) '내 목표는 백엔드 개발자야', '나는 짧게 집중하는 스타일이야' 라고 알려줘."
        )
    return None  # 메모리 있으면 Claude가 system prompt 기반으로 처리


# ── 할 일 조회/완료/삭제 처리 ────────────────────────────────
def _handle_todo_command(user_input: str) -> str | None:
    text = user_input.strip().replace("할일", "할 일")  # 붙여쓰기 정규화

    # 할 일 추가 — "OO 할 일에 추가해줘" / "OO 투두에 추가해줘"
    # LLM의 [TODO:] 태그 누락 시(응답에서 "추가했어"라고 말만 하고 실제 저장 안 되는 문제) 대비해
    # 명시적 추가 요청은 태그에 의존하지 않고 직접 저장한다.
    add_match = re.search(r"(.+?)(?:를|을)?\s*(?:할 일|투두)(?:에|로)?\s*추가", text)
    if add_match:
        task = add_match.group(1).strip()
        if task:
            due_match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
            save_todo(task, due_match.group(1) if due_match else None)
            return f"'{task}' 할 일에 추가했어!"

    # 할 일 조회
    if any(k in text for k in ("할 일 보여", "할 일 목록", "할 일 뭐야", "할 일 알려", "해야 할 거", "투두")):
        todos = get_todos(only_pending=True)
        if not todos:
            return "할 일 창 열었어~ 지금 할 일 목록은 비어 있어 ㅎ"
        lines = []
        for t in todos:
            date_str = f" 📅{t['due_date']}" if t.get("due_date") else ""
            lines.append(f"{t['id']}.{date_str} {t['task']}")
        return "할 일 창 열었어!\n" + "\n".join(lines)

    # 완료된 것 전부 삭제 (← "완료" 체크보다 먼저)
    _clear_keywords = ("완료된 거 삭제", "완료된 것 삭제", "완료 삭제", "다 한 거 지워", "완료된 거 지워",
                       "완료된거 삭제", "완료된거 지워", "완료된거 없애", "완료된 거 없애",
                       "완료된 것 없애", "완료된 것들 없애", "완료된 것들 삭제", "완료된 것들 지워",
                       "다 없애", "전부 없애", "전부 삭제", "전부 지워")
    # "완료" + ("없애"/"지워"/"삭제") 조합도 감지
    _has_clear = any(k in text for k in _clear_keywords)
    _has_clear = _has_clear or ("완료" in text and any(k in text for k in ("없애", "지워", "삭제", "치워")))
    if _has_clear:
        count = clear_done_todos()
        return f"완료된 할 일 {count}개 전부 삭제했어!"

    # 완료된 할 일 보기 (← "완료" 체크보다 먼저)
    if any(k in text for k in ("완료된 할 일", "완료 목록", "다 한 거", "다 한 것")):
        done_list = [t for t in get_todos(only_pending=False) if t["done"]]
        if not done_list:
            return "아직 완료된 할 일이 없어!"
        lines = [f"✅ {t['task']}" + (f" (📅{t['due_date']})" if t.get("due_date") else "") for t in done_list]
        return "완료된 할 일이야:\n" + "\n".join(lines)

    # 기한 초과 확인
    if any(k in text for k in ("기한 지난", "마감 지난", "오버듀", "밀린 할 일")):
        overdue = get_overdue_todos()
        if not overdue:
            return "기한 지난 할 일 없어~ 잘하고 있는 거야 👍"
        lines = [f"⚠️ {t['task']} (마감: {t['due_date']})" for t in overdue]
        return "기한 지난 할 일이야:\n" + "\n".join(lines)

    # 완료 처리 — 반드시 번호 명시 필요 ("1번 완료", "2번 다 했어")
    id_match = re.search(r"(\d+)\s*번", text)
    if id_match and any(k in text for k in ("완료", "다 했어", "끝냈어", "했어")):
        done_todo(int(id_match.group(1)))
        return f"{id_match.group(1)}번 할 일 완료 처리했어! 👍"

    # 개별 삭제
    if any(k in text for k in ("할 일 삭제", "할 일 지워", "투두 삭제", "투두 지워")):
        todos = get_todos(only_pending=False)
        if not todos:
            return "삭제할 할 일이 없어!"
        id_match2 = re.search(r"(\d+)\s*번", text)
        if id_match2:
            todo_id = int(id_match2.group(1))
            target = next((t for t in todos if t["id"] == todo_id), None)
        else:
            target = todos[0]
        if target:
            delete_todo(target["id"])
            return f"[{target['task']}] 할 일 삭제했어."

    return None


_TODO_KEYWORDS = (
    "할 일", "할일", "투두", "todo", "해야", "마감", "기한",
    "완료", "끝냈어", "다 했어", "추가해", "삭제해", "지워", "없애",
)

def _open_todo_window() -> None:
    """이미 실행 중이면 띄우지 않음."""
    already = subprocess.run(["pgrep", "-f", "todo_window.py"], capture_output=True)
    if already.returncode != 0:  # 실행 중인 프로세스 없을 때만
        todo_script = str(__import__("pathlib").Path(__file__).parent / "todo_window.py")
        subprocess.Popen([sys.executable, todo_script])


# ── 대화 처리 ─────────────────────────────────────────────────
def responder(user_input: str, history: list[Message]) -> str:
    # 이번 사용자 메시지를 저장하기 전에 경과 시간부터 계산 (안 그러면 방금 저장한
    # 메시지 자신의 시각과 비교하게 돼서 항상 "0분"이 됨)
    elapsed = format_elapsed(load_last_message_time())
    save_message("user", user_input)

    reply: str | None = None
    raw = ""

    # 공부 플래너 — 메모리 없으면 먼저 안내
    reply = _handle_study_command(user_input)

    # 메모 명령어 우선 처리
    if reply is None:
        reply = _handle_note_command(user_input)

    # 대화 시간 조회 처리
    if reply is None:
        reply = _handle_time_lookup_command(user_input)

    # PDF 요약 명령어 처리
    if reply is None:
        reply = _handle_pdf_command(user_input)

    # 파일 검색 명령어 처리
    if reply is None:
        reply = _handle_file_search_command(user_input)

    # 할 일 명령어 처리
    if reply is None:
        reply = _handle_todo_command(user_input)

    # 나머지는 일반 대화 (질의응답 포함)
    if reply is None:
        raw = get_response(user_input, history, system=_build_system(user_input, elapsed))
        reply = _parse_and_update(raw)

    # 할 일 관련 대화면(사용자 입력이든 JIVIS 응답이든) 무조건 할 일 창 열기
    normalized_input = user_input.replace("할일", "할 일")
    if (
        any(k in normalized_input for k in _TODO_KEYWORDS)
        or any(k in reply for k in _TODO_KEYWORDS)
        or "[TODO:" in raw
        or "[DONE:" in raw
    ):
        _open_todo_window()

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

        elapsed_str = format_elapsed(load_last_message_time())

        now = datetime.now()
        greeting = generate_greeting(
            last_msgs,
            system=_build_system(elapsed=elapsed_str),
            elapsed=elapsed_str,
            current_time=now.strftime("%H:%M"),
        )
        if greeting:
            st.session_state["messages"].append(
                {"role": "assistant", "content": greeting, "time": now.strftime("%H:%M")}
            )

# ── 사이드바 ───────────────────────────────────────────────────
with st.sidebar:
    st.title("🤖 JIVIS")
    st.divider()

    st.session_state.setdefault("pdf_uploader_version", 0)
    uploaded_pdf = st.file_uploader(
        "PDF 업로드", type=["pdf"],
        key=f"pdf_uploader_{st.session_state['pdf_uploader_version']}",
    )
    if uploaded_pdf is not None:
        if st.session_state.get("pdf_filename") != uploaded_pdf.name:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                f.write(uploaded_pdf.read())
                tmp_path = f.name
            text = extract_text(tmp_path)
            st.session_state["pdf_context"] = chunk_text(text)
            st.session_state["pdf_filename"] = uploaded_pdf.name
        chunk_count = len(st.session_state["pdf_context"])
        if chunk_count > 0:
            st.success(f"{uploaded_pdf.name} · {chunk_count}청크 저장됨")
        else:
            st.warning(f"{uploaded_pdf.name}에서 텍스트를 추출하지 못했어요. 스캔 이미지 PDF일 수 있어요.")

    st.divider()

    # ── 음성 입력 (Day 11 STT) ──────────────────────────────────
    st.markdown("**🎙️ 음성 입력**")
    stt_duration = st.slider("녹음 시간(초)", 3, 10, 5, key="stt_duration")
    if st.button("🎙️ 녹음 시작", use_container_width=True):
        try:
            from src.tools.stt import record_and_transcribe
            with st.spinner("🎙️ 녹음 중..."):
                text = record_and_transcribe(duration=stt_duration)
            if text:
                st.session_state["voice_input"] = text
                st.success(f"인식 결과: {text}")
            else:
                st.warning("음성을 인식하지 못했어요.")
        except Exception as e:
            st.error(f"STT 오류: {e}")

    if st.session_state.get("voice_input"):
        voice_text = st.session_state["voice_input"]
        if st.button(f"💬 '{voice_text[:20]}...' 전송", use_container_width=True):
            if "messages" not in st.session_state:
                st.session_state["messages"] = []
            st.session_state["messages"].append({"role": "user", "content": voice_text})
            reply = responder(voice_text, st.session_state["messages"])
            st.session_state["messages"].append({"role": "assistant", "content": reply})
            st.session_state.pop("voice_input", None)
            st.rerun()

    st.divider()

    if st.button("대화 초기화"):
        st.session_state.messages = []
        st.session_state.pop("pdf_context", None)
        st.session_state.pop("pdf_filename", None)
        st.session_state["pdf_uploader_version"] += 1  # 위젯을 새로 만들어 업로드 상태까지 초기화
        clear_conversations()
        fresh_greeting = generate_fresh_greeting(system=_build_system())
        if fresh_greeting:
            now_str = datetime.now().strftime("%H:%M")
            st.session_state.messages = [{"role": "assistant", "content": fresh_greeting, "time": now_str}]
            save_message("assistant", fresh_greeting)
        st.rerun()


# ── 메인 화면 ─────────────────────────────────────────────────
st.header(f"{st.session_state['jivis_name']}와 대화하기")
render_chat(responder)
