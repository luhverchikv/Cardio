# logic/report/blood_pressure_chart.py

import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import datetime, timedelta
from io import BytesIO

from mongo import users_collection


async def generate_blood_pressure_chart(user_id: int):
    user = await users_collection.find_one({"user_id": user_id})
    if not user:
        return None

    entries = user.get("blood_pressure_entries", [])
    targets = user.get("bp_targets", {})

    if not entries:
        return None

    systolic_target = targets.get("systolic")
    diastolic_target = targets.get("diastolic")

    today = datetime.today().date()
    start_date = today - timedelta(days=30)

    daily_sys = defaultdict(list)
    daily_dia = defaultdict(list)
    daily_pulse = defaultdict(list)
    daily_arrhythmia = defaultdict(bool)

    # --- Фильтрация и агрегация ---
    for entry in entries:
        ts = entry.get("timestamp")
        if not isinstance(ts, datetime):
            continue

        date_only = ts.date()
        if date_only < start_date:
            continue

        if entry.get("systolic") is not None:
            daily_sys[date_only].append(entry["systolic"])
        if entry.get("diastolic") is not None:
            daily_dia[date_only].append(entry["diastolic"])
        if entry.get("arrhythmic"):
            daily_arrhythmia[date_only] = True
        if entry.get("pulse") is not None:
            daily_pulse[date_only].append(entry["pulse"])

    
    if not daily_sys and not daily_dia:
        return None

    dates = [start_date + timedelta(days=i) for i in range(31)]
    labels = [d.strftime("%d.%m") for d in dates]

    max_sys = [max(daily_sys[d]) if d in daily_sys else 0 for d in dates]
    max_dia = [max(daily_dia[d]) if d in daily_dia else 0 for d in dates]
    max_pulse = [
        max(daily_pulse[d]) if d in daily_pulse else None
        for d in dates
    ]
    # вычисление максимального систолического для раскраски графика
    valid_sys = [s for s in max_sys if s > 0]
    if valid_sys:
        bp_max_value = max(valid_sys)
    else:
        bp_max_value = 140  # fallback
        
    # вычисдение самого максимального пульса для отрисовки цвета на графике
    valid_pulses = [p for p in max_pulse if p is not None]
    if valid_pulses:
        pulse_max_value = max(valid_pulses)
    else:
        pulse_max_value = 100  # fallback
    upper_limit = pulse_max_value + 10
    #ax_pulse.set_ylim(40, upper_limit)
    
    # --- Цвета ---
    sys_colors = []
    dia_colors = []

    for s, d in zip(max_sys, max_dia):
        # систолическое
        if s == 0:
            sys_colors.append("lightgrey")
        elif systolic_target is not None and s > systolic_target:
            sys_colors.append("red")
        else:
            sys_colors.append("green")

        # диастолическое
        if d == 0:
            dia_colors.append("lightgrey")
        elif diastolic_target is not None and d > diastolic_target:
            dia_colors.append("black")
        else:
            dia_colors.append("grey")

    # --- Построение ---
    fig, (ax_bp, ax_pulse) = plt.subplots(
        2,
        1,
        figsize=(12, 8),
        sharex=True,
        gridspec_kw={"height_ratios": [3, 1]}
    )
    
    # --- Динамический верхний предел давления ---
    bp_upper_limit = bp_max_value + 10
    #ax_bp.set_ylim(40, bp_upper_limit)

    # --- Цветовые зоны давления ---
    ax_bp.axhspan(90, min(120, bp_upper_limit), color="lightgreen", alpha=0.2)
    ax_bp.axhspan(120, min(140, bp_upper_limit), color="khaki", alpha=0.2)
    if bp_upper_limit > 140:
        ax_bp.axhspan(140, bp_upper_limit, color="lightcoral", alpha=0.2)
        
    # --- Цветовые зоны пульса ---
    ax_pulse.axhspan(55, min(70, upper_limit), color="lightgreen", alpha=0.3)
    ax_pulse.axhspan(70, min(90, upper_limit), color="khaki", alpha=0.3)

    if upper_limit > 90:
        ax_pulse.axhspan(90, upper_limit, color="lightcoral", alpha=0.3)

    x = range(len(dates))

    # Диастолическое (нижний слой)
    ax_bp.bar(
        x,
        max_dia,
        color=dia_colors,
        label="Диастолическое"
    )

    # Систолическое (верхний слой)
    ax_bp.bar(
        x,
        [s - d for s, d in zip(max_sys, max_dia)],
        bottom=max_dia,
        color=sys_colors,
        label="Систолическое"
    )
    
    # --- Отметки аритмии ---
    for i, day in enumerate(dates):
        if daily_arrhythmia.get(day, False) and max_sys[i] > 0:
            ax_bp.scatter(
                i,
                max_sys[i] + 3,
                marker="^",
                color="darkred",
                s=80,
                zorder=5
            )
    
    
    ax_pulse.plot(
        x,
        max_pulse,
        color="purple",
        marker="o",
        linewidth=2,
        label="Пульс"
    )
    
    pulse_min = targets.get("heart_rate_min")
    pulse_max = targets.get("heart_rate_max")

    for i, pulse in enumerate(max_pulse):
        if pulse is None:
            continue

        if (
            (pulse_min and pulse < pulse_min)
            or (pulse_max and pulse > pulse_max)
        ):
            ax_pulse.text(
                i,
                pulse + 2,
                str(pulse),
                ha="center",
                va="bottom",
                fontsize=9,
                color="red"
            )


    ax_pulse.set_ylabel("уд/мин")
    ax_pulse.set_xlabel("Дата")
    ax_pulse.grid(axis="y", linestyle="--", alpha=0.5)


    # --- Таргеты ---
    if diastolic_target is not None:
        ax_bp.axhline(
            y=diastolic_target,
            color="black",
            linestyle="--",
            linewidth=1,
            label=f"Цель ДАД ({diastolic_target})"
        )

    if systolic_target is not None:
        ax_bp.axhline(
            y=systolic_target,
            color="red",
            linestyle="--",
            linewidth=1,
            label=f"Цель САД ({systolic_target})"
        )
        
    pulse_min = targets.get("heart_rate_min")
    pulse_max = targets.get("heart_rate_max")

    if pulse_min:
        ax_pulse.axhline(pulse_min, color="purple", linestyle="--", alpha=0.5)

    if pulse_max:
        ax_pulse.axhline(pulse_max, color="purple", linestyle="--", alpha=0.5)


    # --- Оформление ---
    # для давления
    ax_bp.set_title("Артериальное давление за последние 30 дней")
    ax_bp.set_ylabel("мм рт. ст.")
    ax_bp.set_xlabel("Дата")
    ax_bp.set_xticks(x)
    ax_bp.set_xticklabels(labels, rotation=45, ha="right")
    ax_bp.grid(axis="y", linestyle="--", alpha=0.6)

    # для пульса
    ax_pulse.set_ylabel("уд/мин")
    ax_pulse.set_xlabel("Дата")
    ax_pulse.set_xticklabels(labels, rotation=45, ha="right")
    
    
    ax_bp.legend(loc="upper right")
    ax_pulse.legend(loc="upper right")


    
    
    
    min_dia = min([d for d in max_dia if d > 0], default=40)
    ax_bp.set_ylim(bottom=max(40, min_dia - 5))


    # --- Сохранение ---
    buf = BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)

    return buf