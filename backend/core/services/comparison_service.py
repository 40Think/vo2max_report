"""
Comparison Service

Compares multiple tests of the same client, building comparison tables
and calculating dynamics across test dates.

DOCUMENTATION:
    Spec: implementation_plan.md (Phase 2)
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ComparisonColumn:
    """Single test column in comparison table"""
    measurement_id: int
    date: datetime
    test_type: str
    label: str  # e.g. "4 августа" or "2 ноября"


@dataclass
class ComparisonRow:
    """Single row (power level) in comparison table"""
    power: int
    values: Dict[int, Any]  # measurement_id -> value


class ComparisonService:
    """
    Service for comparing multiple tests of the same client.
    
    Builds tables aligned by power level, calculates deltas,
    and filters by test type to prevent invalid comparisons.
    """
    
    @staticmethod
    def get_client_tests(
        client_id: int,
        test_type: Optional[str] = None,
        limit: int = 10
    ) -> list:
        """
        Get list of tests for a client, optionally filtered by type.
        
        Args:
            client_id: Client ID
            test_type: Optional test type filter
            limit: Max number of tests
            
        Returns:
            List of Measurement objects ordered by date
        """
        from core.models import Measurement
        
        qs = Measurement.objects.filter(client_id=client_id)
        if test_type:
            qs = qs.filter(test_type=test_type)
        return list(qs.order_by('-measurement_date')[:limit])
    
    @staticmethod
    def build_power_aligned_table(
        measurements: list,
        metric: str = 'hr'
    ) -> Dict[str, Any]:
        """
        Build comparison table aligned by power levels.
        
        Args:
            measurements: List of Measurement objects
            metric: Field name to compare (hr, vo2_ml_min, ve, lactat, etc.)
            
        Returns:
            {
                'columns': [ComparisonColumn, ...],
                'rows': [ComparisonRow, ...],
                'metric': str
            }
        """
        if not measurements:
            return {'columns': [], 'rows': [], 'metric': metric}
        
        # Build columns
        columns = []
        for m in measurements:
            date_str = m.measurement_date.strftime('%d %b')
            columns.append(ComparisonColumn(
                measurement_id=m.id,
                date=m.measurement_date,
                test_type=m.test_type,
                label=date_str
            ))
        
        # Collect all power levels
        all_powers = set()
        data_by_measurement = {}
        
        for m in measurements:
            items = m.items.filter(use_in_report=True).order_by('rated_power')
            # Group by rated_power and average
            power_data = {}
            for item in items:
                power = item.rated_power or int(item.power or 0)
                if power not in power_data:
                    power_data[power] = []
                value = getattr(item, metric, None)
                if value is not None:
                    power_data[power].append(value)
            
            # Average values per power
            data_by_measurement[m.id] = {}
            for power, values in power_data.items():
                if values:
                    all_powers.add(power)
                    data_by_measurement[m.id][power] = sum(values) / len(values)
        
        # Build rows
        rows = []
        for power in sorted(all_powers):
            values = {}
            for m in measurements:
                values[m.id] = data_by_measurement.get(m.id, {}).get(power)
            rows.append(ComparisonRow(power=power, values=values))
        
        return {
            'columns': columns,
            'rows': rows,
            'metric': metric
        }
    
    @staticmethod
    def calculate_dynamics(
        measurements: list,
        thresholds: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate dynamics (changes) between consecutive tests.
        
        Args:
            measurements: List of Measurement objects (ordered by date)
            thresholds: Include threshold changes
            
        Returns:
            {
                'tests': [...],
                'deltas': [...],
                'thresholds_deltas': [...] (optional)
            }
        """
        if len(measurements) < 2:
            return {'tests': measurements, 'deltas': [], 'thresholds_deltas': []}
        
        deltas = []
        for i in range(1, len(measurements)):
            prev = measurements[i - 1]
            curr = measurements[i]
            
            # Calculate peak values
            prev_peaks = ComparisonService._get_peaks(prev)
            curr_peaks = ComparisonService._get_peaks(curr)
            
            delta = {
                'from': prev.measurement_date,
                'to': curr.measurement_date,
                'days': (curr.measurement_date - prev.measurement_date).days,
                'vo2max_delta': (curr_peaks.get('vo2max', 0) or 0) - (prev_peaks.get('vo2max', 0) or 0),
                'hrmax_delta': (curr_peaks.get('hrmax', 0) or 0) - (prev_peaks.get('hrmax', 0) or 0),
                'power_delta': (curr_peaks.get('power', 0) or 0) - (prev_peaks.get('power', 0) or 0),
            }
            deltas.append(delta)
        
        return {
            'tests': measurements,
            'deltas': deltas
        }
    
    @staticmethod
    def _get_peaks(measurement) -> Dict[str, Any]:
        """Get peak values from a measurement."""
        items = measurement.items.filter(use_in_report=True)
        if not items.exists():
            return {}
        
        from django.db.models import Max
        
        peaks = items.aggregate(
            vo2max=Max('vo2_ml_kg_min'),
            hrmax=Max('hr'),
            power=Max('power')
        )
        return peaks
    
    @staticmethod
    def to_dict(comparison_result: dict) -> dict:
        """Convert comparison result to JSON-serializable dict."""
        result = {
            'metric': comparison_result.get('metric'),
            'columns': [],
            'rows': []
        }
        
        for col in comparison_result.get('columns', []):
            result['columns'].append({
                'id': col.measurement_id,
                'date': col.date.isoformat() if col.date else None,
                'test_type': col.test_type,
                'label': col.label
            })
        
        for row in comparison_result.get('rows', []):
            result['rows'].append({
                'power': row.power,
                'values': row.values
            })
        
        return result
