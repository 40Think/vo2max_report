from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from vo2max.domain import Client, Measurement, MeasurementItem
from vo2max.services.measurement_service import MeasurementWorkspace


MEASUREMENT_TABLE_COLUMNS: list[dict[str, Any]] = [
    {"field": "use_in_report", "label": "Report", "editable": True},
    {"field": "time_label", "label": "Time", "editable": False},
    {"field": "time_sec", "label": "Time, s", "editable": False},
    {"field": "rated_power", "label": "Rated power", "unit": "W", "editable": False},
    {"field": "power", "label": "Power", "unit": "W", "editable": True},
    {"field": "hr", "label": "HR", "unit": "bpm", "editable": True},
    {"field": "vo2_ml_kg_min", "label": "VO2", "unit": "mL/kg/min", "editable": True},
    {"field": "vo2_ml_min", "label": "VO2", "unit": "mL/min", "editable": True},
    {"field": "rf", "label": "Rf", "unit": "bpm", "editable": True},
    {"field": "tv", "label": "Tv", "unit": "L", "editable": True},
    {"field": "ve", "label": "Ve", "unit": "L/min", "editable": True},
    {"field": "rpm", "label": "RPM", "unit": "rpm", "editable": True},
    {"field": "ve_vo2", "label": "Ve/VO2", "editable": True},
    {"field": "feo2", "label": "FeO2", "unit": "%", "editable": True},
    {"field": "lactate", "label": "Lactate", "unit": "mmol/L", "editable": True},
    {"field": "sport_parameter", "label": "Point", "editable": True},
]


@dataclass(slots=True)
class WorkspaceView:
    client: dict[str, Any]
    active_measurement: dict[str, Any]
    history: list[dict[str, Any]]
    table_columns: list[dict[str, Any]]
    table_rows: list[dict[str, Any]]


class WorkspacePresenter:
    def build(self, workspace: MeasurementWorkspace) -> WorkspaceView:
        return WorkspaceView(
            client=self._client(workspace.client),
            active_measurement=self._measurement(workspace.active_measurement),
            history=[self._measurement(measurement) for measurement in workspace.history],
            table_columns=MEASUREMENT_TABLE_COLUMNS,
            table_rows=[self._item(item) for item in workspace.active_measurement.items],
        )

    def _client(self, client: Client) -> dict[str, Any]:
        return {
            "id": client.id,
            "full_name": client.full_name,
            "first_name": client.first_name,
            "last_name": client.last_name,
            "second_name": client.second_name,
            "gender": client.gender,
            "birth_date": client.birth_date.isoformat() if client.birth_date else None,
            "height_cm": client.height_cm,
            "weight_kg": client.weight_kg,
            "phone": client.phone,
            "email": client.email,
            "notes": client.notes,
        }

    def _measurement(self, measurement: Measurement) -> dict[str, Any]:
        return {
            "id": measurement.id,
            "client_id": measurement.client_id,
            "date": measurement.measurement_date.isoformat(),
            "activity_type": measurement.activity_type.value,
            "title": measurement.title,
            "protocol_name": measurement.protocol_name,
            "start_power": measurement.start_power,
            "power_step": measurement.power_step,
            "source_format": measurement.source_format,
            "raw_file_id": measurement.raw_file_id,
            "items_count": len(measurement.items),
            "use_in_report": measurement.use_in_report,
        }

    def _item(self, item: MeasurementItem) -> dict[str, Any]:
        point = item.sport_parameter.value if item.sport_parameter else None
        return {
            "id": item.id,
            "use_in_report": item.use_in_report,
            "time_sec": item.time_sec,
            "time_label": item.time_label,
            "rated_power": item.rated_power,
            "power": item.power,
            "hr": item.hr,
            "vo2_ml_kg_min": item.vo2_ml_kg_min,
            "vo2_ml_min": item.vo2_ml_min,
            "rf": item.rf,
            "tv": item.tv,
            "ve": item.ve,
            "rpm": item.rpm,
            "ve_vo2": item.ve_vo2,
            "feo2": item.feo2,
            "lactate": item.lactate,
            "sport_parameter": point,
            "quality_flags": list(item.quality_flags),
        }
