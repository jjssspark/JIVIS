"""한국어 상대 날짜 표현 → 실제 날짜 변환 유틸"""
from datetime import datetime, timedelta


_WEEKDAY_KR = ["월", "화", "수", "목", "금", "토", "일"]


def get_date_context() -> str:
    """시스템 프롬프트에 삽입할 날짜 레퍼런스 블록 생성"""
    now = datetime.now()
    today = now.date()
    wd = today.weekday()  # 0=월 ~ 6=일

    yesterday  = today - timedelta(days=1)
    tomorrow   = today + timedelta(days=1)
    day_after  = today + timedelta(days=2)

    # 이번 주 각 요일
    this_week = {
        _WEEKDAY_KR[i]: (today + timedelta(days=(i - wd) % 7)).strftime("%Y-%m-%d")
        for i in range(7)
    }

    # 다음 주 각 요일
    next_week = {
        f"다음주{_WEEKDAY_KR[i]}": (today + timedelta(days=(i - wd) % 7 + 7)).strftime("%Y-%m-%d")
        for i in range(7)
    }

    lines = [
        f"- 어제: {yesterday}",
        f"- 오늘: {today} ({_WEEKDAY_KR[wd]}요일)",
        f"- 내일: {tomorrow}",
        f"- 모레: {day_after}",
    ]
    for kr, d in this_week.items():
        lines.append(f"- 이번주 {kr}요일: {d}")
    for kr, d in next_week.items():
        lines.append(f"- {kr}요일: {d}")

    return "\n".join(lines)
