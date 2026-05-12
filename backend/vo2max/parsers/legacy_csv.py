from __future__ import annotations

import csv
from pathlib import Path

from vo2max.domain import ImportWarning, MeasurementItem
from vo2max.parsers.base import BaseParser, ImportPreview, ParsedMeasurement, ParserResult


class LegacyCsvParser(BaseParser):
    """Parser for the legacy CSV format used by the original C# program."""

    source_format = "legacy_csv"
    parser_version = "0.1.0"

    DEFAULT_COLUMN_MAP: dict[str, str] = {
        "Time[s]": "time_sec",
        "Time[hh:mm:ss]": "time_label",
        "VO2[mL/kg/min]": "vo2_ml_kg_min",
        "VO2[mL/min]": "vo2_ml_min",
        "HR[bpm]": "hr",
        "Power[watts]": "power",
        "Rf[bpm]": "rf",
        "Tv[L]": "tv",
        "Ve[L/min]": "ve",
        "RPM[rpm]": "rpm",
        "Ve/VO2": "ve_vo2",
        "FeO2[%]": "feo2",
        "Temp[C]": "temp",
        "HUM[%RH]": "hum",
    }

    NUMERIC_FIELDS = {
        "time_sec",
        "vo2_ml_kg_min",
        "vo2_ml_min",
        "vco2_ml_min",
        "hr",
        "power",
        "rated_power",
        "rf",
        "tv",
        "ve",
        "rpm",
        "ve_vo2",
        "feo2",
        "rer",
        "temp",
        "hum",
        "lactate",
    }

    def can_parse(self, path: Path) -> bool:
        if path.suffix.lower() != ".csv":
            return False

        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                first_line = handle.readline()
        except UnicodeDecodeError:
            with path.open("r", encoding="cp1251", newline="") as handle:
                first_line = handle.readline()

        return "Time[s]" in first_line or "VO2[mL" in first_line

    def parse(self, path: Path, column_mapping: dict[str, str] | None = None) -> ParserResult:
        mapping = dict(self.DEFAULT_COLUMN_MAP)
        if column_mapping:
            mapping.update(column_mapping)

        warnings: list[ImportWarning] = []
        items: list[MeasurementItem] = []
        total_rows = 0

        with self._open_text(path) as handle:
            reader = csv.DictReader(handle)
            headers = reader.fieldnames or []
            normalized_headers = [header.strip() for header in headers if header]
            recognized_fields = [
                mapping[header]
                for header in normalized_headers
                if header in mapping
            ]
            ignored_columns = [
                header
                for header in normalized_headers
                if header not in mapping
            ]

            has_time_column = any(
                header in mapping and mapping[header] == "time_sec"
                for header in normalized_headers
            )
            if not has_time_column:
                warnings.append(ImportWarning(level="error", message="Required time column was not found"))

            for row_number, row in enumerate(reader, start=2):
                total_rows += 1
                item = self._parse_row(row, mapping, row_number, warnings)
                if item is not None:
                    items.append(item)

        parsed = ParsedMeasurement(
            items=items,
            source_format=self.source_format,
            source_file=path.name,
            recognized_fields=sorted(set(recognized_fields)),
            ignored_columns=ignored_columns,
        )
        preview = ImportPreview(
            source_file=path.name,
            source_format=self.source_format,
            total_rows=total_rows,
            parsed_rows=len(items),
            recognized_fields=parsed.recognized_fields,
            ignored_columns=ignored_columns,
            warnings=warnings,
        )
        return ParserResult(measurement=parsed, preview=preview)

    def _parse_row(
        self,
        row: dict[str, str],
        mapping: dict[str, str],
        row_number: int,
        warnings: list[ImportWarning],
    ) -> MeasurementItem | None:
        values: dict[str, object] = {}
        source_fields: dict[str, str] = {}
        quality_flags: list[str] = []

        for source_column, target_field in mapping.items():
            if source_column not in row:
                continue

            raw_value = (row.get(source_column) or "").strip()
            if raw_value == "":
                continue

            source_fields[source_column] = raw_value
            if target_field in self.NUMERIC_FIELDS:
                parsed = self._parse_float(raw_value)
                if parsed is None:
                    warnings.append(
                        ImportWarning(
                            level="warning",
                            message=f"Could not parse numeric value '{raw_value}'",
                            row_number=row_number,
                            field=target_field,
                        )
                    )
                    quality_flags.append(f"invalid_{target_field}")
                    continue
                values[target_field] = parsed
            else:
                values[target_field] = raw_value

        if "time_sec" not in values:
            warnings.append(
                ImportWarning(
                    level="warning",
                    message="Skipped row without time_sec",
                    row_number=row_number,
                    field="time_sec",
                )
            )
            return None

        item = MeasurementItem(
            time_sec=float(values["time_sec"]),
            time_label=self._optional_str(values.get("time_label")),
            vo2_ml_kg_min=self._optional_float(values.get("vo2_ml_kg_min")),
            vo2_ml_min=self._optional_float(values.get("vo2_ml_min")),
            vco2_ml_min=self._optional_float(values.get("vco2_ml_min")),
            hr=self._optional_float(values.get("hr")),
            power=self._optional_float(values.get("power")),
            rated_power=self._optional_int(values.get("rated_power")),
            rf=self._optional_float(values.get("rf")),
            tv=self._optional_float(values.get("tv")),
            ve=self._optional_float(values.get("ve")),
            rpm=self._optional_float(values.get("rpm")),
            ve_vo2=self._optional_float(values.get("ve_vo2")),
            feo2=self._optional_float(values.get("feo2")),
            rer=self._optional_float(values.get("rer")),
            temp=self._optional_float(values.get("temp")),
            hum=self._optional_float(values.get("hum")),
            lactate=self._optional_float(values.get("lactate")),
        )
        item.source_fields = source_fields
        item.quality_flags = quality_flags
        return item

    def _parse_float(self, value: str) -> float | None:
        cleaned = value.strip().replace(" ", "").replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return None

    def _optional_float(self, value: object) -> float | None:
        if value is None:
            return None
        return float(value)

    def _optional_int(self, value: object) -> int | None:
        if value is None:
            return None
        return int(value)

    def _optional_str(self, value: object) -> str | None:
        if value is None:
            return None
        return str(value)

    def _open_text(self, path: Path):
        try:
            path.read_text(encoding="utf-8-sig")
            return path.open("r", encoding="utf-8-sig", newline="")
        except UnicodeDecodeError:
            return path.open("r", encoding="cp1251", newline="")
