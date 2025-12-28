"""
MeasurementItem Model - Time-Series Data Point

Mirrors C# MeasurementItem.cs from original project.
Stores breath-by-breath or averaged CPET data.

DOCUMENTATION:
    Spec: implementation_plan.md
    Legacy: src/Fitness.UI/Db/MeasurementItem.cs
    
Column mapping from C# MeasurementItemMap:
    Time[s] -> time_sec
    VO2[mL/kg/min] -> vo2_ml_kg_min
    VO2[mL/min] -> vo2_ml_min
    HR[bpm] -> hr
    Power[watts] -> power
    Rf[bpm] -> rf
    Tv[L] -> tv
    Ve[L/min] -> ve
    RPM[rpm] -> rpm
    Ve/VO2 -> ve_vo2
    FeO2[%] -> feo2
"""
from django.db import models


class MeasurementItem(models.Model):
    """
    Single time-point data row from CPET test.
    
    Contains all measured physiological parameters at a specific
    time offset from test start. Designed to accommodate both:
    - OMNIA CSV format (Ve, Rf, Tv, FeO2)
    - Custom JSON format (HRvar, SD1, SD2, R)
    """
    
    # Foreign key to test session
    measurement = models.ForeignKey(
        'core.Measurement',
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Measurement'
    )
    
    # Time offset from test start
    time_sec = models.FloatField(
        verbose_name='Time (s)',
        help_text='Seconds from test start'
    )
    
    # Gas exchange metrics
    vo2_ml_kg_min = models.FloatField(
        null=True, blank=True,
        verbose_name='VO2 (mL/kg/min)',
        help_text='Oxygen consumption normalized to body weight'
    )
    vo2_ml_min = models.FloatField(
        null=True, blank=True,
        verbose_name='VO2 (mL/min)',
        help_text='Absolute oxygen consumption'
    )
    vco2_ml_min = models.FloatField(
        null=True, blank=True,
        verbose_name='VCO2 (mL/min)',
        help_text='Carbon dioxide production'
    )
    
    # Cardiovascular
    hr = models.IntegerField(
        null=True, blank=True,
        verbose_name='HR (bpm)',
        help_text='Heart rate'
    )
    
    # Power/Load
    power = models.FloatField(
        null=True, blank=True,
        verbose_name='Power (W)',
        help_text='Measured power output'
    )
    rated_power = models.IntegerField(
        null=True, blank=True,
        verbose_name='Rated Power (W)',
        help_text='Protocol-prescribed power'
    )
    
    # Ventilation (OMNIA CSV specific)
    rf = models.FloatField(
        null=True, blank=True,
        verbose_name='Rf (bpm)',
        help_text='Respiratory frequency'
    )
    tv = models.FloatField(
        null=True, blank=True,
        verbose_name='Tv (L)',
        help_text='Tidal volume'
    )
    ve = models.FloatField(
        null=True, blank=True,
        verbose_name='Ve (L/min)',
        help_text='Minute ventilation'
    )
    
    # Cadence
    rpm = models.FloatField(
        null=True, blank=True,
        verbose_name='RPM',
        help_text='Cycling cadence'
    )
    
    # Derived metrics
    ve_vo2 = models.FloatField(
        null=True, blank=True,
        verbose_name='Ve/VO2',
        help_text='Ventilatory equivalent for O2'
    )
    feo2 = models.FloatField(
        null=True, blank=True,
        verbose_name='FeO2 (%)',
        help_text='Expired oxygen fraction'
    )
    r = models.FloatField(
        null=True, blank=True,
        verbose_name='RER',
        help_text='Respiratory exchange ratio (VCO2/VO2)'
    )
    
    # HRV metrics (JSON format specific)
    hrv = models.IntegerField(
        null=True, blank=True,
        verbose_name='HRvar (ms)',
        help_text='Heart rate variability'
    )
    sd1 = models.FloatField(
        null=True, blank=True,
        verbose_name='SD1 (ms)',
        help_text='Poincaré plot SD1'
    )
    sd2 = models.FloatField(
        null=True, blank=True,
        verbose_name='SD2 (ms)',
        help_text='Poincaré plot SD2'
    )
    
    # Lactate (manual entry)
    lactat = models.FloatField(
        null=True, blank=True,
        verbose_name='Lactate (mmol/L)',
        help_text='Blood lactate concentration'
    )
    
    # Environment (OMNIA CSV)
    temp = models.FloatField(
        null=True, blank=True,
        verbose_name='Temp (°C)'
    )
    hum = models.FloatField(
        null=True, blank=True,
        verbose_name='Humidity (%RH)'
    )
    
    # Editing tracking
    is_edited = models.BooleanField(
        default=False,
        verbose_name='Manually Edited'
    )
    original_values = models.JSONField(
        null=True, blank=True,
        verbose_name='Original Values',
        help_text='Backup of values before manual edit'
    )
    edit_notes = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='Edit Notes'
    )
    
    # Flags
    use_in_report = models.BooleanField(
        default=True,
        verbose_name='Include in Report'
    )
    
    class Meta:
        verbose_name = 'Measurement Item'
        verbose_name_plural = 'Measurement Items'
        ordering = ['measurement', 'time_sec']
        indexes = [
            models.Index(fields=['measurement', 'time_sec']),
        ]
    
    def __str__(self) -> str:
        """Return time-based identifier."""
        return f"t={self.time_sec}s"
