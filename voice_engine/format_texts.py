# voice_ingine/format_texts.py

from .validator import validate_pressure, validate_pulse, ValidationStatus


def format_values(values, pressure_status=None, pressure_notes=None,
                  pulse_status=None, pulse_notes=None) -> str:
    """
    получает на вход значения давления и пульса, 
    сверяет их значения и выдает форматировпнный текст
    """
    
    parts = []

    if values.get("systolic") and values.get("diastolic"):
        line = (
            f"🩺 <b>Артериальное давление:</b> "
            f"{values['systolic']}/{values['diastolic']} мм рт. ст."
        )

        if pressure_status == ValidationStatus.WARNING:
            line += " ⚠️"
        elif pressure_status == ValidationStatus.INVALID:
            line += " ❌"

        parts.append(line)

        for note in pressure_notes or []:
            parts.append(f"• {note}")

    if values.get("pulse"):
        heart = "💔" if values.get("arrhythmic") else "❤️"

        line = (
            f"{heart} <b>Пульс:</b> "
            f"{values['pulse']} уд/мин"
        )

        if values.get("arrhythmic"):
            line += " ⚠️ аритмичный"

        if pulse_status == ValidationStatus.WARNING:
            line += " ⚠️"
            
        elif pulse_status == ValidationStatus.INVALID:
            line += " ❌"

        parts.append(line)


        for note in pulse_notes or []:
            parts.append(f"• {note}")

    return "\n".join(parts)