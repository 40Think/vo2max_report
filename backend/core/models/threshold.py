"""
Threshold Model - Manual/Auto Threshold Values

Stores threshold zones (AeT, AnT, VO2max, etc.) with support for both
automatic detection and manual override by specialists.

DOCUMENTATION:
    Spec: implementation_plan.md (Phase 2)
"""
from django.db import models


class Threshold(models.Model):
    """
    Threshold value for a specific test.
    
    Thresholds can be:
    - Auto-detected by algorithms (is_manual=False)
    - Manually set by specialists (is_manual=True)
    
    When edited manually, the automatic value is preserved for reference.
    """
    
    class ThresholdType(models.TextChoices):
        AET = 'AET', 'АэП (Аэробный порог)'
        ANT = 'ANT', 'АнП (Анаэробный порог)'
        VO2MAX = 'VO2MAX', 'МПК (VO2max)'
        DO2 = 'DO2', 'ДО2 (Дефлекция O2)'
        MAM = 'MAM', 'МАМ (Макс анаэр. мощность)'
    
    # Link to test
    measurement = models.ForeignKey(
        'core.Measurement',
        on_delete=models.CASCADE,
        related_name='thresholds',
        verbose_name='Measurement'
    )
    
    # Threshold type
    threshold_type = models.CharField(
        max_length=10,
        choices=ThresholdType.choices,
        verbose_name='Threshold Type'
    )
    
    # Values at threshold
    power = models.IntegerField(
        verbose_name='Power (W)'
    )
    hr = models.IntegerField(
        null=True, blank=True,
        verbose_name='HR (bpm)'
    )
    vo2 = models.FloatField(
        null=True, blank=True,
        verbose_name='VO2 (mL/min)'
    )
    vo2_per_kg = models.FloatField(
        null=True, blank=True,
        verbose_name='VO2 (mL/kg/min)'
    )
    lactate = models.FloatField(
        null=True, blank=True,
        verbose_name='Lactate (mmol/L)'
    )
    
    # Manual vs automatic
    is_manual = models.BooleanField(
        default=False,
        verbose_name='Manually Set',
        help_text='True if set by specialist, False if auto-detected'
    )
    
    # Preserve auto value when manually edited
    auto_power = models.IntegerField(
        null=True, blank=True,
        verbose_name='Auto-detected Power',
        help_text='Original auto-detected value before manual edit'
    )
    
    # Notes from specialist
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name='Notes'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Threshold'
        verbose_name_plural = 'Thresholds'
        unique_together = ['measurement', 'threshold_type']
        ordering = ['measurement', 'power']
    
    def __str__(self) -> str:
        manual = '(manual)' if self.is_manual else '(auto)'
        return f"{self.get_threshold_type_display()}: {self.power}W {manual}"
    
    def set_manual(self, power: int, **kwargs):
        """Set threshold manually, preserving auto value."""
        if not self.is_manual:
            self.auto_power = self.power
        self.power = power
        self.is_manual = True
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.save()
    
    def reset_to_auto(self):
        """Reset to auto-detected value."""
        if self.auto_power is not None:
            self.power = self.auto_power
            self.is_manual = False
            self.save()
