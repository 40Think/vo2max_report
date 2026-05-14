"""
PDF Report Generator

Generates PDF reports from HTML/Jinja2 templates.
Supports customizable templates with threshold zones, training recommendations, and charts.

DOCUMENTATION:
    Sample: uploaded_image (user's report format)
"""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import json


@dataclass
class ThresholdZone:
    """Single threshold zone (AeT, AnT, VO2max, etc.)"""
    name: str              # АэП, АнП, МПК, ДО2, МАМ
    name_full: str         # Full name for display
    power: int             # Watts
    power_per_kg: float    # W/kg
    vo2: float             # L/min or mL/min
    vo2_per_kg: float      # mL/kg/min
    hr: int                # bpm
    color: str = "#4a90d9" # Bar color


@dataclass
class TrainingZone:
    """Training zone recommendation"""
    name: str              # Z1, Z2, etc.
    label: str             # Отдых, АэП, АнП, etc.
    hr_min: Optional[int] = None
    hr_max: Optional[int] = None
    power_min: Optional[int] = None
    power_max: Optional[int] = None
    intervals_min: Optional[int] = None
    intervals_max: Optional[int] = None
    rest_power_min: Optional[int] = None
    rest_power_max: Optional[int] = None
    sessions_per_week: Optional[str] = None


@dataclass
class ReportData:
    """Complete report data structure"""
    # Client info
    client_name: str = ""
    client_age: Optional[int] = None
    client_height: Optional[int] = None  # cm
    client_weight: Optional[float] = None  # kg
    client_qualification: str = ""
    
    # Test info
    test_date: Optional[datetime] = None
    sport: str = ""
    test_type: str = ""
    protocol: str = ""
    equipment: str = ""
    
    # Threshold zones
    thresholds: List[ThresholdZone] = field(default_factory=list)
    
    # Conclusions
    limiting_factor: str = ""
    muscle_quality: str = ""
    o2_delivery_limit: Optional[int] = None
    muscle_strength_limit: Optional[float] = None
    
    # Training zones
    training_zones: List[TrainingZone] = field(default_factory=list)
    
    # Raw data for charts
    chart_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for template rendering."""
        return {
            'client': {
                'name': self.client_name,
                'age': self.client_age,
                'height': self.client_height,
                'weight': self.client_weight,
                'qualification': self.client_qualification,
            },
            'test': {
                'date': self.test_date.strftime('%d.%m.%Y') if self.test_date else '',
                'sport': self.sport,
                'test_type': self.test_type,
                'protocol': self.protocol,
                'equipment': self.equipment,
            },
            'thresholds': [
                {
                    'name': t.name,
                    'name_full': t.name_full,
                    'power': t.power,
                    'power_per_kg': t.power_per_kg,
                    'vo2': t.vo2,
                    'vo2_per_kg': t.vo2_per_kg,
                    'hr': t.hr,
                    'color': t.color,
                    'power_percent': min(100, t.power / 12),  # Scale for bar chart
                }
                for t in self.thresholds
            ],
            'conclusions': {
                'limiting_factor': self.limiting_factor,
                'muscle_quality': self.muscle_quality,
                'o2_delivery_limit': self.o2_delivery_limit,
                'muscle_strength_limit': self.muscle_strength_limit,
            },
            'training_zones': [
                {
                    'name': z.name,
                    'label': z.label,
                    'hr_min': z.hr_min or '',
                    'hr_max': z.hr_max or '',
                    'power_min': z.power_min or '',
                    'power_max': z.power_max or '',
                    'intervals_min': z.intervals_min or '',
                    'intervals_max': z.intervals_max or '',
                    'rest_power_min': z.rest_power_min or '',
                    'rest_power_max': z.rest_power_max or '',
                    'sessions': z.sessions_per_week or '',
                }
                for z in self.training_zones
            ],
            'chart_data': self.chart_data,
        }


def create_sample_report() -> ReportData:
    """Create sample report matching the user's image."""
    return ReportData(
        client_name="",
        client_age=35,
        client_height=172,
        client_weight=61,
        client_qualification="МС",
        test_date=datetime(2019, 1, 24),
        sport="Велоспорт",
        test_type="Велоэргометрия",
        protocol="Старт 140 ватт, +20 ватт каждые 2 минуты",
        equipment="станок Тасх",
        thresholds=[
            ThresholdZone("АэП", "Аэробный порог", 230, 3.77, 3.2, 52, 148, "#6b9bd1"),
            ThresholdZone("АнП", "Анаэробный порог", 270, 4.43, 3.4, 56, 163, "#5a8bc4"),
            ThresholdZone("МПК", "Макс. потр. O2", 380, 6.23, 4.5, 74, 186, "#4a7ab7"),
            ThresholdZone("ДО2", "Дефлекция O2", 500, 8.20, 6.7, 109, 0, "#3a6aaa"),
            ThresholdZone("МАМ", "Макс. анаэр. мощн.", 1050, 17.21, 0, 0, 0, "#2a5a9d"),
        ],
        limiting_factor="Локальная мышечная выносливость",
        muscle_quality="Высокое",
        o2_delivery_limit=500,
        muscle_strength_limit=472.5,
        training_zones=[
            TrainingZone("Z1", "Отдых", None, 148, None, 230, None, None, None, None, None),
            TrainingZone("Z2", "АэП", 148, 155, 230, 250, 1, 5, 100, 230, None),
            TrainingZone("Z3", "АнП", 156, 163, 260, 280, 1, 5, 200, 250, None),
            TrainingZone("Z4", "АнП+", 164, 183, 290, 350, 1, 10, 200, 250, None),
            TrainingZone("Z5", "МПК и ДО2", 184, 190, 380, 410, 1, 5, 200, 250, None),
            TrainingZone("Z6-7", "МАМ", None, None, 630, 945, 2, 4, 200, 250, None),
        ],
    )
