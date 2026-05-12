from __future__ import annotations

import tempfile
import unittest
import base64
from datetime import date
from pathlib import Path

from vo2max.api import create_application_api


ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / "samples" / "legacy_omnia_sample.csv"


class ApplicationApiTest(unittest.TestCase):
    def test_api_flow_from_client_to_workspace_and_edit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            api = create_application_api(tmp_dir)
            client = api.create_client({"first_name": "Api", "last_name": "Client"})
            measurement = api.import_measurement(
                client["id"],
                {
                    "source_path": str(SAMPLE),
                    "measurement_date": date(2026, 4, 29).isoformat(),
                    "activity_type": "cycling",
                    "title": "API import",
                },
            )
            workspace = api.get_workspace(client["id"], measurement["id"])
            first_row = workspace["table_rows"][0]

            updated_row = api.update_measurement_item(
                measurement["id"],
                first_row["id"],
                {"hr": 119.0, "changed_by": "api-test"},
            )
            api.apply_row_sampling(measurement["id"], {"every_n": 2})

            updated_workspace = api.get_workspace(client["id"], measurement["id"])
            threshold = api.set_threshold(
                measurement["id"],
                {
                    "item_id": updated_workspace["table_rows"][0]["id"],
                    "parameter": "aep",
                },
            )
            charts = api.get_charts(client["id"], measurement["id"])
            zones = api.get_training_zones(measurement["id"])
            preview = api.preview_report_html(measurement["id"])
            reports = api.generate_reports(measurement["id"])
            payload = {"hr": 120.0, "changed_by": "mutation-test"}
            api.update_measurement_item(measurement["id"], first_row["id"], payload)

            self.assertEqual(workspace["client"]["full_name"], "Client Api")
            self.assertEqual(workspace["active_measurement"]["items_count"], 3)
            self.assertEqual(updated_row["hr"], 119.0)
            self.assertEqual(
                [row["use_in_report"] for row in updated_workspace["table_rows"]],
                [True, False, True],
            )
            self.assertEqual(threshold["parameter"], "aep")
            self.assertEqual(charts["charts"]["hr"][0]["points"][0]["y"], 119.0)
            self.assertEqual(zones[0]["upper_hr"], 119.0)
            self.assertIn("VO2max / MPK Report", preview)
            self.assertEqual({file["format"] for file in reports["files"]}, {"html", "pdf", "docx"})
            self.assertEqual(payload["changed_by"], "mutation-test")

    def test_api_upload_measurement_from_base64_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            api = create_application_api(tmp_dir)
            client = api.create_client({"first_name": "Upload", "last_name": "Client"})
            uploaded = api.upload_measurement(
                client["id"],
                {
                    "filename": "uploaded.csv",
                    "content_base64": base64.b64encode(SAMPLE.read_bytes()).decode("ascii"),
                    "measurement_date": "2026-04-29",
                    "activity_type": "cycling",
                },
            )

            self.assertEqual(uploaded["items_count"], 3)

    def test_api_manual_measurement_and_row_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            api = create_application_api(tmp_dir)
            client = api.create_client({"first_name": "Manual", "last_name": "Client"})
            measurement = api.create_manual_measurement(
                client["id"],
                {
                    "measurement_date": "2026-04-30",
                    "activity_type": "cycling",
                    "title": "Manual test",
                },
            )
            item = api.add_manual_measurement_item(
                measurement["id"],
                {
                    "time_sec": 120,
                    "power": 180,
                    "hr": 144,
                    "vo2_ml_kg_min": 41.2,
                    "lactate": 2.1,
                },
            )
            workspace = api.get_workspace(client["id"], measurement["id"])

            self.assertEqual(measurement["items_count"], 0)
            self.assertEqual(item["time_label"], "02:00")
            self.assertEqual(workspace["active_measurement"]["items_count"], 1)
            self.assertEqual(workspace["table_rows"][0]["vo2_ml_kg_min"], 41.2)


if __name__ == "__main__":
    unittest.main()
