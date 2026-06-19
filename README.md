# JIVIS — 나만의 개인 AI 비서

> 카카오톡 스타일 UI로 대화하는 Claude 기반 개인 AI입니다.  
> 대화할수록 나를 기억하고, 껐다 켜도 이전 대화를 이어받습니다.

---

## 주요 기능

- **카카오톡 스타일 채팅 UI** — 말풍선, 아바타, 배경색까지
- **나를 기억하는 AI** — 이름, 말투 설정을 `memory.json`에 영구 저장
- **대화에서 이름 자동 감지** — "내 이름은 tina야" 하면 바로 기억
- **대화 기록 유지** — 앱을 껐다 켜도 이전 대화 맥락 이어받기
- **재접속 인사** — 이전 대화 분위기 그대로 자연스럽게 이어받기
- **말투 3종** — 반말 친구 / 존댓말 비서 / 자비스 격식체
- **Claude API 기반** — claude-haiku 모델로 빠르고 자연스러운 응답

---

## 시작하기

### 1. 저장소 클론

```bash
git clone https://github.com/jjssspark/JIVIS.git
cd JIVIS
```

### 2. 가상환경 & 패키지 설치

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 환경변수 설정

`.env.example`을 복사해서 `.env`를 만들고 API 키를 입력합니다.

```bash
cp .env.example .env
```

`.env` 파일:

```
ANTHROPIC_API_KEY=sk-ant-여기에-키-입력
MODEL_ID=claude-haiku-4-5-20251001
```

### 4. 실행

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속

---

## 프로젝트 구조

```
JIVIS/
├── app.py                  # 메인 진입점
├── memory.json             # 사용자 설정 + 대화 기록 저장 (자동 생성)
├── requirements.txt
├── .env                    # API 키 (git 제외)
├── .env.example            # 환경변수 예시
└── src/
    ├── agents/
    │   └── claude_ai.py    # Claude API 연동, 인사 생성
    ├── memory/
    │   └── memory.py       # 설정/대화 저장·불러오기
    ├── ui/
    │   └── chat.py         # 카카오톡 스타일 채팅 UI
    └── config.py           # 환경변수 로드
```

---

## 개발 일지 (1주차)

| 일차 | 작업 내용 |
|------|-----------|
| Day 1 | 프로젝트 구조 설계, 가상환경 구성 |
| Day 2 | Streamlit 카카오톡 스타일 채팅 UI 구현 |
| Day 3 | Claude API 연동, 시스템 프롬프트 / 페르소나 커스터마이징 |
| Day 4 | memory.json 영구 저장, 채팅에서 이름 자동 감지 |
| Day 5 | 대화 기록 저장·로드, 재접속 시 맥락 이어받기 인사 |

---

## 환경

- Python 3.13+
- Streamlit 1.35+
- Anthropic SDK 0.30+

---

## 라이선스

개인 학습 프로젝트입니다.
