from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

from vo2max.domain import Client, Measurement, Threshold
from vo2max.services.chart_service import ChartService
from vo2max.services.repository import InMemoryRepository
from vo2max.services.threshold_service import ThresholdService


@dataclass(slots=True)
class ReportFile:
    format: str
    path: str
    filename: str
    content_type: str


class ReportService:
    DEFAULT_DOCX_TEMPLATE = [
        "VO2max / MPK Report",
        "Client: {{client.full_name}}",
        "Date: {{measurement.date}}",
        "Activity: {{measurement.activity_type}}",
        "Thresholds:",
        "{{threshold_lines}}",
        "Zones:",
        "{{zone_lines}}",
        "Comparison:",
        "{{comparison_lines}}",
        "Measurement table:",
        "{{table_lines}}",
    ]

    def __init__(self, repository: InMemoryRepository, output_dir: Path | str):
        self.repository = repository
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.threshold_service = ThresholdService(repository)
        self.chart_service = ChartService(repository)

    def build_snapshot(self, measurement_id: str) -> dict[str, Any]:
        measurement = self.repository.get_measurement(measurement_id)
        client = self.repository.get_client(measurement.client_id)
        thresholds = self.repository.list_thresholds_for_measurement(measurement_id)
        zones = self.threshold_service.calculate_zones(measurement_id)
        charts = self.chart_service.build_measurement_charts(measurement_id)
        comparison = self.chart_service.build_client_comparison(client.id, measurement_id)
        return {
            "client": self._client(client),
            "measurement": self._measurement(measurement),
            "thresholds": [self.threshold_service.threshold_to_dict(threshold) for threshold in thresholds],
            "zones": [self.threshold_service.zone_to_dict(zone) for zone in zones],
            "table": [self._row(row) for row in measurement.items],
            "charts": {
                metric: [
                    {
                        "measurement_id": series.measurement_id,
                        "label": series.label,
                        "metric": series.metric,
                        "points": [
                            {
                                "item_id": point.item_id,
                                "x": point.x,
                                "y": point.y,
                                "time_label": point.time_label,
                            }
                            for point in series.points
                        ],
                    }
                    for series in series_list
                ]
                for metric, series_list in charts.charts.items()
            },
            "comparison": self._comparison(measurement),
            "generated_at": datetime.now(UTC).isoformat(),
        }

    def render_html(self, measurement_id: str) -> str:
        snapshot = self.build_snapshot(measurement_id)
        rows = "\n".join(
            "<tr>"
            f"<td>{escape(str(row['time_label'] or row['time_sec']))}</td>"
            f"<td>{self._fmt(row['rated_power'])}</td>"
            f"<td>{self._fmt(row['power'])}</td>"
            f"<td>{self._fmt(row['hr'])}</td>"
            f"<td>{self._fmt(row['vo2_ml_kg_min'])}</td>"
            f"<td>{self._fmt(row['ve'])}</td>"
            f"<td>{self._fmt(row['lactate'])}</td>"
            f"<td>{escape(str(row['sport_parameter'] or ''))}</td>"
            "</tr>"
            for row in snapshot["table"]
            if row["use_in_report"]
        )
        thresholds = "\n".join(
            "<li>"
            f"{escape(threshold['parameter'].upper())}: "
            f"HR {self._fmt(threshold['hr'])}, "
            f"W {self._fmt(threshold['power'])}, "
            f"VO2 {self._fmt(threshold['vo2_ml_min'])}"
            "</li>"
            for threshold in snapshot["thresholds"]
        ) or "<li>Пороги не назначены</li>"
        zones = "\n".join(
            "<li>"
            f"{escape(zone['name'])}: "
            f"HR {self._range(zone['lower_hr'], zone['upper_hr'])}, "
            f"W {self._range(zone['lower_power'], zone['upper_power'])}"
            "</li>"
            for zone in snapshot["zones"]
        )
        charts = self._render_svg_chart(snapshot["charts"].get("hr", []), "ЧСС")
        charts += self._render_svg_chart(snapshot["charts"].get("oxygen", []), "VO2")
        comparison_rows = "\n".join(
            "<tr>"
            f"<td>{escape(item['date'])}</td>"
            f"<td>{self._fmt(item['max_hr'])}</td>"
            f"<td>{self._fmt(item['max_power'])}</td>"
            f"<td>{self._fmt(item['max_vo2'])}</td>"
            f"<td>{item['rows_count']}</td>"
            "</tr>"
            for item in snapshot["comparison"]
        )

        client = snapshot["client"]
        measurement = snapshot["measurement"]
        return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>VO2max Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; color: #172033; margin: 32px; }}
    h1, h2 {{ margin-bottom: 8px; }}
    .muted {{ color: #65738a; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 12px; font-size: 12px; }}
    th, td {{ border: 1px solid #d9e0ea; padding: 6px; text-align: left; }}
    th {{ background: #f0f4f8; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }}
    .chart {{ border: 1px solid #d9e0ea; margin: 12px 0; padding: 8px; }}
  </style>
</head>
<body>
  <h1>VO2max / MPK Report</h1>
  <p class="muted">Клиент: {escape(client['full_name'])}</p>
  <p class="muted">Дата теста: {escape(measurement['date'])} · Активность: {escape(measurement['activity_type'])}</p>

  <div class="grid">
    <section>
      <h2>Пороги</h2>
      <ul>{thresholds}</ul>
    </section>
    <section>
      <h2>Зоны</h2>
      <ul>{zones}</ul>
    </section>
  </div>

  <h2>Графики</h2>
  {charts}

  <h2>Сравнение тестов</h2>
  <table>
    <thead><tr><th>Дата</th><th>Max HR</th><th>Max Power</th><th>Max VO2</th><th>Строк</th></tr></thead>
    <tbody>{comparison_rows}</tbody>
  </table>

  <h2>Таблица измерений</h2>
  <table>
    <thead><tr><th>Время</th><th>Rated W</th><th>Power</th><th>HR</th><th>VO2</th><th>Ve</th><th>Лактат</th><th>Точка</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</body>
</html>"""

    def export_html(self, measurement_id: str) -> ReportFile:
        filename = self._filename(measurement_id, "html")
        path = self.output_dir / filename
        path.write_text(self.render_html(measurement_id), encoding="utf-8")
        return ReportFile("html", str(path), filename, "text/html; charset=utf-8")

    def export_docx(self, measurement_id: str) -> ReportFile:
        snapshot = self.build_snapshot(measurement_id)
        filename = self._filename(measurement_id, "docx")
        path = self.output_dir / filename
        paragraphs = self._render_docx_template(snapshot)
        document_xml = self._docx_document_xml(paragraphs)
        with ZipFile(path, "w", ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", self._docx_content_types())
            archive.writestr("_rels/.rels", self._docx_rels())
            archive.writestr("word/document.xml", document_xml)
        return ReportFile(
            "docx",
            str(path),
            filename,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    def export_pdf(self, measurement_id: str) -> ReportFile:
        snapshot = self.build_snapshot(measurement_id)
        filename = self._filename(measurement_id, "pdf")
        path = self.output_dir / filename
        lines = self._plain_report_lines(snapshot)
        path.write_bytes(self._minimal_pdf(lines))
        return ReportFile("pdf", str(path), filename, "application/pdf")

    def export_all(self, measurement_id: str) -> list[ReportFile]:
        return [
            self.export_html(measurement_id),
            self.export_pdf(measurement_id),
            self.export_docx(measurement_id),
        ]

    def _client(self, client: Client) -> dict[str, Any]:
        return {
            "id": client.id,
            "full_name": client.full_name,
            "height_cm": client.height_cm,
            "weight_kg": client.weight_kg,
        }

    def _measurement(self, measurement: Measurement) -> dict[str, Any]:
        return {
            "id": measurement.id,
            "date": measurement.measurement_date.isoformat(),
            "activity_type": measurement.activity_type.value,
            "title": measurement.title,
            "start_power": measurement.start_power,
            "power_step": measurement.power_step,
        }

    def _row(self, row) -> dict[str, Any]:
        return {
            "id": row.id,
            "time_sec": row.time_sec,
            "time_label": row.time_label,
            "rated_power": row.rated_power,
            "power": row.power,
            "hr": row.hr,
            "vo2_ml_kg_min": row.vo2_ml_kg_min,
            "vo2_ml_min": row.vo2_ml_min,
            "ve": row.ve,
            "lactate": row.lactate,
            "sport_parameter": row.sport_parameter.value if row.sport_parameter else None,
            "use_in_report": row.use_in_report,
        }

    def _comparison(self, active: Measurement) -> list[dict[str, Any]]:
        measurements = self.repository.list_measurements_for_client(active.client_id)
        comparison_rows: list[dict[str, Any]] = []
        for measurement in measurements:
            hr_values = [item.hr for item in measurement.items if item.hr is not None]
            power_values = [item.power for item in measurement.items if item.power is not None]
            vo2_values = [item.vo2_ml_kg_min for item in measurement.items if item.vo2_ml_kg_min is not None]
            comparison_rows.append(
                {
                    "measurement_id": measurement.id,
                    "date": measurement.measurement_date.isoformat(),
                    "is_active": measurement.id == active.id,
                    "max_hr": max(hr_values) if hr_values else None,
                    "max_power": max(power_values) if power_values else None,
                    "max_vo2": max(vo2_values) if vo2_values else None,
                    "rows_count": len(measurement.items),
                }
            )
        return comparison_rows

    def _render_svg_chart(self, series_list: list[dict[str, Any]], title: str) -> str:
        series = next((item for item in series_list if item["points"]), None)
        if not series:
            return f"<div class=\"chart\"><strong>{escape(title)}</strong><p class=\"muted\">Нет данных</p></div>"
        points = series["points"]
        width, height = 620, 180
        pad_left, pad_bottom, pad_top, pad_right = 42, 24, 14, 12
        xs = [point["x"] for point in points]
        ys = [point["y"] for point in points]
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        y_pad = max(1, (y_max - y_min) * 0.1)
        y_min -= y_pad
        y_max += y_pad

        def sx(x):
            return pad_left + ((x - x_min) / max(1, x_max - x_min)) * (width - pad_left - pad_right)

        def sy(y):
            return height - pad_bottom - ((y - y_min) / max(1, y_max - y_min)) * (height - pad_top - pad_bottom)

        polyline = " ".join(f"{sx(point['x']):.1f},{sy(point['y']):.1f}" for point in points)
        return f"""<div class="chart">
  <strong>{escape(title)}</strong>
  <svg viewBox="0 0 {width} {height}" width="100%" height="180" role="img">
    <line x1="{pad_left}" y1="{height - pad_bottom}" x2="{width - pad_right}" y2="{height - pad_bottom}" stroke="#d9e0ea" />
    <line x1="{pad_left}" y1="{pad_top}" x2="{pad_left}" y2="{height - pad_bottom}" stroke="#d9e0ea" />
    <polyline points="{polyline}" fill="none" stroke="#147c72" stroke-width="2.5" />
  </svg>
</div>"""

    def _render_docx_template(self, snapshot: dict[str, Any]) -> list[str]:
        context = self._template_context(snapshot)
        rendered: list[str] = []
        for template_line in self.DEFAULT_DOCX_TEMPLATE:
            expanded = template_line
            for key, value in context.items():
                expanded = expanded.replace("{{" + key + "}}", value)
            rendered.extend(line for line in expanded.split("\n") if line)
        return rendered

    def _template_context(self, snapshot: dict[str, Any]) -> dict[str, str]:
        return {
            "client.full_name": str(snapshot["client"]["full_name"]),
            "measurement.date": str(snapshot["measurement"]["date"]),
            "measurement.activity_type": str(snapshot["measurement"]["activity_type"]),
            "threshold_lines": "\n".join(self._threshold_lines(snapshot)) or "- not assigned",
            "zone_lines": "\n".join(self._zone_lines(snapshot)),
            "comparison_lines": "\n".join(self._comparison_lines(snapshot)),
            "table_lines": "\n".join(self._table_lines(snapshot)),
        }

    def _plain_report_lines(self, snapshot: dict[str, Any]) -> list[str]:
        client = snapshot["client"]
        measurement = snapshot["measurement"]
        lines = [
            "VO2max / MPK Report",
            f"Client: {client['full_name']}",
            f"Date: {measurement['date']}",
            f"Activity: {measurement['activity_type']}",
            "Thresholds:",
        ]
        if snapshot["thresholds"]:
            for threshold in snapshot["thresholds"]:
                lines.append(
                    f"- {threshold['parameter'].upper()}: HR {self._fmt(threshold['hr'])}, W {self._fmt(threshold['power'])}"
                )
        else:
            lines.append("- not assigned")
        lines.append("Zones:")
        lines.extend(self._zone_lines(snapshot))
        lines.append("Comparison:")
        lines.extend(self._comparison_lines(snapshot))
        return lines

    def _threshold_lines(self, snapshot: dict[str, Any]) -> list[str]:
        return [
            f"- {threshold['parameter'].upper()}: HR {self._fmt(threshold['hr'])}, W {self._fmt(threshold['power'])}"
            for threshold in snapshot["thresholds"]
        ]

    def _zone_lines(self, snapshot: dict[str, Any]) -> list[str]:
        return [
            f"- {zone['name']}: HR {self._range(zone['lower_hr'], zone['upper_hr'])}, W {self._range(zone['lower_power'], zone['upper_power'])}"
            for zone in snapshot["zones"]
        ]

    def _comparison_lines(self, snapshot: dict[str, Any]) -> list[str]:
        return [
            f"- {row['date']}: max HR {self._fmt(row['max_hr'])}, max W {self._fmt(row['max_power'])}, max VO2 {self._fmt(row['max_vo2'])}"
            for row in snapshot["comparison"]
        ]

    def _table_lines(self, snapshot: dict[str, Any]) -> list[str]:
        return [
            f"{row['time_label'] or row['time_sec']} | HR {self._fmt(row['hr'])} | W {self._fmt(row['power'])} | VO2 {self._fmt(row['vo2_ml_kg_min'])}"
            for row in snapshot["table"]
            if row["use_in_report"]
        ]

    def _minimal_pdf(self, lines: list[str]) -> bytes:
        escaped_lines = [line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") for line in lines[:42]]
        text_commands = ["BT", "/F1 11 Tf", "50 790 Td", "14 TL"]
        for index, line in enumerate(escaped_lines):
            if index:
                text_commands.append("T*")
            text_commands.append(f"({line}) Tj")
        text_commands.append("ET")
        stream = "\n".join(text_commands).encode("latin-1", errors="replace")
        objects = [
            b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
            b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
            b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n",
            b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
            b"5 0 obj << /Length " + str(len(stream)).encode("ascii") + b" >> stream\n" + stream + b"\nendstream endobj\n",
        ]
        pdf = b"%PDF-1.4\n"
        offsets = [0]
        for obj in objects:
            offsets.append(len(pdf))
            pdf += obj
        xref_start = len(pdf)
        pdf += f"xref\n0 {len(objects) + 1}\n".encode("ascii")
        pdf += b"0000000000 65535 f \n"
        for offset in offsets[1:]:
            pdf += f"{offset:010d} 00000 n \n".encode("ascii")
        pdf += f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n".encode("ascii")
        return pdf

    def _docx_document_xml(self, paragraphs: list[str]) -> str:
        body = "".join(
            f"<w:p><w:r><w:t>{escape(paragraph)}</w:t></w:r></w:p>"
            for paragraph in paragraphs
        )
        return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>{body}<w:sectPr /></w:body>
</w:document>"""

    def _docx_content_types(self) -> str:
        return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""

    def _docx_rels(self) -> str:
        return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

    def _filename(self, measurement_id: str, extension: str) -> str:
        safe_id = measurement_id.replace("/", "_").replace("\\", "_")
        stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        return f"vo2max_report_{safe_id}_{stamp}.{extension}"

    def _fmt(self, value: Any) -> str:
        if value is None:
            return "-"
        if isinstance(value, float):
            return f"{value:.1f}"
        return str(value)

    def _range(self, lower: Any, upper: Any) -> str:
        if lower is None and upper is None:
            return "-"
        if lower is None:
            return f"< {self._fmt(upper)}"
        if upper is None:
            return f"> {self._fmt(lower)}"
        return f"{self._fmt(lower)}-{self._fmt(upper)}"
