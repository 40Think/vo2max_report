"""
Measurement Model - Test Session

Mirrors C# Measurement.cs from original project.
Represents a single CPET test session with protocol parameters.

DOCUMENTATION:
    Spec: implementation_plan.md
    Legacy: src/Fitness.UI/Db/Measurement.cs
"""
from django.db import models


class Measurement(models.Model):
    """
    Single CPET test session.
    
    Contains protocol configuration and links to:
    - Client: The athlete being tested
    - MeasurementItems: Time-series data points
    
    Fields mirror C# Measurement.cs:
    - StartPower, PowerStep: Protocol ramp configuration
    - MeasurementDate: When the test was performed
    """
    
    class SourceFormat(models.TextChoices):
        OMNIA_CSV = 'OMNIA_CSV', 'COSMED OMNIA CSV'
        CUSTOM_JSON = 'CUSTOM_JSON', 'Custom JSON (dataMap)'
        PNOE_CSV = 'PNOE_CSV', 'PNOE CSV'
        METASOFT = 'METASOFT', 'Cortex MetaSoft'
        FIT = 'FIT', 'Garmin FIT'
    
    class TestType(models.TextChoices):
        CYCLING = 'CYCLING', 'Велосипед'
        RUNNING = 'RUNNING', 'Бег'
        SWIMMING = 'SWIMMING', 'Плавание'
        SKIING = 'SKIING', 'Лыжи'
        ROWING = 'ROWING', 'Гребля'
        OTHER = 'OTHER', 'Другое'
    
    # Foreign key to athlete
    client = models.ForeignKey(
        'core.Client',
        on_delete=models.CASCADE,
        related_name='measurements',
        verbose_name='Athlete'
    )
    
    # Test timing
    measurement_date = models.DateTimeField(
        verbose_name='Test Date'
    )
    
    # Protocol parameters (from C# Measurement.cs)
    start_power = models.IntegerField(
        default=0,
        verbose_name='Start Power (W)',
        help_text='Initial power for stepped protocol'
    )
    power_step = models.IntegerField(
        default=0,
        verbose_name='Power Step (W)',
        help_text='Power increment per stage'
    )
    
    # Test type for filtering comparisons
    test_type = models.CharField(
        max_length=20,
        choices=TestType.choices,
        default=TestType.CYCLING,
        verbose_name='Test Type'
    )
    
    # Source tracking
    source_format = models.CharField(
        max_length=20,
        choices=SourceFormat.choices,
        default=SourceFormat.OMNIA_CSV,
        verbose_name='Source Format'
    )
    source_file = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='Source Filename'
    )
    
    # Raw data backup (JSON blob of original file)
    raw_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Raw Source Data'
    )
    
    # Flags
    use_in_report = models.BooleanField(
        default=True,
        verbose_name='Include in Report'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Measurement'
        verbose_name_plural = 'Measurements'
        ordering = ['-measurement_date']
    
    def __str__(self) -> str:
        """Return formatted test identifier."""
        date_str = self.measurement_date.strftime('%Y-%m-%d')
        return f"{self.client} - {date_str}"
    
    @property
    def item_count(self) -> int:
        """Return number of data points in this measurement."""
        return self.items.count()
    
    @property
    def duration_sec(self) -> float | None:
        """Calculate test duration from items."""
        last = self.items.order_by('-time_sec').first()
        return last.time_sec if last else None
