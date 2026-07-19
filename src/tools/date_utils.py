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


def format_elapsed(last_ts: str | None, now: datetime | None = None) -> str:
    """마지막 메시지 시각("YYYY-MM-DD HH:MM:SS", 로컬시간) 기준 경과 시간을 한국어로 반환.
    정보가 없거나 1분 미만이면 빈 문자열."""
    if not last_ts:
        return ""
    try:
        last_dt = datetime.strptime(last_ts, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return ""
    now = now or datetime.now()
    total_min = int((now - last_dt).total_seconds() / 60)
    if total_min < 1:
        return ""
    if total_min < 60:
        return f"{total_min}분"
    h, m = divmod(total_min, 60)
    return f"{h}시간" if m == 0 else f"{h}시간 {m}분"
