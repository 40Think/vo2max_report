from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from vo2max.domain import ActivityType, AuditEvent, Client, Measurement, MeasurementItem, SportParameter
from vo2max.parsers import LegacyCsvParser
from vo2max.services.import_service import ImportService
from vo2max.services.repository import EntityNotFoundError, InMemoryRepository


@dataclass(slots=True)
class MeasurementWorkspace:
    client: Client
    active_measurement: Measurement
    history: list[Measurement]


class MeasurementService:
    NUMERIC_ITEM_FIELDS = {
        "time_sec",
        "vo2_ml_kg_min",
        "vo2_ml_min",
        "vco2_ml_min",
        "hr",
        "power",
        "rated_power",
        "rf",
        "tv",
        "ve",
        "rpm",
        "ve_vo2",
        "feo2",
        "rer",
        "temp",
        "hum",
        "lactate",
    }
    STRING_ITEM_FIELDS = {"time_label"}
    BOOL_ITEM_FIELDS = {"use_in_report"}
    ENUM_ITEM_FIELDS = {"sport_parameter"}
    PROTECTED_ITEM_FIELDS = {"id", "source_fields", "quality_flags", "original_values"}

    def __init__(self, repository: InMemoryRepository, import_service: ImportService):
        self.repository = repository
        self.import_service = import_service

    def import_legacy_csv_for_client(
        self,
        client_id: str,
        source_path: Path | str,
        measurement_date: date,
        activity_type: ActivityType = ActivityType.CYCLING,
        title: str = "",
        changed_by: str | None = None,
    ) -> Measurement:
        self.repository.get_client(client_id)
        parser_result = self.import_service.preview(source_path)
        raw_file = self.import_service.store_raw_file(
            source_path,
            parser_version=LegacyCsvParser.parser_version,
        )
        self.repository.add_raw_file(raw_file)

        measurement = Measurement(
            client_id=client_id,
            measurement_date=measurement_date,
            activity_type=activity_type,
            title=title,
            raw_file_id=raw_file.id,
            source_format=parser_result.preview.source_format,
            items=parser_result.measurement.items,
        )
        measurement.infer_power_parameters()
        self.repository.add_measurement(measurement)
        self.repository.add_audit_event(
            AuditEvent(
                entity_type="measurement",
                entity_id=measurement.id,
                action="import_legacy_csv",
                changed_by=changed_by,
                after={
                    "source_file": Path(source_path).name,
                    "parsed_rows": parser_result.preview.parsed_rows,
                    "warnings": len(parser_result.preview.warnings),
                    "raw_file_id": raw_file.id,
                },
            )
        )
        return measurement

    def create_manual_measurement(
        self,
        client_id: str,
        measurement_date: date,
        activity_type: ActivityType = ActivityType.CYCLING,
        title: str = "",
        changed_by: str | None = None,
    ) -> Measurement:
        self.repository.get_client(client_id)
        measurement = Measurement(
            client_id=client_id,
            measurement_date=measurement_date,
            activity_type=activity_type,
            title=title,
        )
        self.repository.add_measurement(measurement)
        self._audit(
            measurement,
            action="create_manual_measurement",
            before=None,
            after={
                "measurement_date": measurement.measurement_date.isoformat(),
                "activity_type": measurement.activity_type.value,
                "title": measurement.title,
            },
            changed_by=changed_by,
        )
        return measurement

    def get_workspace(self, client_id: str, measurement_id: str) -> MeasurementWorkspace:
        client = self.repository.get_client(client_id)
        measurement = self.repository.get_measurement(measurement_id)
        if measurement.client_id != client_id:
            raise EntityNotFoundError(
                f"Measurement {measurement_id} does not belong to client {client_id}"
            )
        return MeasurementWorkspace(
            client=client,
            active_measurement=measurement,
            history=self.repository.list_measurements_for_client(client_id),
        )

    def update_power_parameters(
        self,
        measurement_id: str,
        start_power: int | None,
        power_step: int | None,
        changed_by: str | None = None,
    ) -> Measurement:
        measurement = self.repository.get_measurement(measurement_id)
        before = {"start_power": measurement.start_power, "power_step": measurement.power_step}
        measurement.start_power = start_power
        measurement.power_step = power_step
        measurement.update_rated_power()
        self._audit(
            measurement,
            action="update_power_parameters",
            before=before,
            after={"start_power": start_power, "power_step": power_step},
            changed_by=changed_by,
        )
        return measurement

    def update_item(
        self,
        measurement_id: str,
        item_id: str,
        changed_by: str | None = None,
        **changes,
    ) -> MeasurementItem:
        measurement = self.repository.get_measurement(measurement_id)
        item = self._get_item(measurement, item_id)
        normalized_changes = self._validate_item_changes(changes)
        before = {field_name: getattr(item, field_name) for field_name in normalized_changes}

        for field_name, value in normalized_changes.items():
            setattr(item, field_name, value)

        measurement.touch()
        if "use_in_report" in normalized_changes:
            measurement.update_rated_power()

        self._audit(
            measurement,
            action="update_measurement_item",
            before={"item_id": item_id, **before},
            after={"item_id": item_id, **normalized_changes},
            changed_by=changed_by,
        )
        return item

    def add_manual_item(
        self,
        measurement_id: str,
        changed_by: str | None = None,
        **values,
    ) -> MeasurementItem:
        measurement = self.repository.get_measurement(measurement_id)
        normalized_values = self._validate_item_changes(values)
        if normalized_values.get("time_sec") is None:
            raise ValueError("time_sec is required for manual measurement item")

        item = MeasurementItem(**normalized_values)
        if not item.time_label:
            item.time_label = self._format_time_label(item.time_sec)
        measurement.items.append(item)
        measurement.items.sort(key=lambda row: row.time_sec)
        measurement.touch()
        measurement.update_rated_power()
        self._audit(
            measurement,
            action="add_manual_measurement_item",
            before=None,
            after={"item_id": item.id, **normalized_values},
            changed_by=changed_by,
        )
        return item

    def set_item_use_in_report(
        self,
        measurement_id: str,
        item_id: str,
        use_in_report: bool,
        changed_by: str | None = None,
    ) -> MeasurementItem:
        return self.update_item(
            measurement_id,
            item_id,
            changed_by=changed_by,
            use_in_report=use_in_report,
        )

    def apply_row_sampling(
        self,
        measurement_id: str,
        every_n: int,
        changed_by: str | None = None,
    ) -> Measurement:
        if every_n < 1:
            raise ValueError("every_n must be greater than zero")

        measurement = self.repository.get_measurement(measurement_id)
        before = [
            {"item_id": item.id, "use_in_report": item.use_in_report}
            for item in measurement.items
        ]

        for index, item in enumerate(measurement.items):
            item.use_in_report = index % every_n == 0

        measurement.update_rated_power()
        self._audit(
            measurement,
            action="apply_row_sampling",
            before={"items": before},
            after={"every_n": every_n},
            changed_by=changed_by,
        )
        return measurement

    def list_measurements_for_client(self, client_id: str) -> list[Measurement]:
        return self.repository.list_measurements_for_client(client_id)

    def _get_item(self, measurement: Measurement, item_id: str) -> MeasurementItem:
        for item in measurement.items:
            if item.id == item_id:
                return item
        raise EntityNotFoundError(f"Measurement item not found: {item_id}")

    def _validate_item_changes(self, changes: dict[str, Any]) -> dict[str, Any]:
        normalized: dict[str, Any] = {}
        for field_name, value in changes.items():
            if field_name in self.PROTECTED_ITEM_FIELDS:
                raise ValueError(f"Measurement item field cannot be changed: {field_name}")
            if not hasattr(MeasurementItem, "__dataclass_fields__") or field_name not in MeasurementItem.__dataclass_fields__:
                raise ValueError(f"Unknown measurement item field: {field_name}")

            if field_name in self.NUMERIC_ITEM_FIELDS:
                if value is not None and not isinstance(value, (int, float)):
                    raise TypeError(f"Measurement item field must be numeric or None: {field_name}")
                normalized[field_name] = None if value is None else float(value)
                continue

            if field_name in self.STRING_ITEM_FIELDS:
                if value is not None and not isinstance(value, str):
                    raise TypeError(f"Measurement item field must be string or None: {field_name}")
                normalized[field_name] = value
                continue

            if field_name in self.BOOL_ITEM_FIELDS:
                if not isinstance(value, bool):
                    raise TypeError(f"Measurement item field must be bool: {field_name}")
                normalized[field_name] = value
                continue

            if field_name in self.ENUM_ITEM_FIELDS:
                if value is None or isinstance(value, SportParameter):
                    normalized[field_name] = value
                    continue
                if isinstance(value, str):
                    try:
                        normalized[field_name] = SportParameter(value)
                    except ValueError as exc:
                        raise ValueError(f"Unknown sport parameter: {value}") from exc
                    continue
                raise TypeError(f"Measurement item field must be SportParameter, string or None: {field_name}")

            normalized[field_name] = value
        return normalized

    def _format_time_label(self, time_sec: float) -> str:
        total_seconds = int(round(time_sec))
        minutes, seconds = divmod(total_seconds, 60)
        return f"{minutes:02d}:{seconds:02d}"

    def _audit(
        self,
        measurement: Measurement,
        action: str,
        before: dict[str, Any] | None,
        after: dict[str, Any] | None,
        changed_by: str | None,
    ) -> None:
        self.repository.add_audit_event(
            AuditEvent(
                entity_type="measurement",
                entity_id=measurement.id,
                action=action,
                changed_by=changed_by,
                before=before,
                after=after,
            )
        )
