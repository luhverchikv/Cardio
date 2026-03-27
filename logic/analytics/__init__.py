# logic/analytics/__init__.py
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from mongo import users_collection, get_bp_entries_last_days
from .adherence import calculate_adherence, calculate_dtir


def _get_utc_now() -> datetime:
    """Хелпер для получения текущего времени в UTC"""
    return datetime.now(timezone.utc)


async def generate_smart_user_analytics(user_id: int, days: int = 30) -> Optional[Dict[str, Any]]:
    """
    Генерирует аналитический отчёт для смарт-пользователя.
    
    Возвращает:
    {
        'avg_systolic': float,      # Среднее САД
        'avg_diastolic': float,     # Среднее ДАД
        'avg_pulse': float,         # Средний пульс
        'adherence': float,         # % дней с измерениями
        'dtir': float,              # % дней в целевом диапазоне
        'records_count': int,       # Всего записей
        'trend': str,               # '📈 Рост' / '📉 Снижение' / '➡️ Стабильно'
        'alerts': list[str],        # Предупреждения
        'period': str               # Период отчёта
    }
    """
    entries, targets = await get_bp_entries_last_days(user_id, days)
    
    if not entries:
        return None
    
    # --- Базовые метрики ---
    systolic_vals = [e["systolic"] for e in entries if e.get("systolic")]
    diastolic_vals = [e["diastolic"] for e in entries if e.get("diastolic")]
    pulse_vals = [e["pulse"] for e in entries if e.get("pulse")]
    
    avg_sys = round(sum(systolic_vals) / len(systolic_vals), 1) if systolic_vals else None
    avg_dia = round(sum(diastolic_vals) / len(diastolic_vals), 1) if diastolic_vals else None
    avg_pulse = round(sum(pulse_vals) / len(pulse_vals), 1) if pulse_vals else None
    
    # --- Приверженность (adherence) ---
    days_with, days_without, adherence = calculate_adherence(entries, days)
    
    # --- DTIR (Days in Target Range) ---
    dtir = calculate_dtir(entries, targets) if targets else 0.0
    
    # --- Тренд (сравнение первой и второй половины периода) ---
    trend = "➡️ Стабильно"
    if len(systolic_vals) >= 4:  # Минимум 4 записи для анализа
        mid = len(systolic_vals) // 2
        first_half = sum(systolic_vals[:mid]) / mid
        second_half = sum(systolic_vals[mid:]) / (len(systolic_vals) - mid)
        diff = second_half - first_half
        if abs(diff) > 5:  # Порог значимости 5 мм рт.ст.
            trend = "📈 Рост" if diff > 0 else "📉 Снижение"
    
    # --- Предупреждения ---
    alerts = []
    if avg_sys and targets and avg_sys > targets.get("systolic", 180):
        alerts.append(f"⚠️ Среднее САД ({avg_sys}) выше целевого ({targets['systolic']})")
    if avg_dia and targets and avg_dia > targets.get("diastolic", 120):
        alerts.append(f"⚠️ Среднее ДАД ({avg_dia}) выше целевого ({targets['diastolic']})")
    if adherence < 50:
        alerts.append(f"⚠️ Низкая приверженность: измерения только в {adherence:.0f}% дней")
    if dtir < 50 and targets:
        alerts.append(f"⚠️ Контроль АД: только {dtir:.0f}% дней в целевом диапазоне")
    
    # --- Период ---
    end_date = _get_utc_now().date()
    start_date = end_date - timedelta(days=days)
    period = f"{start_date.strftime('%d.%m')} — {end_date.strftime('%d.%m')}"
    
    return {
        "avg_systolic": avg_sys,
        "avg_diastolic": avg_dia,
        "avg_pulse": avg_pulse,
        "adherence": adherence,
        "dtir": dtir,
        "records_count": len(entries),
        "trend": trend,
        "alerts": alerts,
        "period": period,
        "targets": targets
    }

