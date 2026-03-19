# logic/analytics/report_builder.py
from .calculations import basic_stats, pulse_pressure, mean_arterial_pressure
from .adherence import calculate_adherence, calculate_dtir
from .flags import evaluate_clinical_status
from .models import PressureStats, BasicStats, AdherenceStats, ClinicalFlags
from logic.analytics.circadian import calculate_circadian_profile
from logic.analytics.circadian_flags import classify_dipping


def build_bp_report(entries: list[dict], targets: dict):
    sbp = [e["systolic"] for e in entries if e["systolic"]]
    dbp = [e["diastolic"] for e in entries if e["diastolic"]]
    hr = [e["pulse"] for e in entries if e.get("pulse")]

    sbp_stats = basic_stats(sbp)
    dbp_stats = basic_stats(dbp)
    hr_stats = basic_stats(hr) if hr else None

    pressure_stats = PressureStats(
        sbp=BasicStats(*sbp_stats),
        dbp=BasicStats(*dbp_stats),
        hr=BasicStats(*hr_stats) if hr_stats else None,
        pp_mean=pulse_pressure(sbp, dbp),
        map_mean=mean_arterial_pressure(sbp, dbp),
    )

    days_with, days_without, adherence = calculate_adherence(entries)
    dtir = calculate_dtir(entries, targets)

    adherence_stats = AdherenceStats(
        days_with, days_without, adherence, dtir
    )

    status, notes = evaluate_clinical_status(adherence, dtir)

    flags = ClinicalFlags(status=status, notes=notes)
    circadian = calculate_circadian_profile(entries)

    dipping_status = classify_dipping(
        circadian.day.sbp_mean,
        circadian.night.sbp_mean
    )
    
    return pressure_stats, adherence_stats, flags, circadian, dipping_status