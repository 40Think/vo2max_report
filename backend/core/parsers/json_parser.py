"""
JsonParser - Custom JSON Format Parser

Parses JSON files from custom gas analyzer software.
Key characteristics:
- dataMap: array of [time_sec, {metrics}] tuples
- setup: athlete profile and test metadata
- Units: Flow in mL/min, times in seconds

DOCUMENTATION:
    Spec: implementation_plan.md
    Sample: doc/девайсы/T 20191110111405PDLGA001 Фетисова Ирина.json
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from core.parsers.base import BaseParser, ParsedItem, ParsedMeasurement


class JsonParser(BaseParser):
    """
    Parser for custom JSON format with dataMap structure.
    
    Expected JSON structure:
    {
        "dataMap": [[5, {"Flow": 25660, "O2_Flow": 1462, ...}], ...],
        "setup": {"name": "...", "weight": 53, "height": 170, ...},
        "legend": [...]
    }
    """
    
    # Field mapping from JSON keys to ParsedItem fields
    FIELD_MAP: Dict[str, str] = {
        'O2_Flow': 'vo2_ml_min',
        'CO2_Flow': 'vco2_ml_min',
        'Flow': 've_ml',           # Need to convert mL -> L
        'HR': 'hr',
        'Power': 'power',
        'Cadence': 'rpm',
        'R': 'r',
        'HRvar': 'hrv',
        'SD1': 'sd1',
        'SD2': 'sd2',
    }
    
    # Fields that need unit conversion (mL to L)
    ML_TO_L_FIELDS = {'ve_ml'}
    
    # Fields that should be integers
    INT_FIELDS = {'hr', 'hrv'}
    
    @classmethod
    def can_parse(cls, file_path: str) -> bool:
        """Check if file is JSON with dataMap structure."""
        path = Path(file_path)
        if not path.suffix.lower() == '.json':
            return False
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return 'dataMap' in data
        except Exception:
            return False
    
    def parse(self, file_path: str) -> ParsedMeasurement:
        """
        Parse custom JSON file to normalized format.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            ParsedMeasurement with items and client metadata
        """
        path = Path(file_path)
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Parse setup (client metadata)
        setup = data.get('setup', {})
        
        # Parse dataMap (time-series)
        items = []
        for entry in data.get('dataMap', []):
            item = self._parse_data_entry(entry)
            if item is not None:
                items.append(item)
        
        # Build result with metadata
        return ParsedMeasurement(
            items=items,
            client_name=setup.get('name'),
            client_weight=setup.get('weight'),
            client_height=setup.get('height'),
            client_gender=self._normalize_gender(setup.get('sex')),
            client_age=setup.get('age'),
            measurement_date=self._parse_datetime(setup.get('createTS')),
            test_id=setup.get('testID'),
            comment=setup.get('comment'),
            source_format='CUSTOM_JSON',
            source_file=path.name
        )
    
    def _parse_data_entry(self, entry: list) -> ParsedItem | None:
        """
        Parse single dataMap entry.
        
        Entry format: [time_sec, {metric: value, ...}]
        """
        if not isinstance(entry, list) or len(entry) != 2:
            return None
        
        time_sec, metrics = entry
        
        if not isinstance(metrics, dict):
            return None
        
        try:
            kwargs = {'time_sec': float(time_sec)}
            
            for json_key, field_name in self.FIELD_MAP.items():
                if json_key not in metrics:
                    continue
                    
                value = metrics[json_key]
                if value is None:
                    continue
                
                # Handle mL to L conversion
                if field_name in self.ML_TO_L_FIELDS:
                    value = value / 1000.0
                    field_name = 've'  # Rename ve_ml -> ve
                
                # Convert to int if needed
                if field_name in self.INT_FIELDS:
                    value = int(value)
                else:
                    value = float(value)
                    
                kwargs[field_name] = value
            
            return ParsedItem(**kwargs)
            
        except (ValueError, TypeError):
            return None
    
    def _normalize_gender(self, sex: Optional[str]) -> Optional[str]:
        """Convert various gender formats to M/F."""
        if not sex:
            return None
        sex = sex.lower()
        if sex in ('m', 'male', 'м'):
            return 'M'
        elif sex in ('f', 'female', 'ж'):
            return 'F'
        return None
    
    def _parse_datetime(self, ts: Optional[str]) -> Optional[datetime]:
        """Parse ISO datetime string."""
        if not ts:
            return None
        try:
            # Handle ISO format with Z suffix
            if ts.endswith('Z'):
                ts = ts[:-1] + '+00:00'
            return datetime.fromisoformat(ts)
        except ValueError:
            return None
