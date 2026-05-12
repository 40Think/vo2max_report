from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from vo2max.domain import RawFile
from vo2max.parsers import ImportPreview, LegacyCsvParser, ParserResult


class ImportService:
    """Coordinates parser selection, preview generation and raw file storage."""

    def __init__(self, raw_storage_dir: Path | str):
        self.raw_storage_dir = Path(raw_storage_dir)
        self.raw_storage_dir.mkdir(parents=True, exist_ok=True)
        self.parsers = [LegacyCsvParser()]

    def preview(self, source_path: Path | str, column_mapping: dict[str, str] | None = None) -> ParserResult:
        path = Path(source_path)
        parser = self._select_parser(path)
        return parser.parse(path, column_mapping=column_mapping)

    def store_raw_file(self, source_path: Path | str, parser_version: str | None = None) -> RawFile:
        path = Path(source_path)
        checksum = self._sha256(path)
        stored_name = f"{checksum[:12]}_{path.name}"
        stored_path = self.raw_storage_dir / stored_name

        if not stored_path.exists():
            shutil.copy2(path, stored_path)

        return RawFile(
            original_name=path.name,
            stored_path=str(stored_path),
            checksum=checksum,
            parser_version=parser_version,
        )

    def build_import_preview(self, source_path: Path | str) -> ImportPreview:
        return self.preview(source_path).preview

    def _select_parser(self, path: Path):
        for parser in self.parsers:
            if parser.can_parse(path):
                return parser
        raise ValueError(f"No parser available for file: {path}")

    def _sha256(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

