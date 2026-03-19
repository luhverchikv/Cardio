from voice_engine.numbers import words_to_number


def extract_values(text: str, pattern: str | None = None) -> dict:
    text = text.lower().strip()

    result = {
        "systolic": None,
        "diastolic": None,
        "pulse": None,
        "arrhythmic": False,
    }

    # 1️⃣ Аритмия
    if "аритмич" in text:
        result["arrhythmic"] = True
        text = (
            text.replace("аритмичный", "")
                .replace("аритмичная", "")
                .strip()
        )

    # 2️⃣ Пульс
    if "пульс" in text:
        left, right = text.split("пульс", 1)
        result["pulse"] = words_to_number(right.strip())
        text = left.strip()

    # 3️⃣ Диастолическое давление
    if " на " in text:
        left, right = text.split(" на ", 1)
        result["diastolic"] = words_to_number(right.strip())
        text = left.strip()

    # 4️⃣ Систолическое давление
    if "давление" in text:
        text = text.split("давление", 1)[1].strip()

    result["systolic"] = words_to_number(text)

    return result