import pytest
from src.memory.emotion import detect_emotion, get_emotion_prompt


@pytest.mark.parametrize("text,expected", [
    ("시험 망했어", "sad"),
    ("너무 힘들어", "sad"),
    ("오늘 진짜 행복해", "happy"),
    ("해냈다 최고야", "happy"),
    ("내일 발표 불안해", "anxious"),
    ("너무 걱정돼", "anxious"),
    ("진짜 화나 짜증나", "angry"),
    ("너무 피곤해", "tired"),
    ("완전 번아웃 왔어", "tired"),
    ("오늘 뭐 먹을까", "neutral"),
])
def test_detect_emotion(text: str, expected: str):
    assert detect_emotion(text) == expected


def test_get_emotion_prompt_sad_nonempty():
    result = get_emotion_prompt("너무 슬퍼")
    assert isinstance(result, str) and len(result) > 0


def test_get_emotion_prompt_neutral_empty():
    result = get_emotion_prompt("안녕 오늘 날씨 좋다")
    assert result == ""
