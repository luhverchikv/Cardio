# logic/analytics/formatter.py

from logic.analytics.models import (
    PressureStats, AdherenceStats, ClinicalFlags
)
from logic.analytics.circadian import CircadianProfile


def format_bp_report(
    pressure: PressureStats,
    adherence: AdherenceStats,
    flags: ClinicalFlags,
    circadian,
    dipping_status: str
) -> str:

    lines = [
        "📊 <b>Отчёт за 30 дней</b>\n",

        "🩺 <b>Показатели АД:</b>",
        f"• SBP: {pressure.sbp.mean:.0f} ± {pressure.sbp.sd:.0f} мм рт.ст. (CV {pressure.sbp.cv:.0f}%)",
        f"• DBP: {pressure.dbp.mean:.0f} ± {pressure.dbp.sd:.0f} мм рт.ст. (CV {pressure.dbp.cv:.0f}%)",
        f"• Пульсовое давление: {pressure.pp_mean:.0f}",
        f"• MAP: {pressure.map_mean:.0f}\n",

        "📆 <b>Приверженность:</b>",
        f"• Дней с измерениями: {adherence.days_with_measurements}",
        f"• Дней без измерений: {adherence.days_without_measurements}",
        f"• Приверженность: {adherence.adherence_percent:.0f}%",
        f"• dTIR: {adherence.dtir_percent:.0f}%\n",

        f"🚦 <b>Статус:</b> {flags.status}",
    ]

    for note in flags.notes:
        lines.append(f"• {note}")

    lines.append("\n🌙 <b>Суточный профиль АД (SBP):</b>")

    def fmt(p):
        return f"{p.sbp_mean:.0f} мм рт.ст." if p.valid else "недостаточно данных"

    lines.extend([
        f"• Утро: {fmt(circadian.morning)}",
        f"• День: {fmt(circadian.day)}",
        f"• Вечер: {fmt(circadian.evening)}",
        f"• Ночь: {fmt(circadian.night)}",
    ])

    lines.append(f"\n🧠 <b>Тип суточного ритма:</b> {dipping_status}")

    return "\n".join(lines)