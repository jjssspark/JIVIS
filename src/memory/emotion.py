EMOTION_KEYWORDS: dict[str, list[str]] = {
    "sad":     ["슬퍼", "힘들어", "우울", "망했", "실패", "속상", "눈물", "힘드", "죽겠", "최악"],
    "happy":   ["좋아", "신나", "행복", "최고", "성공", "해냈", "기뻐", "ㅋㅋ", "ㅎㅎ", "완료"],
    "anxious": ["불안", "걱정", "두려워", "무서워", "긴장", "떨려", "어떡하"],
    "angry":   ["화나", "짜증", "열받아", "싫어", "ㅡㅡ", "열받"],
    "tired":   ["피곤", "지쳐", "힘없", "졸려", "번아웃", "쉬고싶", "너무힘"],
}

EMOTION_PROMPTS: dict[str, str] = {
    "sad":     "사용자가 슬프거나 힘든 상황이야. 먼저 충분히 공감해주고 위로해줘. 해결책은 사용자가 원할 때만 제안해.",
    "happy":   "사용자가 기분이 좋아! 같이 신나게 반응해줘.",
    "anxious": "사용자가 불안해하고 있어. 차분하게 안심시켜주고 작은 다음 단계를 제안해줘.",
    "angry":   "사용자가 화가 났어. 판단하지 말고 일단 들어줘.",
    "tired":   "사용자가 지쳐있어. 무리하지 말라고 하고, 쉬어도 된다고 말해줘.",
    "neutral": "",
}


def detect_emotion(text: str) -> str:
    for emotion, keywords in EMOTION_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return emotion
    return "neutral"


def get_emotion_prompt(text: str) -> str:
    return EMOTION_PROMPTS.get(detect_emotion(text), "")
