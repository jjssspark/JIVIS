"""대화에서 사용자 정보를 추출하는 모듈"""
import re


def extract_user_name(text: str) -> str | None:
    """
    사용자 메시지에서 이름을 추출.
    예) "내 이름은 박지윤이야" → "박지윤"
    """
    patterns = [
        r"내\s*이름\s*[은는이가]?\s*([가-힣]{2,5})[이야라고]",
        r"나\s+([가-힣]{2,5})[이야]야",
        r"([가-힣]{2,5})(이라고|라고)\s*불러",
        r"이름\s*[이가]?\s*([가-힣]{2,5})[이야]야",
        r"([가-힣]{2,5})(이야|야)[,.]?\s*(나야|맞아|ㅋ|ㅎ)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None


def extract_personality(text: str) -> str | None:
    """
    말투 변경 요청 감지.
    예) "존댓말로 해줘" → "존댓말"
    """
    if re.search(r"존댓말|공손하게|정중하게", text):
        return "존댓말"
    if re.search(r"반말|친구처럼|편하게", text):
        return "반말"
    if re.search(r"자비스|격식|품위", text):
        return "자비스"
    return None
