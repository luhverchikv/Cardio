# voice_engine/validator.py
from enum import Enum


class ValidationStatus(str, Enum):
    OK = "ok"
    WARNING = "warning"
    INVALID = "invalid"


def validate_pressure(systolic: int, diastolic: int) -> tuple[ValidationStatus, list[str]]:
    errors = []

    if systolic < 70 or systolic > 250:
        return ValidationStatus.INVALID, ["Систолическое давление вне допустимого диапазона"]

    if diastolic < 40 or diastolic > 150:
        return ValidationStatus.INVALID, ["Диастолическое давление вне допустимого диапазона"]

    if diastolic >= systolic:
        return ValidationStatus.INVALID, ["Диастолическое давление не может быть выше систолического"]

    warnings = []
    if systolic < 90 or systolic > 180:
        warnings.append("Систолическое давление выглядит необычным")

    if diastolic < 60 or diastolic > 110:
        warnings.append("Диастолическое давление выглядит необычным")

    if warnings:
        return ValidationStatus.WARNING, warnings

    return ValidationStatus.OK, []


def validate_pulse(pulse: int) -> tuple[ValidationStatus, list[str]]:
    if pulse < 30 or pulse > 220:
        return ValidationStatus.INVALID, ["Пульс вне допустимого диапазона"]

    if pulse < 40 or pulse > 180:
        return ValidationStatus.WARNING, ["Пульс выглядит необычным"]

    return ValidationStatus.OK, []