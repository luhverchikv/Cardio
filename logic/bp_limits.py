# logic/bp_limits.py
from datetime import datetime, timedelta

MIN_INTERVAL_MINUTES = 45


def check_bp_interval(last_time: datetime | None) -> tuple[bool, int]:
    """
    Возвращает:
    - можно ли продолжать
    - сколько минут прошло с последнего измерения
    """
    if not last_time:
        return True, 0

    now = datetime.utcnow()
    diff_minutes = int((now - last_time).total_seconds() / 60)

    if diff_minutes < MIN_INTERVAL_MINUTES:
        return False, diff_minutes

    return True, diff_minutes