"""
CsvParser - COSMED OMNIA CSV Format Parser

Parses CSV files from COSMED OMNIA gas analyzer.
Key characteristics:
- Comma as decimal separator ("22,53" = 22.53)
- Quoted numeric values
- Header row with column names like "VO2[mL/kg/min]"

DOCUMENTATION:
    Spec: implementation_plan.md
    Sample: doc/исходные.csv
    Legacy: C# MeasurementItemMap in MeasurementItem.cs
"""
import csv
from pathlib import Path
from typing import Dict, Any

from core.parsers.base import BaseParser, ParsedItem, ParsedMeasurement


class CsvParser(BaseParser):
    """
    Parser for COSMED OMNIA CSV format.
    
    Handles the specific quirks of OMNIA exports:
    - European decimal format (comma separator)
    - Time in both seconds and HH:MM:SS
    - Various optional columns
    """
    
    # Column mapping from OMNIA headers to ParsedItem fields
    # Based on C# MeasurementItemMap
    COLUMN_MAP: Dict[str, str] = {
        'Time[s]': 'time_sec',
        'VO2[mL/kg/min]': 'vo2_ml_kg_min',
        'VO2[mL/min]': 'vo2_ml_min',
        'HR[bpm]': 'hr',
        'Power[watts]': 'power',
        'Rf[bpm]': 'rf',
        'Tv[L]': 'tv',
        'Ve[L/min]': 've',
        'RPM[rpm]': 'rpm',
        'Ve/VO2': 've_vo2',
        'FeO2[%]': 'feo2',
        'Temp[C]': 'temp',
        'HUM[%RH]': 'hum',
    }
    
    # Fields that should be parsed as integers
    INT_FIELDS = {'hr'}
    
    @classmethod
    def can_parse(cls, file_path: str) -> bool:
        """Check if file is a CSV with OMNIA-style headers."""
        path = Path(file_path)
        if not path.suffix.lower() == '.csv':
            return False
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                first_line = f.readline()
                # Check for characteristic OMNIA column names
                return 'VO2[mL' in first_line or 'Time[s]' in first_line
        except Exception:
            return False
    
    def parse(self, file_path: str) -> ParsedMeasurement:
        """
        Parse OMNIA CSV file to normalized format.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            ParsedMeasurement with all data points
        """
        path = Path(file_path)
        items = []
        
        with open(path, 'r', encoding='utf-8') as f:
            # Read header to build column index
            header_line = f.readline().strip()
            headers = self._parse_header(header_line)
            
            # Map header indices to our field names
            col_indices = {}
            for idx, header in enumerate(headers):
                if header in self.COLUMN_MAP:
                    col_indices[idx] = self.COLUMN_MAP[header]
            
            # Parse data rows
            for line in f:
                line = line.strip()
                if not line:
                    continue
                    
                values = self._parse_row(line)
                item = self._build_item(values, col_indices)
                if item is not None:
                    items.append(item)
        
        return ParsedMeasurement(
            items=items,
            source_format='OMNIA_CSV',
            source_file=path.name
        )
    
    def _parse_header(self, header_line: str) -> list:
        """Parse CSV header, handling potential BOM and whitespace."""
        # Remove BOM if present
        if header_line.startswith('\ufeff'):
            header_line = header_line[1:]
        
        # Split by comma, preserving quoted content
        reader = csv.reader([header_line])
        return next(reader)
    
    def _parse_row(self, line: str) -> list:
        """Parse CSV data row, handling quoted comma-decimals."""
        reader = csv.reader([line])
        return next(reader)
    
    def _build_item(self, values: list, col_indices: Dict[int, str]) -> ParsedItem | None:
        """
        Build ParsedItem from row values.
        
        Args:
            values: List of string values from CSV row
            col_indices: Mapping of column index to field name
            
        Returns:
            ParsedItem or None if row is invalid
        """
        try:
            kwargs = {}
            
            for idx, field_name in col_indices.items():
                if idx >= len(values):
                    continue
                    
                raw_value = values[idx]
                if not raw_value or raw_value.strip() == '':
                    continue
                
                # Parse numeric value with comma decimal
                parsed = self._parse_decimal_comma(raw_value)
                
                # Convert to int if needed
                if field_name in self.INT_FIELDS:
                    parsed = int(parsed)
                    
                kwargs[field_name] = parsed
            
            # time_sec is required
            if 'time_sec' not in kwargs:
                return None
                
            return ParsedItem(**kwargs)
            
        except (ValueError, TypeError) as e:
            # Skip malformed rows
            return None
