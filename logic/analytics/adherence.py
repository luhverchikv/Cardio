# analytics/adherence.py
from datetime import datetime, timedelta


def calculate_adherence(entries: list[dict], days: int = 30):
    today = datetime.utcnow().date()
    dates = {
        entry["timestamp"].date()
        for entry in entries
    }

    days_with = sum(
        1 for i in range(days)
        if (today - timedelta(days=i)) in dates
    )

    adherence = (days_with / days) * 100

    return days_with, days - days_with, adherence


def calculate_dtir(entries: list[dict], targets: dict):
    if not entries:
        return 0.0

    controlled_days = set()

    for e in entries:
        if (
            e["systolic"] <= targets["systolic"]
            and e["diastolic"] <= targets["diastolic"]
        ):
            controlled_days.add(e["timestamp"].date())

    days_with = {e["timestamp"].date() for e in entries}

    return (len(controlled_days) / len(days_with)) * 100