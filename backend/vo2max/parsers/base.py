from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from vo2max.domain import ImportWarning, MeasurementItem


@dataclass(slots=True)
class ParsedMeasurement:
    items: list[MeasurementItem]
    source_format: str
    source_file: str
    recognized_fields: list[str] = field(default_factory=list)
    ignored_columns: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ImportPreview:
    source_file: str
    source_format: str
    total_rows: int
    parsed_rows: int
    recognized_fields: list[str]
    ignored_columns: list[str]
    warnings: list[ImportWarning] = field(default_factory=list)


@dataclass(slots=True)
class ParserResult:
    measurement: ParsedMeasurement
    preview: ImportPreview


class BaseParser(ABC):
    source_format = "unknown"
    parser_version = "0.1.0"

    @abstractmethod
    def can_parse(self, path: Path) -> bool:
        """Return whether this parser can handle the given file."""

    @abstractmethod
    def parse(self, path: Path, column_mapping: dict[str, str] | None = None) -> ParserResult:
        """Parse a source file into normalized measurement rows."""
