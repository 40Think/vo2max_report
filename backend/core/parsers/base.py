"""
BaseParser - Abstract Base Class for Data Parsers

Defines the contract for all format-specific parsers.
Provides normalized data structures for inter-format compatibility.

DOCUMENTATION:
    Spec: implementation_plan.md
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class ParsedItem:
    """
    Normalized data point - format-agnostic representation.
    
    All parsers convert their native format to this structure.
    Fields are Optional to accommodate different formats having
    different available metrics.
    """
    time_sec: float
    
    # Gas exchange
    vo2_ml_kg_min: Optional[float] = None
    vo2_ml_min: Optional[float] = None
    vco2_ml_min: Optional[float] = None
    
    # Cardiovascular
    hr: Optional[int] = None
    
    # Power/Load
    power: Optional[float] = None
    
    # Ventilation
    rf: Optional[float] = None      # Respiratory frequency
    tv: Optional[float] = None      # Tidal volume
    ve: Optional[float] = None      # Minute ventilation (L/min)
    
    # Cadence
    rpm: Optional[float] = None
    
    # Derived metrics
    ve_vo2: Optional[float] = None
    feo2: Optional[float] = None
    r: Optional[float] = None       # RER
    
    # HRV (JSON format)
    hrv: Optional[int] = None
    sd1: Optional[float] = None
    sd2: Optional[float] = None
    
    # Environment
    temp: Optional[float] = None
    hum: Optional[float] = None


@dataclass
class ParsedMeasurement:
    """
    Complete parsed test result.
    
    Contains both client metadata (if available in source)
    and the list of time-series data points.
    """
    items: List[ParsedItem] = field(default_factory=list)
    
    # Client info (from JSON setup or header)
    client_name: Optional[str] = None
    client_weight: Optional[float] = None
    client_height: Optional[float] = None
    client_gender: Optional[str] = None
    client_age: Optional[int] = None
    
    # Test metadata
    measurement_date: Optional[datetime] = None
    test_id: Optional[str] = None
    comment: Optional[str] = None
    
    # Source info
    source_format: str = 'UNKNOWN'
    source_file: str = ''


class BaseParser(ABC):
    """
    Abstract base class for format-specific parsers.
    
    Subclasses must implement:
    - parse(): Convert file to ParsedMeasurement
    - can_parse(): Static check if parser handles given file
    """
    
    @abstractmethod
    def parse(self, file_path: str) -> ParsedMeasurement:
        """
        Parse file and return normalized data structure.
        
        Args:
            file_path: Path to input file
            
        Returns:
            ParsedMeasurement with items and metadata
            
        Raises:
            ValueError: If file format is invalid
            FileNotFoundError: If file doesn't exist
        """
        pass
    
    @classmethod
    @abstractmethod
    def can_parse(cls, file_path: str) -> bool:
        """
        Check if this parser can handle the given file.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if parser can handle this file
        """
        pass
    
    @staticmethod
    def _parse_decimal_comma(value: str) -> float:
        """
        Parse numeric string with comma as decimal separator.
        
        Handles OMNIA CSV format where decimals are "22,53" not "22.53".
        Also handles quoted values like '"22,53"'.
        
        Args:
            value: String numeric value
            
        Returns:
            Parsed float
        """
        # Remove quotes if present
        cleaned = value.strip().strip('"').strip("'")
        # Replace comma with dot for float parsing
        cleaned = cleaned.replace(',', '.')
        return float(cleaned)
