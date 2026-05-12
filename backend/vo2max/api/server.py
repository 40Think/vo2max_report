from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from vo2max.api.application import create_application_api
from vo2max.services import EntityNotFoundError


def create_handler(raw_storage_dir: Path | str):
    raw_storage_dir = Path(raw_storage_dir)
    api = create_application_api(raw_storage_dir)
    frontend_root = Path(__file__).resolve().parents[3] / "frontend"
    report_root = raw_storage_dir.parent / "reports"

    class Vo2maxRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self._safe_handle(self._handle_get)

        def do_POST(self) -> None:
            self._safe_handle(self._handle_post)

        def do_PATCH(self) -> None:
            self._safe_handle(self._handle_patch)

        def _handle_get(self) -> None:
            parsed = urlparse(self.path)
            parts = [part for part in parsed.path.split("/") if part]
            query = parse_qs(parsed.query)

            if parts == []:
                self._send_file(frontend_root / "index.html", "text/html; charset=utf-8")
                return

            if len(parts) == 2 and parts[0] == "static":
                self._send_static(parts[1])
                return

            if parts == ["health"]:
                self._send_json({"status": "ok"})
                return

            if parts == ["clients"]:
                self._send_json(api.list_clients(query.get("query", [""])[0]))
                return

            if len(parts) == 2 and parts[0] == "clients":
                self._send_json(api.get_client_profile(parts[1]))
                return

            if len(parts) == 4 and parts[0] == "clients" and parts[2] == "measurements":
                self._send_json(api.get_workspace(parts[1], parts[3]))
                return

            if len(parts) == 5 and parts[0] == "clients" and parts[2] == "measurements" and parts[4] == "charts":
                self._send_json(api.get_charts(parts[1], parts[3]))
                return

            if len(parts) == 3 and parts[0] == "measurements" and parts[2] == "thresholds":
                self._send_json(api.list_thresholds(parts[1]))
                return

            if len(parts) == 3 and parts[0] == "measurements" and parts[2] == "zones":
                self._send_json(api.get_training_zones(parts[1]))
                return

            if len(parts) == 3 and parts[0] == "measurements" and parts[2] == "report-preview":
                self._send_html(api.preview_report_html(parts[1]))
                return

            if len(parts) == 2 and parts[0] == "reports":
                self._send_report_file(parts[1])
                return

            self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)

        def _handle_post(self) -> None:
            parsed = urlparse(self.path)
            parts = [part for part in parsed.path.split("/") if part]
            payload = self._read_json()

            if parts == ["clients"]:
                self._send_json(api.create_client(payload), HTTPStatus.CREATED)
                return

            if len(parts) == 3 and parts[0] == "clients" and parts[2] == "measurements":
                self._send_json(api.import_measurement(parts[1], payload), HTTPStatus.CREATED)
                return

            if len(parts) == 4 and parts[0] == "clients" and parts[2] == "measurements" and parts[3] == "upload":
                self._send_json(api.upload_measurement(parts[1], payload), HTTPStatus.CREATED)
                return

            if len(parts) == 4 and parts[0] == "clients" and parts[2] == "measurements" and parts[3] == "manual":
                self._send_json(api.create_manual_measurement(parts[1], payload), HTTPStatus.CREATED)
                return

            if len(parts) == 3 and parts[0] == "measurements" and parts[2] == "items":
                self._send_json(api.add_manual_measurement_item(parts[1], payload), HTTPStatus.CREATED)
                return

            if len(parts) == 3 and parts[0] == "measurements" and parts[2] == "sampling":
                self._send_json(api.apply_row_sampling(parts[1], payload))
                return

            if len(parts) == 3 and parts[0] == "measurements" and parts[2] == "thresholds":
                self._send_json(api.set_threshold(parts[1], payload), HTTPStatus.CREATED)
                return

            if len(parts) == 3 and parts[0] == "measurements" and parts[2] == "reports":
                self._send_json(api.generate_reports(parts[1]), HTTPStatus.CREATED)
                return

            self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)

        def _handle_patch(self) -> None:
            parsed = urlparse(self.path)
            parts = [part for part in parsed.path.split("/") if part]
            payload = self._read_json()

            if len(parts) == 2 and parts[0] == "clients":
                self._send_json(api.update_client(parts[1], payload))
                return

            if len(parts) == 3 and parts[0] == "measurements" and parts[2] == "power":
                self._send_json(api.update_power_parameters(parts[1], payload))
                return

            if len(parts) == 4 and parts[0] == "measurements" and parts[2] == "items":
                self._send_json(api.update_measurement_item(parts[1], parts[3], payload))
                return

            self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)

        def _safe_handle(self, handler) -> None:
            try:
                handler()
            except EntityNotFoundError as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
            except (ValueError, KeyError, json.JSONDecodeError) as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            except TypeError as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            except Exception as exc:
                self._send_json({"error": "Internal server error", "detail": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)

        def _read_json(self) -> dict:
            length = int(self.headers.get("Content-Length", "0"))
            if length == 0:
                return {}
            raw_body = self.rfile.read(length).decode("utf-8")
            return json.loads(raw_body)

        def _send_json(self, payload, status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status.value)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_html(self, html: str) -> None:
            body = html.encode("utf-8")
            self.send_response(HTTPStatus.OK.value)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_static(self, name: str) -> None:
            if name.endswith(".js"):
                content_type = "text/javascript; charset=utf-8"
            elif name.endswith(".css"):
                content_type = "text/css; charset=utf-8"
            else:
                self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
                return
            self._send_file(frontend_root / name, content_type)

        def _send_file(self, path: Path, content_type: str) -> None:
            if not path.exists() or path.parent != frontend_root:
                self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
                return
            body = path.read_bytes()
            self.send_response(HTTPStatus.OK.value)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_report_file(self, name: str) -> None:
            path = report_root / name
            if not path.exists() or path.parent != report_root:
                self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
                return
            if name.endswith(".pdf"):
                content_type = "application/pdf"
            elif name.endswith(".docx"):
                content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif name.endswith(".html"):
                content_type = "text/html; charset=utf-8"
            else:
                content_type = "application/octet-stream"
            body = path.read_bytes()
            self.send_response(HTTPStatus.OK.value)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Disposition", f"attachment; filename={name}")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args) -> None:
            return

    return Vo2maxRequestHandler


def run(host: str = "127.0.0.1", port: int = 8080) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    raw_storage_dir = backend_root.parent / "storage" / "raw_files"
    server = ThreadingHTTPServer((host, port), create_handler(raw_storage_dir))
    print(f"VO2max API listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
