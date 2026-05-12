from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path
from zipfile import ZipFile

from vo2max.services import (
    ClientService,
    ImportService,
    InMemoryRepository,
    MeasurementService,
    ReportService,
    ThresholdService,
)


ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / "samples" / "legacy_omnia_sample.csv"


class ReportServiceTest(unittest.TestCase):
    def test_report_snapshot_html_pdf_and_docx_exports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repository = InMemoryRepository()
            client_service = ClientService(repository)
            measurement_service = MeasurementService(repository, ImportService(Path(tmp_dir) / "raw"))
            threshold_service = ThresholdService(repository)
            report_service = ReportService(repository, Path(tmp_dir) / "reports")

            client = client_service.create_client(first_name="Report", last_name="Client")
            measurement = measurement_service.import_legacy_csv_for_client(
                client_id=client.id,
                source_path=SAMPLE,
                measurement_date=date(2026, 4, 29),
            )
            measurement_service.import_legacy_csv_for_client(
                client_id=client.id,
                source_path=SAMPLE,
                measurement_date=date(2026, 5, 29),
            )
            threshold_service.set_threshold_from_item(
                measurement_id=measurement.id,
                item_id=measurement.items[0].id,
                parameter="aep",
            )

            snapshot = report_service.build_snapshot(measurement.id)
            html = report_service.render_html(measurement.id)
            files = report_service.export_all(measurement.id)

            self.assertEqual(snapshot["client"]["full_name"], "Client Report")
            self.assertEqual(len(snapshot["comparison"]), 2)
            self.assertIn("VO2max / MPK Report", html)
            self.assertIn("AEP", html)
            self.assertIn("Сравнение тестов", html)
            self.assertEqual({file.format for file in files}, {"html", "pdf", "docx"})
            for file in files:
                self.assertTrue(Path(file.path).exists())

            pdf = next(file for file in files if file.format == "pdf")
            self.assertTrue(Path(pdf.path).read_bytes().startswith(b"%PDF-1.4"))

            docx = next(file for file in files if file.format == "docx")
            with ZipFile(docx.path) as archive:
                self.assertIn("word/document.xml", archive.namelist())
                document = archive.read("word/document.xml").decode("utf-8")
            self.assertIn("VO2max / MPK Report", document)
            self.assertIn("Comparison:", document)


if __name__ == "__main__":
    unittest.main()
