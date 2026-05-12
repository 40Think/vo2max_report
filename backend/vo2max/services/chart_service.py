from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from vo2max.domain import Measurement, Threshold
from vo2max.services.repository import InMemoryRepository


@dataclass(slots=True)
class ChartPoint:
    item_id: str
    x: float
    y: float
    time_label: str | None = None


@dataclass(slots=True)
class ChartSeries:
    measurement_id: str
    label: str
    metric: str
    points: list[ChartPoint]


@dataclass(slots=True)
class ChartBundle:
    active_measurement_id: str
    charts: dict[str, list[ChartSeries]]
    thresholds: list[dict[str, Any]] = field(default_factory=list)


class ChartService:
    METRICS = {
        "hr": {"label": "ЧСС", "field": "hr", "unit": "bpm"},
        "ventilation": {"label": "Вентиляция", "field": "ve", "unit": "L/min"},
        "oxygen": {"label": "VO2", "field": "vo2_ml_kg_min", "unit": "mL/kg/min"},
        "lactate": {"label": "Лактат", "field": "lactate", "unit": "mmol/L"},
    }

    def __init__(self, repository: InMemoryRepository):
        self.repository = repository

    def build_measurement_charts(self, measurement_id: str) -> ChartBundle:
        measurement = self.repository.get_measurement(measurement_id)
        return self._bundle(measurement, [measurement])

    def build_client_comparison(self, client_id: str, active_measurement_id: str) -> ChartBundle:
        active = self.repository.get_measurement(active_measurement_id)
        if active.client_id != client_id:
            raise ValueError(f"Measurement {active_measurement_id} does not belong to client {client_id}")
        measurements = self.repository.list_measurements_for_client(client_id)
        return self._bundle(active, measurements)

    def _bundle(self, active: Measurement, measurements: list[Measurement]) -> ChartBundle:
        charts: dict[str, list[ChartSeries]] = {}
        for metric, config in self.METRICS.items():
            charts[metric] = [
                self._series(measurement, metric=metric, field_name=config["field"])
                for measurement in measurements
            ]
        return ChartBundle(
            active_measurement_id=active.id,
            charts=charts,
            thresholds=[
                self._threshold_marker(threshold)
                for threshold in self.repository.list_thresholds_for_measurement(active.id)
            ],
        )

    def _series(self, measurement: Measurement, metric: str, field_name: str) -> ChartSeries:
        points = []
        for item in measurement.items:
            value = getattr(item, field_name)
            if value is None:
                continue
            points.append(
                ChartPoint(
                    item_id=item.id,
                    x=item.time_sec,
                    y=float(value),
                    time_label=item.time_label,
                )
            )
        return ChartSeries(
            measurement_id=measurement.id,
            label=measurement.measurement_date.isoformat(),
            metric=metric,
            points=points,
        )

    def _threshold_marker(self, threshold: Threshold) -> dict[str, Any]:
        return {
            "id": threshold.id,
            "parameter": threshold.parameter.value,
            "time_sec": threshold.item_time_sec,
            "power": threshold.power,
            "hr": threshold.hr,
            "lactate": threshold.lactate,
            "vo2_ml_min": threshold.vo2_ml_min,
            "notes": threshold.notes,
        }
