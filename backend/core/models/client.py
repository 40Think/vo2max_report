"""
Client Model - Athlete Profile

Mirrors C# Client.cs from original project.
Stores athlete demographic and anthropometric data.

DOCUMENTATION:
    Spec: implementation_plan.md
    Legacy: src/Fitness.UI/Db/Client.cs
"""
from django.db import models


class Client(models.Model):
    """
    Athlete profile containing personal and anthropometric data.
    
    Fields mirror the original C# Client.cs:
    - Name, LastName, SecondName: Full name components
    - Gender: M/F enum
    - Birthdate: Date of birth for age calculation
    - Height: Height in cm
    - Weight: Weight in kg (used for VO2/kg calculations)
    """
    
    class Gender(models.TextChoices):
        MALE = 'M', 'Male'
        FEMALE = 'F', 'Female'
    
    # Name fields (matches C# Name, LastName, SecondName)
    name = models.CharField(
        max_length=100,
        verbose_name='First Name'
    )
    last_name = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='Last Name'
    )
    second_name = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='Middle Name'
    )
    
    # Demographics
    gender = models.CharField(
        max_length=1,
        choices=Gender.choices,
        default=Gender.MALE,
        verbose_name='Gender'
    )
    birthdate = models.DateField(
        null=True,
        blank=True,
        verbose_name='Date of Birth'
    )
    
    # Anthropometrics
    height = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Height (cm)'
    )
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Weight (kg)'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'
        ordering = ['last_name', 'name']
    
    def __str__(self) -> str:
        """Return full name for display."""
        parts = [self.last_name, self.name, self.second_name]
        return ' '.join(p for p in parts if p)
    
    @property
    def full_name(self) -> str:
        """Alias for __str__ for explicit access."""
        return str(self)
    
    @property
    def age(self) -> int | None:
        """Calculate age from birthdate."""
        if not self.birthdate:
            return None
        from datetime import date
        today = date.today()
        return today.year - self.birthdate.year - (
            (today.month, today.day) < (self.birthdate.month, self.birthdate.day)
        )
