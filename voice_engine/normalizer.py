# voice_engine/normalizer.py
import re

REPLACEMENTS = {
    "пуль": "пульс",
    "пулс": "пульс",

    "давлени": "давление",

    "аритмич": "аритмичный",
}


def normalize_medical_terms(text: str) -> str:
    text = text.lower().strip()

    # 1️⃣ Лечим "а ритмичный", "о ритмичный", "э ритмичный"
    text = re.sub(
        r"\b[аоэ]\s+ритмич\w*\b",
        "аритмичный",
        text
    )

    # 2️⃣ Лечим обрубленные слова
    words = text.split()
    normalized_words = []

    for w in words:
        replaced = False
        for key, value in REPLACEMENTS.items():
            if w.startswith(key):
                normalized_words.append(value)
                replaced = True
                break
        if not replaced:
            normalized_words.append(w)

    return " ".join(normalized_words)