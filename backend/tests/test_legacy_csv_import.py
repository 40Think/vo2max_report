from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from vo2max.domain import Measurement
from vo2max.parsers import LegacyCsvParser
from vo2max.services import ImportService


ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / "samples" / "legacy_omnia_sample.csv"


class LegacyCsvImportTest(unittest.TestCase):
    def test_parser_reads_legacy_csv(self) -> None:
        parser = LegacyCsvParser()

        self.assertTrue(parser.can_parse(SAMPLE))

        result = parser.parse(SAMPLE)

        self.assertEqual(result.preview.total_rows, 3)
        self.assertEqual(result.preview.parsed_rows, 3)
        self.assertIn("time_sec", result.preview.recognized_fields)
        self.assertIn("vo2_ml_min", result.preview.recognized_fields)
        self.assertEqual(result.measurement.items[0].time_sec, 30.0)
        self.assertEqual(result.measurement.items[0].hr, 113.3)
        self.assertEqual(result.measurement.items[0].time_label, "00:00:30")

    def test_measurement_infers_and_updates_rated_power(self) -> None:
        result = LegacyCsvParser().parse(SAMPLE)
        measurement = Measurement(
            client_id="client-1",
            measurement_date=__import__("datetime").date.today(),
            items=result.measurement.items,
        )

        measurement.infer_power_parameters(round_to=10)

        self.assertEqual(measurement.start_power, 100)
        self.assertEqual(measurement.power_step, 20)
        self.assertEqual([item.rated_power for item in measurement.items], [100, 120, 140])

    def test_import_service_stores_raw_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            service = ImportService(tmp_dir)
            raw_file = service.store_raw_file(SAMPLE, parser_version=LegacyCsvParser.parser_version)

            self.assertEqual(raw_file.original_name, SAMPLE.name)
            self.assertTrue(Path(raw_file.stored_path).exists())
            self.assertEqual(raw_file.parser_version, "0.1.0")

    def test_parser_reports_empty_csv_as_missing_time_column(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "empty.csv"
            path.write_text("", encoding="utf-8")

            result = LegacyCsvParser().parse(path)

            self.assertEqual(result.preview.total_rows, 0)
            self.assertEqual(result.preview.parsed_rows, 0)
            self.assertTrue(any(warning.level == "error" for warning in result.preview.warnings))

    def test_parser_skips_rows_without_time_column(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "missing_time.csv"
            path.write_text("HR[bpm],Power[watts]\n120,100\n", encoding="utf-8")

            result = LegacyCsvParser().parse(path)

            self.assertEqual(result.preview.total_rows, 1)
            self.assertEqual(result.preview.parsed_rows, 0)
            self.assertTrue(any(warning.field == "time_sec" for warning in result.preview.warnings))

    def test_parser_marks_bad_numeric_value_but_keeps_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "bad_numeric.csv"
            path.write_text("Time[s],HR[bpm],Power[watts]\n30,not-a-number,100\n", encoding="utf-8")

            result = LegacyCsvParser().parse(path)

            self.assertEqual(result.preview.total_rows, 1)
            self.assertEqual(result.preview.parsed_rows, 1)
            self.assertEqual(result.measurement.items[0].quality_flags, ["invalid_hr"])
            self.assertTrue(any(warning.field == "hr" for warning in result.preview.warnings))

    def test_import_service_rejects_unknown_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "data.txt"
            path.write_text("not a csv", encoding="utf-8")

            with self.assertRaises(ValueError):
                ImportService(tmp_dir).preview(path)


if __name__ == "__main__":
    unittest.main()
