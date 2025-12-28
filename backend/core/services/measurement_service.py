"""
MeasurementService - Data Processing and Persistence

Handles the workflow of parsing files and creating database records.
Provides methods for importing data from various file formats.

DOCUMENTATION:
    Spec: implementation_plan.md
"""
from datetime import datetime
from typing import Optional, Tuple
from pathlib import Path

from core.models import Client, Measurement, MeasurementItem
from core.parsers import ParserFactory, ParsedMeasurement, ParsedItem


class MeasurementService:
    """
    Service for importing and processing CPET measurement data.
    
    Workflow:
    1. Parse file using ParserFactory
    2. Create or find Client from parsed metadata
    3. Create Measurement record
    4. Bulk create MeasurementItems
    """
    
    @classmethod
    def import_file(
        cls,
        file_path: str,
        client: Optional[Client] = None,
        measurement_date: Optional[datetime] = None
    ) -> Tuple[Measurement, int]:
        """
        Import file and create database records.
        
        Args:
            file_path: Path to data file
            client: Optional existing client (will be created from file if not provided)
            measurement_date: Optional override for test date
            
        Returns:
            Tuple of (Measurement, item_count)
        """
        # Parse file
        parsed = ParserFactory.parse(file_path)
        
        # Get or create client
        if client is None:
            client = cls._get_or_create_client(parsed)
        
        # Create measurement
        measurement = cls._create_measurement(
            client=client,
            parsed=parsed,
            file_path=file_path,
            measurement_date=measurement_date
        )
        
        # Create items
        item_count = cls._create_items(measurement, parsed.items)
        
        return measurement, item_count
    
    @classmethod
    def _get_or_create_client(cls, parsed: ParsedMeasurement) -> Client:
        """Create or find client from parsed metadata."""
        # Try to find existing by name
        if parsed.client_name:
            existing = Client.objects.filter(
                name__iexact=parsed.client_name
            ).first()
            if existing:
                return existing
        
        # Create new client
        name = parsed.client_name or 'Unknown'
        name_parts = name.split()
        
        return Client.objects.create(
            name=name_parts[0] if name_parts else name,
            last_name=' '.join(name_parts[1:]) if len(name_parts) > 1 else '',
            gender=parsed.client_gender or 'M',
            height=parsed.client_height,
            weight=parsed.client_weight
        )
    
    @classmethod
    def _create_measurement(
        cls,
        client: Client,
        parsed: ParsedMeasurement,
        file_path: str,
        measurement_date: Optional[datetime] = None
    ) -> Measurement:
        """Create Measurement record."""
        # Detect protocol parameters from power progression
        start_power, power_step = cls._detect_protocol(parsed.items)
        
        return Measurement.objects.create(
            client=client,
            measurement_date=measurement_date or parsed.measurement_date or datetime.now(),
            start_power=start_power,
            power_step=power_step,
            source_format=parsed.source_format,
            source_file=Path(file_path).name
        )
    
    @classmethod
    def _create_items(cls, measurement: Measurement, items: list[ParsedItem]) -> int:
        """Bulk create MeasurementItem records."""
        db_items = []
        
        for item in items:
            db_items.append(MeasurementItem(
                measurement=measurement,
                time_sec=item.time_sec,
                vo2_ml_kg_min=item.vo2_ml_kg_min,
                vo2_ml_min=item.vo2_ml_min,
                vco2_ml_min=item.vco2_ml_min,
                hr=item.hr,
                power=item.power,
                rf=item.rf,
                tv=item.tv,
                ve=item.ve,
                rpm=item.rpm,
                ve_vo2=item.ve_vo2,
                feo2=item.feo2,
                r=item.r,
                hrv=item.hrv,
                sd1=item.sd1,
                sd2=item.sd2,
                temp=item.temp,
                hum=item.hum
            ))
        
        MeasurementItem.objects.bulk_create(db_items)
        return len(db_items)
    
    @classmethod
    def _detect_protocol(cls, items: list[ParsedItem]) -> Tuple[int, int]:
        """
        Auto-detect protocol parameters from power data.
        
        Analyzes power progression to find start power and step size.
        Based on C# Measurement.InitPowerParameters().
        
        Returns:
            (start_power, power_step)
        """
        if not items:
            return 0, 0
        
        # Extract unique power values, rounded to nearest 5W
        powers = []
        for item in items:
            if item.power is not None and item.power > 0:
                rounded = round(item.power / 5) * 5
                if rounded not in powers:
                    powers.append(rounded)
        
        if len(powers) < 2:
            return int(powers[0]) if powers else 0, 0
        
        # Calculate deltas
        deltas = [powers[i] - powers[i-1] for i in range(1, len(powers))]
        
        # Filter positive deltas (ascending protocol)
        positive_deltas = [d for d in deltas if d > 0]
        
        if not positive_deltas:
            return int(powers[0]), 0
        
        # Use most common step as protocol step
        from collections import Counter
        step = Counter(positive_deltas).most_common(1)[0][0]
        
        return int(powers[0]), int(step)
