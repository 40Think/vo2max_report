from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from vo2max.domain import ActivityType, SportParameter
from vo2max.services import (
    ClientService,
    EntityNotFoundError,
    ImportService,
    InMemoryRepository,
    MeasurementService,
    WorkspacePresenter,
)


ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / "samples" / "legacy_omnia_sample.csv"


class ClientMeasurementWorkflowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repository = InMemoryRepository()
        self.client_service = ClientService(self.repository)
        self.measurement_service = MeasurementService(
            repository=self.repository,
            import_service=ImportService(self.temp_dir.name),
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_client_profile_contains_imported_measurement_history(self) -> None:
        client = self.client_service.create_client(
            first_name="Ivan",
            last_name="Petrov",
            phone="+79990000000",
        )

        measurement = self.measurement_service.import_legacy_csv_for_client(
            client_id=client.id,
            source_path=SAMPLE,
            measurement_date=date(2026, 4, 29),
            activity_type=ActivityType.CYCLING,
            title="Baseline cycling test",
            changed_by="tester",
        )

        profile = self.client_service.get_profile(client.id)

        self.assertEqual(profile.client.full_name, "Petrov Ivan")
        self.assertEqual(profile.measurements, [measurement])
        self.assertEqual(measurement.client_id, client.id)
        self.assertEqual(len(measurement.items), 3)
        self.assertIsNotNone(measurement.raw_file_id)
        self.assertEqual(self.repository.audit_events[-1].action, "import_legacy_csv")

    def test_workspace_exposes_active_measurement_and_client_history(self) -> None:
        client = self.client_service.create_client(first_name="Anna", last_name="Sidorova")
        measurement = self.measurement_service.import_legacy_csv_for_client(
            client_id=client.id,
            source_path=SAMPLE,
            measurement_date=date(2026, 4, 29),
        )

        workspace = self.measurement_service.get_workspace(client.id, measurement.id)

        self.assertEqual(workspace.client.id, client.id)
        self.assertEqual(workspace.active_measurement.id, measurement.id)
        self.assertEqual([item.rated_power for item in workspace.active_measurement.items], [100, 120, 140])
        self.assertEqual(len(workspace.history), 1)

    def test_workspace_presenter_builds_frontend_ready_table_view(self) -> None:
        client = self.client_service.create_client(first_name="Anna", last_name="Sidorova")
        measurement = self.measurement_service.import_legacy_csv_for_client(
            client_id=client.id,
            source_path=SAMPLE,
            measurement_date=date(2026, 4, 29),
        )
        workspace = self.measurement_service.get_workspace(client.id, measurement.id)

        view = WorkspacePresenter().build(workspace)

        self.assertEqual(view.client["full_name"], "Sidorova Anna")
        self.assertEqual(view.active_measurement["items_count"], 3)
        self.assertGreaterEqual(len(view.table_columns), 10)
        self.assertEqual(view.table_rows[0]["hr"], 113.3)
        self.assertEqual(view.table_rows[0]["rated_power"], 100)

    def test_editing_measurement_item_updates_value_and_audit_trail(self) -> None:
        client = self.client_service.create_client(first_name="Olga", last_name="Ivanova")
        measurement = self.measurement_service.import_legacy_csv_for_client(
            client_id=client.id,
            source_path=SAMPLE,
            measurement_date=date(2026, 4, 29),
        )
        item = measurement.items[0]

        updated = self.measurement_service.update_item(
            measurement_id=measurement.id,
            item_id=item.id,
            hr=118.5,
            changed_by="expert",
        )

        self.assertEqual(updated.hr, 118.5)
        self.assertEqual(self.repository.audit_events[-1].action, "update_measurement_item")
        self.assertEqual(self.repository.audit_events[-1].before["hr"], 113.3)
        self.assertEqual(self.repository.audit_events[-1].after["hr"], 118.5)

    def test_manual_measurement_and_item_entry(self) -> None:
        client = self.client_service.create_client(first_name="Manual", last_name="Entry")
        measurement = self.measurement_service.create_manual_measurement(
            client_id=client.id,
            measurement_date=date(2026, 4, 30),
            activity_type=ActivityType.CYCLING,
            title="Manual test",
            changed_by="expert",
        )

        item = self.measurement_service.add_manual_item(
            measurement.id,
            time_sec=180,
            power=220,
            hr=158,
            vo2_ml_kg_min=48.5,
            lactate=4.2,
            changed_by="expert",
        )
        workspace = self.measurement_service.get_workspace(client.id, measurement.id)
        view = WorkspacePresenter().build(workspace)

        self.assertEqual(item.time_label, "03:00")
        self.assertEqual(view.active_measurement["items_count"], 1)
        self.assertEqual(view.table_rows[0]["power"], 220.0)
        self.assertEqual(view.table_rows[0]["hr"], 158.0)
        self.assertEqual(self.repository.audit_events[-1].action, "add_manual_measurement_item")

    def test_manual_item_requires_time_sec(self) -> None:
        client = self.client_service.create_client(first_name="Manual", last_name="Broken")
        measurement = self.measurement_service.create_manual_measurement(
            client_id=client.id,
            measurement_date=date(2026, 4, 30),
        )

        with self.assertRaises(ValueError):
            self.measurement_service.add_manual_item(measurement.id, hr=150)

    def test_row_sampling_and_manual_exclude_recalculate_rated_power(self) -> None:
        client = self.client_service.create_client(first_name="Maxim", last_name="Smirnov")
        measurement = self.measurement_service.import_legacy_csv_for_client(
            client_id=client.id,
            source_path=SAMPLE,
            measurement_date=date(2026, 4, 29),
        )

        self.measurement_service.apply_row_sampling(measurement.id, every_n=2, changed_by="expert")

        self.assertEqual([item.use_in_report for item in measurement.items], [True, False, True])
        self.assertEqual([item.rated_power for item in measurement.items], [100, None, 120])
        self.assertEqual(self.repository.audit_events[-1].action, "apply_row_sampling")

        self.measurement_service.set_item_use_in_report(
            measurement_id=measurement.id,
            item_id=measurement.items[0].id,
            use_in_report=False,
            changed_by="expert",
        )

        self.assertEqual([item.use_in_report for item in measurement.items], [False, False, True])
        self.assertEqual([item.rated_power for item in measurement.items], [None, None, 100])

    def test_client_search_uses_name_phone_and_email(self) -> None:
        self.client_service.create_client(
            first_name="Kirill",
            last_name="Agoge",
            email="coach@example.test",
        )
        self.client_service.create_client(first_name="Maria", last_name="Runner")

        self.assertEqual(len(self.client_service.search_clients("coach")), 1)
        self.assertEqual(len(self.client_service.search_clients("runner")), 1)

    def test_workspace_rejects_measurement_from_another_client(self) -> None:
        first_client = self.client_service.create_client(first_name="First", last_name="Client")
        second_client = self.client_service.create_client(first_name="Second", last_name="Client")
        measurement = self.measurement_service.import_legacy_csv_for_client(
            client_id=first_client.id,
            source_path=SAMPLE,
            measurement_date=date(2026, 4, 29),
        )

        with self.assertRaises(EntityNotFoundError):
            self.measurement_service.get_workspace(second_client.id, measurement.id)

    def test_update_item_rejects_unknown_and_invalid_fields(self) -> None:
        client = self.client_service.create_client(first_name="Test", last_name="Client")
        measurement = self.measurement_service.import_legacy_csv_for_client(
            client_id=client.id,
            source_path=SAMPLE,
            measurement_date=date(2026, 4, 29),
        )
        item = measurement.items[0]

        with self.assertRaises(ValueError):
            self.measurement_service.update_item(measurement.id, item.id, unknown_field=1)

        with self.assertRaises(TypeError):
            self.measurement_service.update_item(measurement.id, item.id, hr="fast")

        with self.assertRaises(ValueError):
            self.measurement_service.update_item(measurement.id, item.id, id="new-id")

    def test_update_item_accepts_sport_parameter_string_and_presenter_does_not_crash(self) -> None:
        client = self.client_service.create_client(first_name="Test", last_name="Point")
        measurement = self.measurement_service.import_legacy_csv_for_client(
            client_id=client.id,
            source_path=SAMPLE,
            measurement_date=date(2026, 4, 29),
        )
        item = measurement.items[0]

        self.measurement_service.update_item(measurement.id, item.id, sport_parameter="aep")
        workspace = self.measurement_service.get_workspace(client.id, measurement.id)
        view = WorkspacePresenter().build(workspace)

        self.assertEqual(item.sport_parameter, SportParameter.AEP)
        self.assertEqual(view.table_rows[0]["sport_parameter"], "aep")

    def test_client_update_rejects_id_change(self) -> None:
        client = self.client_service.create_client(first_name="Safe", last_name="Client")

        with self.assertRaises(ValueError):
            self.client_service.update_client(client.id, id="changed")


if __name__ == "__main__":
    unittest.main()
