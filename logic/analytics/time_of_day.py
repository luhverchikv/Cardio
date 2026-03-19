# logic/analytics/time_of_day.py
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class TimePeriodStats:
    sbp_mean: float | None
    dbp_mean: float | None
    count: int

    @property
    def valid(self) -> bool:
        return self.count >= 3 and self.sbp_mean is not None


@dataclass
class CircadianProfile:
    morning: TimePeriodStats
    day: TimePeriodStats
    evening: TimePeriodStats
    night: TimePeriodStats


def get_time_period(dt: datetime) -> str:
    hour = dt.hour

    if 6 <= hour <= 10:
        return "morning"
    if 11 <= hour <= 16:
        return "day"
    if 17 <= hour <= 21:
        return "evening"
    return "night"
