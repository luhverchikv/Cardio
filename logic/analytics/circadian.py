# logic/analytics/circadian.py
from statistics import mean
from collections import defaultdict

from logic.analytics.time_of_day import (
    TimePeriodStats, CircadianProfile, get_time_period
)

MIN_MEASUREMENTS = 10


def calculate_circadian_profile(entries: list[dict]) -> CircadianProfile:
    buckets = defaultdict(list)

    for e in entries:
        if not e.get("timestamp"):
            continue

        period = get_time_period(e["timestamp"])
        buckets[period].append(e)

    def calc(bucket: list[dict]) -> TimePeriodStats:
        sbp = [e["systolic"] for e in bucket if e.get("systolic")]
        dbp = [e["diastolic"] for e in bucket if e.get("diastolic")]

        if len(sbp) < MIN_MEASUREMENTS:
            return TimePeriodStats(
                sbp_mean=None,
                dbp_mean=None,
                count=len(sbp)
            )

        return TimePeriodStats(
            sbp_mean=mean(sbp),
            dbp_mean=mean(dbp),
            count=len(sbp)
        )

    return CircadianProfile(
        morning=calc(buckets["morning"]),
        day=calc(buckets["day"]),
        evening=calc(buckets["evening"]),
        night=calc(buckets["night"]),
    )