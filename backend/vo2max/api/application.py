from __future__ import annotations

import base64
import binascii
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any

from vo2max.domain import ActivityType
from vo2max.services import (
    ClientService,
    ChartService,
    FileRepository,
    ImportService,
    InMemoryRepository,
    MeasurementService,
    ReportService,
    ThresholdService,
    WorkspacePresenter,
)


class Vo2maxApplicationApi:
    """Dependency-free API facade used by CLI, tests and the thin HTTP wrapper."""

    def __init__(self, repository: InMemoryRepository, raw_storage_dir: Path | str, report_dir: Path | str):
        self.repository = repository
        self.client_service = ClientService(repository)
        self.measurement_service = MeasurementService(repository, ImportService(raw_storage_dir))
        self.chart_service = ChartService(repository)
        self.threshold_service = ThresholdService(repository)
        self.report_service = ReportService(repository, report_dir)
        self.workspace_presenter = WorkspacePresenter()

    def create_client(self, payload: dict[str, Any]) -> dict[str, Any]:
        client = self.client_service.create_client(**payload)
        return self._client_to_dict(client)

    def update_client(self, client_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        client = self.client_service.update_client(client_id, **payload)
        return self._client_to_dict(client)

    def list_clients(self, query: str = "") -> list[dict[str, Any]]:
        return [self._client_to_dict(client) for client in self.client_service.search_clients(query)]

    def get_client_profile(self, client_id: str) -> dict[str, Any]:
        profile = self.client_service.get_profile(client_id)
        return {
            "client": self._client_to_dict(profile.client),
            "measurements": [
                self.workspace_presenter._measurement(measurement)
                for measurement in profile.measurements
            ],
        }

    def import_measurement(self, client_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        measurement_date = date.fromisoformat(payload["measurement_date"])
        activity_type = ActivityType(payload.get("activity_type", ActivityType.CYCLING.value))
        measurement = self.measurement_service.import_legacy_csv_for_client(
            client_id=client_id,
            source_path=payload["source_path"],
            measurement_date=measurement_date,
            activity_type=activity_type,
            title=payload.get("title", ""),
            changed_by=payload.get("changed_by"),
        )
        return self.workspace_presenter._measurement(measurement)

    def upload_measurement(self, client_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        filename = Path(payload["filename"]).name
        if not filename:
            raise ValueError("filename is required")
        try:
            content = base64.b64decode(payload["content_base64"], validate=True)
        except (KeyError, binascii.Error) as exc:
            raise ValueError("content_base64 must contain a valid base64 file payload") from exc
        if not content:
            raise ValueError("uploaded file is empty")

        upload_dir = self.measurement_service.import_service.raw_storage_dir / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        upload_path = upload_dir / filename
        upload_path.write_bytes(content)

        import_payload = dict(payload)
        import_payload["source_path"] = str(upload_path)
        return self.import_measurement(client_id, import_payload)

    def create_manual_measurement(self, client_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        measurement_date = date.fromisoformat(payload["measurement_date"])
        activity_type = ActivityType(payload.get("activity_type", ActivityType.CYCLING.value))
        measurement = self.measurement_service.create_manual_measurement(
            client_id=client_id,
            measurement_date=measurement_date,
            activity_type=activity_type,
            title=payload.get("title", "Manual test"),
            changed_by=payload.get("changed_by"),
        )
        return self.workspace_presenter._measurement(measurement)

    def get_workspace(self, client_id: str, measurement_id: str) -> dict[str, Any]:
        workspace = self.measurement_service.get_workspace(client_id, measurement_id)
        return asdict(self.workspace_presenter.build(workspace))

    def get_charts(self, client_id: str, measurement_id: str) -> dict[str, Any]:
        return asdict(self.chart_service.build_client_comparison(client_id, measurement_id))

    def set_threshold(self, measurement_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        threshold = self.threshold_service.set_threshold_from_item(
            measurement_id=measurement_id,
            item_id=payload["item_id"],
            parameter=payload["parameter"],
            notes=payload.get("notes", ""),
            changed_by=payload.get("changed_by"),
        )
        return self.threshold_service.threshold_to_dict(threshold)

    def list_thresholds(self, measurement_id: str) -> list[dict[str, Any]]:
        return [
            self.threshold_service.threshold_to_dict(threshold)
            for threshold in self.threshold_service.list_thresholds(measurement_id)
        ]

    def get_training_zones(self, measurement_id: str) -> list[dict[str, Any]]:
        return [
            self.threshold_service.zone_to_dict(zone)
            for zone in self.threshold_service.calculate_zones(measurement_id)
        ]

    def preview_report_html(self, measurement_id: str) -> str:
        return self.report_service.render_html(measurement_id)

    def generate_reports(self, measurement_id: str) -> dict[str, Any]:
        files = self.report_service.export_all(measurement_id)
        return {
            "measurement_id": measurement_id,
            "files": [
                {
                    "format": file.format,
                    "filename": file.filename,
                    "path": file.path,
                    "content_type": file.content_type,
                    "download_url": f"/reports/{file.filename}",
                }
                for file in files
            ],
        }

    def update_measurement_item(
        self,
        measurement_id: str,
        item_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        changes = dict(payload)
        changed_by = changes.pop("changed_by", None)
        item = self.measurement_service.update_item(
            measurement_id=measurement_id,
            item_id=item_id,
            changed_by=changed_by,
            **changes,
        )
        return self.workspace_presenter._item(item)

    def add_manual_measurement_item(self, measurement_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        values = dict(payload)
        changed_by = values.pop("changed_by", None)
        item = self.measurement_service.add_manual_item(
            measurement_id=measurement_id,
            changed_by=changed_by,
            **values,
        )
        return self.workspace_presenter._item(item)

    def update_power_parameters(self, measurement_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        measurement = self.measurement_service.update_power_parameters(
            measurement_id=measurement_id,
            start_power=payload.get("start_power"),
            power_step=payload.get("power_step"),
            changed_by=payload.get("changed_by"),
        )
        return self.workspace_presenter._measurement(measurement)

    def apply_row_sampling(self, measurement_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        measurement = self.measurement_service.apply_row_sampling(
            measurement_id=measurement_id,
            every_n=int(payload["every_n"]),
            changed_by=payload.get("changed_by"),
        )
        return self.workspace_presenter._measurement(measurement)

    def _client_to_dict(self, client) -> dict[str, Any]:
        return self.workspace_presenter._client(client)


def create_application_api(
    raw_storage_dir: Path | str,
    state_path: Path | str | None = None,
) -> Vo2maxApplicationApi:
    raw_storage = Path(raw_storage_dir)
    report_dir = raw_storage.parent / "reports"
    return Vo2maxApplicationApi(
        repository=FileRepository(state_path=state_path or raw_storage / "vo2max_state.pkl"),
        raw_storage_dir=raw_storage,
        report_dir=report_dir,
    )
