# analytics/models.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class BasicStats:
    mean: float
    sd: float
    cv: float


@dataclass
class PressureStats:
    sbp: BasicStats
    dbp: BasicStats
    hr: Optional[BasicStats]
    pp_mean: float
    map_mean: float


@dataclass
class AdherenceStats:
    days_with_measurements: int
    days_without_measurements: int
    adherence_percent: float
    dtir_percent: float


@dataclass
class ClinicalFlags:
    status: str  # red / yellow / green
    notes: list[str]