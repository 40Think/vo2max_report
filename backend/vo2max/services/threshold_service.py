from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from vo2max.domain import AuditEvent, MeasurementItem, SportParameter, Threshold
from vo2max.services.repository import EntityNotFoundError, InMemoryRepository


@dataclass(slots=True)
class TrainingZone:
    name: str
    lower_hr: float | None
    upper_hr: float | None
    lower_power: float | None
    upper_power: float | None


class ThresholdService:
    def __init__(self, repository: InMemoryRepository):
        self.repository = repository

    def set_threshold_from_item(
        self,
        measurement_id: str,
        item_id: str,
        parameter: SportParameter | str,
        notes: str = "",
        changed_by: str | None = None,
    ) -> Threshold:
        measurement = self.repository.get_measurement(measurement_id)
        parameter = SportParameter(parameter)
        item = self._get_item(measurement.items, item_id)
        before = self._threshold_to_dict_or_none(measurement_id, parameter)

        item.sport_parameter = parameter
        threshold = Threshold(
            measurement_id=measurement_id,
            parameter=parameter,
            item_time_sec=item.time_sec,
            power=item.power,
            hr=item.hr,
            lactate=item.lactate,
            vo2_ml_min=item.vo2_ml_min,
            notes=notes,
        )
        stored = self.repository.upsert_threshold(threshold)
        measurement.touch()
        self.repository.persist()
        self.repository.add_audit_event(
            AuditEvent(
                entity_type="measurement",
                entity_id=measurement_id,
                action="set_threshold",
                changed_by=changed_by,
                before=before,
                after=self.threshold_to_dict(stored),
            )
        )
        return stored

    def list_thresholds(self, measurement_id: str) -> list[Threshold]:
        return self.repository.list_thresholds_for_measurement(measurement_id)

    def calculate_zones(self, measurement_id: str) -> list[TrainingZone]:
        thresholds = {
            threshold.parameter: threshold
            for threshold in self.repository.list_thresholds_for_measurement(measurement_id)
        }
        aep = thresholds.get(SportParameter.AEP)
        anp = thresholds.get(SportParameter.ANP)
        vo2max = thresholds.get(SportParameter.VO2MAX) or thresholds.get(SportParameter.MAM)

        return [
            TrainingZone("Z1 recovery", None, self._hr(aep), None, self._power(aep)),
            TrainingZone("Z2 aerobic", self._hr(aep), self._hr(anp), self._power(aep), self._power(anp)),
            TrainingZone("Z3 threshold", self._hr(anp), self._hr(vo2max), self._power(anp), self._power(vo2max)),
            TrainingZone("Z4 high intensity", self._hr(vo2max), None, self._power(vo2max), None),
        ]

    def threshold_to_dict(self, threshold: Threshold) -> dict[str, Any]:
        return {
            "id": threshold.id,
            "measurement_id": threshold.measurement_id,
            "parameter": threshold.parameter.value,
            "item_time_sec": threshold.item_time_sec,
            "power": threshold.power,
            "hr": threshold.hr,
            "lactate": threshold.lactate,
            "vo2_ml_min": threshold.vo2_ml_min,
            "notes": threshold.notes,
        }

    def zone_to_dict(self, zone: TrainingZone) -> dict[str, Any]:
        return {
            "name": zone.name,
            "lower_hr": zone.lower_hr,
            "upper_hr": zone.upper_hr,
            "lower_power": zone.lower_power,
            "upper_power": zone.upper_power,
        }

    def _get_item(self, items: list[MeasurementItem], item_id: str) -> MeasurementItem:
        for item in items:
            if item.id == item_id:
                return item
        raise EntityNotFoundError(f"Measurement item not found: {item_id}")

    def _threshold_to_dict_or_none(self, measurement_id: str, parameter: SportParameter) -> dict[str, Any] | None:
        try:
            return self.threshold_to_dict(self.repository.get_threshold(measurement_id, parameter.value))
        except EntityNotFoundError:
            return None

    def _hr(self, threshold: Threshold | None) -> float | None:
        return None if threshold is None else threshold.hr

    def _power(self, threshold: Threshold | None) -> float | None:
        return None if threshold is None else threshold.power
