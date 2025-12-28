"""
VO2max Report - Parsers Package

Parser infrastructure for importing data from various formats:
- BaseParser: Abstract base class
- CsvParser: COSMED OMNIA CSV format
- JsonParser: Custom JSON format with dataMap
- ParserFactory: Auto-detection and parser selection
"""
from core.parsers.base import BaseParser, ParsedItem, ParsedMeasurement
from core.parsers.csv_parser import CsvParser
from core.parsers.json_parser import JsonParser
from core.parsers.factory import ParserFactory

__all__ = [
    'BaseParser', 'ParsedItem', 'ParsedMeasurement',
    'CsvParser', 'JsonParser', 'ParserFactory'
]
