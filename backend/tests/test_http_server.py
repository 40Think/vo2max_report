from __future__ import annotations

import json
import tempfile
import threading
import unittest
import base64
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from vo2max.api.server import create_handler


ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / "samples" / "legacy_omnia_sample.csv"


class HttpServerSmokeTest(unittest.TestCase):
    def test_server_health_frontend_client_import_and_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            server = ThreadingHTTPServer(("127.0.0.1", 0), create_handler(tmp_dir))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_port}"

            try:
                with urlopen(f"{base_url}/health", timeout=5) as response:
                    health = json.loads(response.read().decode("utf-8"))

                with urlopen(f"{base_url}/", timeout=5) as response:
                    html = response.read().decode("utf-8")

                with urlopen(f"{base_url}/static/app.js", timeout=5) as response:
                    app_js = response.read().decode("utf-8")

                payload = json.dumps({"first_name": "Http", "last_name": "Client"}).encode("utf-8")
                request = Request(
                    f"{base_url}/clients",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urlopen(request, timeout=5) as response:
                    client = json.loads(response.read().decode("utf-8"))

                payload = json.dumps(
                    {
                        "source_path": str(SAMPLE),
                        "measurement_date": "2026-04-29",
                        "activity_type": "cycling",
                    }
                ).encode("utf-8")
                request = Request(
                    f"{base_url}/clients/{client['id']}/measurements",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urlopen(request, timeout=5) as response:
                    measurement = json.loads(response.read().decode("utf-8"))

                payload = json.dumps(
                    {
                        "filename": "uploaded.csv",
                        "content_base64": base64.b64encode(SAMPLE.read_bytes()).decode("ascii"),
                        "measurement_date": "2026-04-30",
                        "activity_type": "cycling",
                    }
                ).encode("utf-8")
                request = Request(
                    f"{base_url}/clients/{client['id']}/measurements/upload",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urlopen(request, timeout=5) as response:
                    uploaded_measurement = json.loads(response.read().decode("utf-8"))

                payload = json.dumps(
                    {
                        "measurement_date": "2026-04-30",
                        "activity_type": "cycling",
                        "title": "Manual test",
                    }
                ).encode("utf-8")
                request = Request(
                    f"{base_url}/clients/{client['id']}/measurements/manual",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urlopen(request, timeout=5) as response:
                    manual_measurement = json.loads(response.read().decode("utf-8"))

                payload = json.dumps(
                    {
                        "time_sec": 60,
                        "power": 150,
                        "hr": 136,
                        "vo2_ml_kg_min": 35.5,
                    }
                ).encode("utf-8")
                request = Request(
                    f"{base_url}/measurements/{manual_measurement['id']}/items",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urlopen(request, timeout=5) as response:
                    manual_item = json.loads(response.read().decode("utf-8"))

                with urlopen(
                    f"{base_url}/clients/{client['id']}/measurements/{measurement['id']}",
                    timeout=5,
                ) as response:
                    workspace = json.loads(response.read().decode("utf-8"))

                payload = json.dumps(
                    {
                        "item_id": workspace["table_rows"][0]["id"],
                        "parameter": "aep",
                    }
                ).encode("utf-8")
                request = Request(
                    f"{base_url}/measurements/{measurement['id']}/thresholds",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urlopen(request, timeout=5) as response:
                    threshold = json.loads(response.read().decode("utf-8"))

                with urlopen(
                    f"{base_url}/clients/{client['id']}/measurements/{measurement['id']}/charts",
                    timeout=5,
                ) as response:
                    charts = json.loads(response.read().decode("utf-8"))

                with urlopen(f"{base_url}/measurements/{measurement['id']}/zones", timeout=5) as response:
                    zones = json.loads(response.read().decode("utf-8"))

                with urlopen(f"{base_url}/measurements/{measurement['id']}/report-preview", timeout=5) as response:
                    report_preview = response.read().decode("utf-8")

                request = Request(
                    f"{base_url}/measurements/{measurement['id']}/reports",
                    data=b"{}",
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urlopen(request, timeout=5) as response:
                    reports = json.loads(response.read().decode("utf-8"))

                html_report = next(file for file in reports["files"] if file["format"] == "html")
                with urlopen(f"{base_url}{html_report['download_url']}", timeout=5) as response:
                    downloaded_report = response.read().decode("utf-8")

                bad_request = Request(
                    f"{base_url}/clients/{client['id']}/measurements/upload",
                    data=json.dumps({"filename": "bad.csv", "content_base64": "not-base64"}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                try:
                    urlopen(bad_request, timeout=5)
                    bad_status = None
                except HTTPError as exc:
                    bad_status = exc.code

                try:
                    urlopen(f"{base_url}/clients/not-found", timeout=5)
                    not_found_status = None
                except HTTPError as exc:
                    not_found_status = exc.code
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

        self.assertEqual(health, {"status": "ok"})
        self.assertIn("VO2max / MPK Report", html)
        self.assertIn("renderCharts", app_js)
        self.assertIn("generateReports", app_js)
        self.assertIn("uploadTest", app_js)
        self.assertEqual(client["full_name"], "Client Http")
        self.assertEqual(measurement["items_count"], 3)
        self.assertEqual(uploaded_measurement["items_count"], 3)
        self.assertEqual(manual_measurement["items_count"], 0)
        self.assertEqual(manual_item["time_label"], "01:00")
        self.assertEqual(manual_item["hr"], 136.0)
        self.assertEqual(workspace["table_rows"][0]["hr"], 113.3)
        self.assertEqual(threshold["parameter"], "aep")
        active_hr_series = next(
            series for series in charts["charts"]["hr"] if series["measurement_id"] == measurement["id"]
        )
        self.assertEqual(active_hr_series["points"][0]["y"], 113.3)
        self.assertEqual(zones[0]["upper_hr"], 113.3)
        self.assertIn("VO2max / MPK Report", report_preview)
        self.assertEqual({file["format"] for file in reports["files"]}, {"html", "pdf", "docx"})
        self.assertIn("VO2max / MPK Report", downloaded_report)
        self.assertEqual(bad_status, 400)
        self.assertEqual(not_found_status, 404)


if __name__ == "__main__":
    unittest.main()
