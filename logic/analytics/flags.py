# analytics/flags.py

def evaluate_clinical_status(adherence: float, dtir: float):
    notes = []

    if adherence < 50:
        return "🔴 Тревога", ["Пациент выпал из наблюдения"]

    if dtir < 60:
        return "🟡 Внимание", ["АД часто вне целевого диапазона"]

    if adherence > 85 and dtir > 75:
        return "🟢 Стабильность", ["Хорошая приверженность и контроль АД"]

    return "🟡 Внимание", ["Требуется наблюдение"]