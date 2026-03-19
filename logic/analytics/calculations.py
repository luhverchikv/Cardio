# analytics/calculations.py
import math
from statistics import mean, stdev


def basic_stats(values: list[float]):
    if len(values) < 2:
        return None

    m = mean(values)
    sd = stdev(values)
    cv = (sd / m) * 100 if m else 0

    return m, sd, cv


def pulse_pressure(sbp: list[int], dbp: list[int]) -> float:
    values = [s - d for s, d in zip(sbp, dbp)]
    return mean(values)


def mean_arterial_pressure(sbp: list[int], dbp: list[int]) -> float:
    values = [d + (s - d) / 3 for s, d in zip(sbp, dbp)]
    return mean(values)