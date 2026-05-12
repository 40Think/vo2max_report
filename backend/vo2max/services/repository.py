from __future__ import annotations

from dataclasses import dataclass, field
import pickle
from pathlib import Path

from vo2max.domain import AuditEvent, Client, Measurement, RawFile, Threshold


class EntityNotFoundError(LookupError):
    """Raised when a requested domain entity does not exist."""


@dataclass(slots=True)
class InMemoryRepository:
    """Small repository used until the project gets a real database layer."""

    clients: dict[str, Client] = field(default_factory=dict)
    measurements: dict[str, Measurement] = field(default_factory=dict)
    raw_files: dict[str, RawFile] = field(default_factory=dict)
    thresholds: dict[str, Threshold] = field(default_factory=dict)
    audit_events: list[AuditEvent] = field(default_factory=list)

    def add_client(self, client: Client) -> Client:
        self.clients[client.id] = client
        self.persist()
        return client

    def get_client(self, client_id: str) -> Client:
        try:
            return self.clients[client_id]
        except KeyError as exc:
            raise EntityNotFoundError(f"Client not found: {client_id}") from exc

    def list_clients(self) -> list[Client]:
        return sorted(self.clients.values(), key=lambda client: client.full_name.lower())

    def add_measurement(self, measurement: Measurement) -> Measurement:
        self.get_client(measurement.client_id)
        self.measurements[measurement.id] = measurement
        self.persist()
        return measurement

    def get_measurement(self, measurement_id: str) -> Measurement:
        try:
            return self.measurements[measurement_id]
        except KeyError as exc:
            raise EntityNotFoundError(f"Measurement not found: {measurement_id}") from exc

    def list_measurements_for_client(self, client_id: str) -> list[Measurement]:
        self.get_client(client_id)
        return sorted(
            (
                measurement
                for measurement in self.measurements.values()
                if measurement.client_id == client_id
            ),
            key=lambda measurement: (measurement.measurement_date, measurement.created_at),
            reverse=True,
        )

    def add_raw_file(self, raw_file: RawFile) -> RawFile:
        self.raw_files[raw_file.id] = raw_file
        self.persist()
        return raw_file

    def upsert_threshold(self, threshold: Threshold) -> Threshold:
        self.get_measurement(threshold.measurement_id)
        for existing_id, existing in self.thresholds.items():
            if existing.measurement_id == threshold.measurement_id and existing.parameter == threshold.parameter:
                threshold.id = existing_id
                break
        self.thresholds[threshold.id] = threshold
        self.persist()
        return threshold

    def list_thresholds_for_measurement(self, measurement_id: str) -> list[Threshold]:
        self.get_measurement(measurement_id)
        return sorted(
            (
                threshold
                for threshold in self.thresholds.values()
                if threshold.measurement_id == measurement_id
            ),
            key=lambda threshold: threshold.parameter.value,
        )

    def get_threshold(self, measurement_id: str, parameter: str) -> Threshold:
        for threshold in self.thresholds.values():
            if threshold.measurement_id == measurement_id and threshold.parameter.value == parameter:
                return threshold
        raise EntityNotFoundError(f"Threshold not found: {measurement_id}/{parameter}")

    def add_audit_event(self, event: AuditEvent) -> AuditEvent:
        self.audit_events.append(event)
        self.persist()
        return event

    def list_audit_events(self, entity_id: str | None = None) -> list[AuditEvent]:
        if entity_id is None:
            return list(self.audit_events)
        return [event for event in self.audit_events if event.entity_id == entity_id]

    def persist(self) -> None:
        """Persist repository state when the concrete repository supports it."""


@dataclass(slots=True)
class FileRepository(InMemoryRepository):
    state_path: Path | str = "vo2max_state.pkl"

    def __post_init__(self) -> None:
        self.state_path = Path(self.state_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        if self.state_path.exists():
            with self.state_path.open("rb") as handle:
                state = pickle.load(handle)
            self.clients = state.get("clients", {})
            self.measurements = state.get("measurements", {})
            self.raw_files = state.get("raw_files", {})
            self.thresholds = state.get("thresholds", {})
            self.audit_events = state.get("audit_events", [])

    def persist(self) -> None:
        state = {
            "clients": self.clients,
            "measurements": self.measurements,
            "raw_files": self.raw_files,
            "thresholds": self.thresholds,
            "audit_events": self.audit_events,
        }
        with Path(self.state_path).open("wb") as handle:
            pickle.dump(state, handle)
