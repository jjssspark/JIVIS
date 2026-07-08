"""macOS 메모앱(Notes.app) 연동 모듈 — AppleScript 기반"""
import subprocess


def _run(script: str) -> tuple[bool, str]:
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return r.returncode == 0, r.stdout.strip()


def _esc(s: str) -> str:
    """AppleScript 문자열 리터럴용 이스케이프"""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def create_note(title: str, body: str) -> bool:
    """메모 생성 후 메모앱 열기"""
    t, b = _esc(title), _esc(body)
    script = f'''
tell application "Notes"
    set n to make new note with properties {{name:"{t}", body:"{t}\\n\\n{b}"}}
    activate
    show n
end tell
'''
    ok, _ = _run(script)
    return ok


def update_note(title: str, new_body: str) -> bool:
    """제목으로 메모 찾아서 내용 수정 후 열기"""
    t, b = _esc(title), _esc(new_body)
    script = f'''
tell application "Notes"
    set theNote to first note whose name is "{t}"
    set body of theNote to "{t}\\n\\n{b}"
    activate
    show theNote
end tell
'''
    ok, _ = _run(script)
    return ok


def delete_note_by_title(title: str) -> bool:
    """제목으로 메모 찾아서 삭제"""
    t = _esc(title)
    script = f'''
tell application "Notes"
    delete first note whose name is "{t}"
end tell
'''
    ok, _ = _run(script)
    return ok


def open_notes_app() -> None:
    """메모앱만 열기"""
    subprocess.run(["osascript", "-e", 'tell application "Notes" to activate'])
