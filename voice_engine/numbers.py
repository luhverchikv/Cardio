# voice_engine/numbers.py

NUMBERS = {
    "ноль": 0, "один": 1, "раз": 1, "два": 2, "две": 2, "три": 3, "четыре": 4,
    "пять": 5, "шесть": 6, "семь": 7, "восемь": 8, "девять": 9,
    "десять": 10, "одиннадцать": 11, "двенадцать": 12, "тринадцать": 13,
    "четырнадцать": 14, "пятнадцать": 15, "шестнадцать": 16,
    "семнадцать": 17, "восемнадцать": 18, "девятнадцать": 19,
    "двадцать": 20, "тридцать": 30, "сорок": 40, "пятьдесят": 50,
    "шестьдесят": 60, "семьдесят": 70, "восемьдесят": 80, "девяносто": 90,
    "сто": 100, "двести": 200, "триста": 300, "четыреста": 400,
    "пятьсот": 500, "шестьсот": 600, "семьсот": 700, "восемьсот": 800,
    "девятьсот": 900,
}

MULTIPLIERS = {
    "тысяча": 1000, "тысячи": 1000, "тысяч": 1000,
}


def words_to_number(text: str) -> int | None:
    """Преобразует числительные в число."""
    words = text.lower().split()
    total = 0
    current = 0

    # Если все слова — цифры 0–9, собираем как "123"
    if all(w in NUMBERS and NUMBERS[w] < 10 for w in words):
        return int("".join(str(NUMBERS[w]) for w in words))

    for w in words:
        if w in NUMBERS:
            current += NUMBERS[w]
        elif w in MULTIPLIERS:
            current = max(1, current) * MULTIPLIERS[w]
            total += current
            current = 0
        elif w.isdigit():
            current += int(w)
    total += current
    return total if total > 0 else None