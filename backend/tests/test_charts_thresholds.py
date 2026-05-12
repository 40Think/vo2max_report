from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from vo2max.domain import SportParameter
from vo2max.services import (
    ChartService,
    ClientService,
    ImportService,
    InMemoryRepository,
    MeasurementService,
    ThresholdService,
)


ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / "samples" / "legacy_omnia_sample.csv"


class ChartsThresholdsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repository = InMemoryRepository()
        self.client_service = ClientService(self.repository)
        self.measurement_service = MeasurementService(
            repository=self.repository,
            import_service=ImportService(self.temp_dir.name),
        )
        self.chart_service = ChartService(self.repository)
        self.threshold_service = ThresholdService(self.repository)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_charts_are_built_from_real_measurement_rows(self) -> None:
        client = self.client_service.create_client(first_name="Chart", last_name="Client")
        measurement = self.measurement_service.import_legacy_csv_for_client(
            client_id=client.id,
            source_path=SAMPLE,
            measurement_date=date(2026, 4, 29),
        )
        self.measurement_service.update_item(measurement.id, measurement.items[1].id, lactate=2.1)

        bundle = self.chart_service.build_measurement_charts(measurement.id)

        self.assertEqual(bundle.active_measurement_id, measurement.id)
        self.assertEqual(len(bundle.charts["hr"][0].points), 3)
        self.assertEqual(bundle.charts["hr"][0].points[0].y, 113.3)
        self.assertEqual(len(bundle.charts["ventilation"][0].points), 3)
        self.assertEqual(len(bundle.charts["oxygen"][0].points), 3)
        self.assertEqual(len(bundle.charts["lactate"][0].points), 1)

    def test_client_comparison_contains_multiple_measurements(self) -> None:
        client = self.client_service.create_client(first_name="Compare", last_name="Client")
        first = self.measurement_service.import_legacy_csv_for_client(
            client_id=client.id,
            source_path=SAMPLE,
            measurement_date=date(2026, 4, 29),
        )
        self.measurement_service.import_legacy_csv_for_client(
            client_id=client.id,
            source_path=SAMPLE,
            measurement_date=date(2026, 5, 29),
        )

        bundle = self.chart_service.build_client_comparison(client.id, first.id)

        self.assertEqual(len(bundle.charts["hr"]), 2)
        self.assertEqual({series.measurement_id for series in bundle.charts["hr"]}, {first.id, self.repository.list_measurements_for_client(client.id)[0].id})

    def test_threshold_from_item_marks_row_and_calculates_zones(self) -> None:
        client = self.client_service.create_client(first_name="Threshold", last_name="Client")
        measurement = self.measurement_service.import_legacy_csv_for_client(
            client_id=client.id,
            source_path=SAMPLE,
            measurement_date=date(2026, 4, 29),
        )
        aep_item = measurement.items[0]
        anp_item = measurement.items[1]

        aep = self.threshold_service.set_threshold_from_item(
            measurement_id=measurement.id,
            item_id=aep_item.id,
            parameter=SportParameter.AEP,
        )
        self.threshold_service.set_threshold_from_item(
            measurement_id=measurement.id,
            item_id=anp_item.id,
            parameter="anp",
        )
        zones = self.threshold_service.calculate_zones(measurement.id)

        self.assertEqual(aep.parameter, SportParameter.AEP)
        self.assertEqual(aep.item_time_sec, aep_item.time_sec)
        self.assertEqual(aep_item.sport_parameter, SportParameter.AEP)
        self.assertEqual(zones[0].upper_hr, aep_item.hr)
        self.assertEqual(zones[1].lower_hr, aep_item.hr)
        self.assertEqual(zones[1].upper_hr, anp_item.hr)
        self.assertEqual(self.repository.audit_events[-1].action, "set_threshold")


if __name__ == "__main__":
    unittest.main()
