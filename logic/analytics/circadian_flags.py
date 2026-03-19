# logic/analytics/circadian_flags.py

def classify_dipping(day_sbp: float | None, night_sbp: float | None) -> str | None:
    if not day_sbp or not night_sbp:
        return None

    drop = (day_sbp - night_sbp) / day_sbp * 100

    if drop >= 10:
        return "Диппер (нормальное ночное снижение)"
    if 0 <= drop < 10:
        return "Нон-диппер (недостаточное ночное снижение)"
    if drop < 0:
        return "Найт-пикер (ночная гипертензия)"

    return None