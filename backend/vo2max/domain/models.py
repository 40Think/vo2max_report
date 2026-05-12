from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4


class ActivityType(StrEnum):
    CYCLING = "cycling"
    RUNNING = "running"
    SWIMMING = "swimming"
    OTHER = "other"


class SportParameter(StrEnum):
    MAM = "mam"
    AEP = "aep"
    ANP = "anp"
    DO2 = "do2"
    VO2MAX = "vo2max"


@dataclass(slots=True)
class Client:
    first_name: str
    last_name: str
    second_name: str = ""
    gender: str | None = None
    birth_date: date | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    phone: str = ""
    email: str = ""
    notes: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))

    @property
    def full_name(self) -> str:
        parts = [self.last_name, self.first_name, self.second_name]
        return " ".join(part for part in parts if part).strip()


@dataclass(slots=True)
class MeasurementItem:
    time_sec: float
    time_label: str | None = None
    vo2_ml_kg_min: float | None = None
    vo2_ml_min: float | None = None
    vco2_ml_min: float | None = None
    hr: float | None = None
    power: float | None = None
    rated_power: int | None = None
    rf: float | None = None
    tv: float | None = None
    ve: float | None = None
    rpm: float | None = None
    ve_vo2: float | None = None
    feo2: float | None = None
    rer: float | None = None
    temp: float | None = None
    hum: float | None = None
    lactate: float | None = None
    sport_parameter: SportParameter | None = None
    use_in_report: bool = True
    source_fields: dict[str, str] = field(default_factory=dict)
    quality_flags: list[str] = field(default_factory=list)
    original_values: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))


@dataclass(slots=True)
class Measurement:
    client_id: str
    measurement_date: date
    activity_type: ActivityType = ActivityType.CYCLING
    title: str = ""
    protocol_name: str = ""
    start_power: int | None = None
    power_step: int | None = None
    raw_file_id: str | None = None
    source_format: str | None = None
    notes: str = ""
    use_in_report: bool = True
    items: list[MeasurementItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: str = field(default_factory=lambda: str(uuid4()))

    def update_rated_power(self) -> None:
        if self.start_power is None or self.power_step is None:
            for item in self.items:
                item.rated_power = None
            return

        current_power = self.start_power
        for item in self.items:
            if item.use_in_report:
                item.rated_power = current_power
                current_power += self.power_step
            else:
                item.rated_power = None
        self.touch()

    def infer_power_parameters(self, round_to: int = 10) -> None:
        powers = sorted(
            {
                int(round(item.power / round_to) * round_to)
                for item in self.items
                if item.power is not None
            }
        )
        if len(powers) <= 2:
            return

        deltas = [powers[i] - powers[i - 1] for i in range(1, len(powers))]
        self.start_power = powers[0]
        self.power_step = max(deltas)
        self.update_rated_power()

    def touch(self) -> None:
        self.updated_at = datetime.now(UTC)


@dataclass(slots=True)
class Threshold:
    measurement_id: str
    parameter: SportParameter
    item_time_sec: float | None = None
    power: float | None = None
    hr: float | None = None
    lactate: float | None = None
    vo2_ml_min: float | None = None
    notes: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))


@dataclass(slots=True)
class RawFile:
    original_name: str
    stored_path: str
    content_type: str | None = None
    checksum: str | None = None
    parser_version: str | None = None
    uploaded_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: str = field(default_factory=lambda: str(uuid4()))


@dataclass(slots=True)
class AuditEvent:
    entity_type: str
    entity_id: str
    action: str
    changed_by: str | None = None
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: str = field(default_factory=lambda: str(uuid4()))


@dataclass(slots=True)
class ImportWarning:
    level: str
    message: str
    row_number: int | None = None
    field: str | None = None
