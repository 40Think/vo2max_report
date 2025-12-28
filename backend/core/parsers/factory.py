"""
ParserFactory - Auto-detection and Parser Selection

Factory pattern for selecting appropriate parser based on file type.
Supports runtime detection of file format.

DOCUMENTATION:
    Spec: implementation_plan.md
"""
from pathlib import Path
from typing import Type, List

from core.parsers.base import BaseParser, ParsedMeasurement
from core.parsers.csv_parser import CsvParser
from core.parsers.json_parser import JsonParser


class ParserFactory:
    """
    Factory for creating appropriate parser based on file format.
    
    Supports both extension-based and content-based detection.
    """
    
    # Registered parsers in priority order
    PARSERS: List[Type[BaseParser]] = [
        JsonParser,
        CsvParser,
    ]
    
    @classmethod
    def get_parser(cls, file_path: str) -> BaseParser:
        """
        Get appropriate parser for file.
        
        Uses can_parse() method of each registered parser
        to determine which one handles the file.
        
        Args:
            file_path: Path to file to parse
            
        Returns:
            Instantiated parser
            
        Raises:
            ValueError: If no parser found for file format
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Try each parser's can_parse method
        for parser_class in cls.PARSERS:
            if parser_class.can_parse(file_path):
                return parser_class()
        
        raise ValueError(
            f"No parser found for file: {path.name}. "
            f"Supported formats: {cls.supported_formats()}"
        )
    
    @classmethod
    def parse(cls, file_path: str) -> ParsedMeasurement:
        """
        Convenience method: get parser and parse in one call.
        
        Args:
            file_path: Path to file
            
        Returns:
            ParsedMeasurement result
        """
        parser = cls.get_parser(file_path)
        return parser.parse(file_path)
    
    @classmethod
    def supported_formats(cls) -> str:
        """Return human-readable list of supported formats."""
        return "JSON (dataMap), CSV (OMNIA)"
    
    @classmethod
    def register_parser(cls, parser_class: Type[BaseParser]) -> None:
        """
        Register additional parser at runtime.
        
        Useful for plugins or custom format support.
        """
        if parser_class not in cls.PARSERS:
            cls.PARSERS.insert(0, parser_class)
