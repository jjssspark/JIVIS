"""JIVIS 할 일 — 네이티브 데스크탑 창 (날짜별 보기 + jivis.db 영구 저장)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import webview
from src.memory.database import init_db, get_todos, save_todo, done_todo, delete_todo


class TodoAPI:
    def get_todos(self):
        return get_todos(only_pending=False)

    def add_todo(self, task: str, due_date: str = "") -> bool:
        save_todo(task.strip(), due_date.strip() or None)
        return True

    def complete_todo(self, todo_id: int) -> bool:
        done_todo(int(todo_id))
        return True

    def uncheck_todo(self, todo_id: int) -> bool:
        import sqlite3
        from pathlib import Path
        db = Path(__file__).parent / "jivis.db"
        with sqlite3.connect(db) as conn:
            conn.execute("UPDATE todos SET done = 0 WHERE id = ?", (int(todo_id),))
        return True

    def delete_todo(self, todo_id: int) -> bool:
        delete_todo(int(todo_id))
        return True


HTML = r"""
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>JIVIS 할 일</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --bg:      #1e1e2e;
  --surface: #313244;
  --surface2:#45475a;
  --text:    #cdd6f4;
  --sub:     #a6adc8;
  --muted:   #6c7086;
  --accent:  #cba6f7;
  --green:   #a6e3a1;
  --red:     #f38ba8;
  --blue:    #89b4fa;
  --radius:  12px;
}
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: var(--bg);
  color: var(--text);
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ── 헤더 ── */
.header {
  padding: 16px 20px 12px;
  border-bottom: 1px solid var(--surface2);
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}
.header h1 { font-size: 17px; font-weight: 700; color: var(--accent); }
.badge {
  background: var(--accent);
  color: var(--bg);
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 20px;
}

/* ── 날짜 탭 ── */
.date-tabs {
  display: flex;
  gap: 6px;
  padding: 12px 20px 8px;
  overflow-x: auto;
  flex-shrink: 0;
  scrollbar-width: none;
}
.date-tabs::-webkit-scrollbar { display: none; }

.tab {
  flex-shrink: 0;
  padding: 6px 14px;
  border-radius: 20px;
  border: 1.5px solid var(--surface2);
  background: transparent;
  color: var(--sub);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}
.tab:hover { border-color: var(--accent); color: var(--accent); }
.tab.active {
  background: var(--accent);
  border-color: var(--accent);
  color: var(--bg);
  font-weight: 700;
}
.tab.has-todo { border-color: var(--blue); color: var(--blue); }
.tab.has-todo.active { background: var(--blue); border-color: var(--blue); color: var(--bg); }

/* ── 날짜 커스텀 피커 ── */
.date-picker-row {
  padding: 0 20px 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
.date-picker-row input[type=date] {
  padding: 6px 10px;
  border-radius: var(--radius);
  border: 1.5px solid var(--surface2);
  background: var(--surface);
  color: var(--text);
  font-size: 13px;
  color-scheme: dark;
  cursor: pointer;
  outline: none;
}
.date-picker-row input[type=date]:focus { border-color: var(--accent); }
.go-btn {
  padding: 6px 14px;
  border-radius: var(--radius);
  border: none;
  background: var(--surface2);
  color: var(--text);
  font-size: 13px;
  cursor: pointer;
}
.go-btn:hover { background: var(--accent); color: var(--bg); }

/* ── 할 일 목록 ── */
.list-area {
  flex: 1;
  overflow-y: auto;
  padding: 8px 20px;
}
.list-area::-webkit-scrollbar { width: 4px; }
.list-area::-webkit-scrollbar-thumb { background: var(--surface2); border-radius: 4px; }

.section-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .08em;
  color: var(--muted);
  margin: 12px 0 6px;
}

.todo-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 14px;
  border-radius: var(--radius);
  background: var(--surface);
  margin-bottom: 7px;
  transition: background .12s;
}
.todo-item:hover { background: #3a3b50; }

.todo-item input[type=checkbox] {
  width: 16px; height: 16px;
  accent-color: var(--green);
  cursor: pointer;
  flex-shrink: 0;
}
.todo-text { flex: 1; font-size: 14px; line-height: 1.4; }
.todo-item.done .todo-text { text-decoration: line-through; color: var(--muted); }
.date-badge {
  font-size: 11px;
  color: var(--blue);
  background: rgba(137,180,250,.12);
  padding: 2px 8px;
  border-radius: 8px;
  white-space: nowrap;
}
.del-btn {
  background: none;
  border: none;
  color: var(--muted);
  font-size: 15px;
  cursor: pointer;
  padding: 2px 5px;
  border-radius: 6px;
  transition: color .12s;
}
.del-btn:hover { color: var(--red); }

.empty {
  text-align: center;
  color: var(--muted);
  font-size: 14px;
  padding: 32px 0;
}

/* ── 입력 폼 ── */
.add-bar {
  display: flex;
  gap: 6px;
  padding: 12px 20px;
  border-top: 1px solid var(--surface2);
  flex-shrink: 0;
}
.add-bar input[type=text] {
  flex: 1;
  padding: 10px 14px;
  border-radius: var(--radius);
  border: 1.5px solid var(--surface2);
  background: var(--surface);
  color: var(--text);
  font-size: 14px;
  outline: none;
}
.add-bar input[type=text]:focus { border-color: var(--accent); }
.add-bar input[type=date] {
  padding: 10px 8px;
  border-radius: var(--radius);
  border: 1.5px solid var(--surface2);
  background: var(--surface);
  color: var(--text);
  font-size: 13px;
  color-scheme: dark;
  width: 136px;
  outline: none;
}
.add-bar input[type=date]:focus { border-color: var(--accent); }
.add-btn {
  padding: 10px 16px;
  border-radius: var(--radius);
  border: none;
  background: var(--accent);
  color: var(--bg);
  font-size: 20px;
  font-weight: 700;
  cursor: pointer;
  transition: opacity .15s;
}
.add-btn:hover { opacity: .85; }
</style>
</head>
<body>

<!-- 헤더 -->
<div class="header">
  <h1>✅ JIVIS 할 일</h1>
  <span class="badge" id="totalBadge">0</span>
</div>

<!-- 날짜 탭 (오늘 기준 ±7일) -->
<div class="date-tabs" id="dateTabs"></div>

<!-- 직접 날짜 선택 -->
<div class="date-picker-row">
  <input type="date" id="jumpDate" />
  <button class="go-btn" onclick="jumpToDate()">이동</button>
</div>

<!-- 할 일 목록 -->
<div class="list-area" id="listArea"></div>

<!-- 입력 폼 -->
<div class="add-bar">
  <input type="text" id="taskInput" placeholder="새 할 일..." onkeydown="if(event.key==='Enter') addTodo()">
  <input type="date" id="dateInput">
  <button class="add-btn" onclick="addTodo()">＋</button>
</div>

<script>
let allTodos = [];
let activeFilter = 'all'; // 'all' | YYYY-MM-DD

// 날짜 헬퍼
function today() {
  return new Date().toISOString().slice(0, 10);
}
function fmtTab(dateStr) {
  const d = new Date(dateStr + 'T00:00:00');
  return `${d.getMonth()+1}/${d.getDate()}`;
}
function offsetDate(base, n) {
  const d = new Date(base + 'T00:00:00');
  d.setDate(d.getDate() + n);
  return d.toISOString().slice(0, 10);
}

// 탭 생성 (오늘 -2 ~ +10)
function buildTabs(todos) {
  const tabs = document.getElementById('dateTabs');
  const t = today();
  const dateSet = new Set(todos.map(td => td.due_date).filter(Boolean));

  tabs.innerHTML = '';
  // 전체 탭
  const all = makeTab('전체', 'all', todos.some(td => !td.done && !td.due_date));
  tabs.appendChild(all);

  for (let i = -2; i <= 10; i++) {
    const d = offsetDate(t, i);
    const hasTodo = dateSet.has(d);
    const tab = makeTab(fmtTab(d), d, hasTodo);
    tabs.appendChild(tab);
  }
}

function makeTab(label, value, hasTodo) {
  const btn = document.createElement('button');
  btn.className = 'tab' + (hasTodo ? ' has-todo' : '') + (activeFilter === value ? ' active' : '');
  btn.textContent = label;
  btn.onclick = () => { activeFilter = value; refresh(); };
  return btn;
}

// 목록 렌더링
function renderList(todos) {
  const area = document.getElementById('listArea');
  area.innerHTML = '';

  let items;
  if (activeFilter === 'all') {
    items = todos;
  } else {
    items = todos.filter(t => t.due_date === activeFilter);
  }

  const pending = items.filter(t => !t.done);
  const done    = items.filter(t => t.done);

  // 미완료 할일 없고 전체 뷰면 날짜 없는 것도 표시
  if (activeFilter === 'all') {
    const undated = todos.filter(t => !t.due_date && !t.done);
    if (undated.length) {
      area.appendChild(makeSection('날짜 없는 할 일', undated));
    }
  }

  if (pending.length) area.appendChild(makeSection('할 일', pending));
  if (done.length)    area.appendChild(makeSection('완료', done));

  if (!items.length && !(activeFilter === 'all' && todos.filter(t => !t.due_date && !t.done).length)) {
    area.innerHTML = '<div class="empty">할 일이 없어~ ☀️</div>';
  }

  // 전체 미완료 배지
  const totalPending = todos.filter(t => !t.done).length;
  document.getElementById('totalBadge').textContent = totalPending || '✓';
}

function makeSection(title, items) {
  const frag = document.createDocumentFragment();
  const label = document.createElement('div');
  label.className = 'section-label';
  label.textContent = `${title} (${items.length})`;
  frag.appendChild(label);
  items.forEach(t => frag.appendChild(makeTodoItem(t)));
  return frag;
}

function makeTodoItem(t) {
  const li = document.createElement('div');
  li.className = 'todo-item' + (t.done ? ' done' : '');

  const cb = document.createElement('input');
  cb.type = 'checkbox';
  cb.checked = t.done;
  cb.onchange = async () => {
    if (cb.checked) await pywebview.api.complete_todo(t.id);
    else            await pywebview.api.uncheck_todo(t.id);
    await refresh();
  };

  const span = document.createElement('span');
  span.className = 'todo-text';
  span.textContent = t.task;

  const del = document.createElement('button');
  del.className = 'del-btn';
  del.textContent = '✕';
  del.onclick = async () => { await pywebview.api.delete_todo(t.id); await refresh(); };

  li.appendChild(cb);
  li.appendChild(span);
  if (t.due_date && activeFilter === 'all') {
    const badge = document.createElement('span');
    badge.className = 'date-badge';
    badge.textContent = '📅 ' + fmtTab(t.due_date);
    li.appendChild(badge);
  }
  li.appendChild(del);
  return li;
}

async function refresh() {
  allTodos = await pywebview.api.get_todos();
  buildTabs(allTodos);
  renderList(allTodos);
}

async function addTodo() {
  const task = document.getElementById('taskInput').value.trim();
  const date = document.getElementById('dateInput').value;
  if (!task) return;
  await pywebview.api.add_todo(task, date || '');
  document.getElementById('taskInput').value = '';
  await refresh();
}

function jumpToDate() {
  const d = document.getElementById('jumpDate').value;
  if (!d) return;
  activeFilter = d;
  refresh();
}

// 오늘 날짜로 입력 기본값
document.getElementById('dateInput').value = today();
document.getElementById('jumpDate').value = today();

window.addEventListener('pywebviewready', refresh);
</script>
</body>
</html>
"""

if __name__ == "__main__":
    init_db()
    api = TodoAPI()
    window = webview.create_window(
        title="JIVIS 할 일",
        html=HTML,
        js_api=api,
        width=540,
        height=720,
        resizable=True,
    )
    webview.start(debug=False)
