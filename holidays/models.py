from django.db import models
from django.core.exceptions import ValidationError


class Holiday(models.Model):
    """National Holiday model for managing holidays"""
    
    # Holiday Type Choices
    HOLIDAY_TYPE_CHOICES = [
        ('national', 'National'),
        ('regional', 'Regional'),
        ('religious', 'Religious'),
        ('cultural', 'Cultural'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(
        max_length=200,
        help_text="Name of the holiday"
    )
    date = models.DateField(
        help_text="Date of the holiday"
    )
    description = models.TextField(
        blank=True,
        help_text="Description or details about the holiday"
    )
    country = models.CharField(
        max_length=100,
        default='India',
        help_text="Country where this holiday is observed"
    )
    region = models.CharField(
        max_length=100,
        blank=True,
        help_text="State/Province/Region (optional, for regional holidays)"
    )
    holiday_type = models.CharField(
        max_length=20,
        choices=HOLIDAY_TYPE_CHOICES,
        default='national',
        help_text="Type of holiday"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this holiday is currently active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'name']
        verbose_name = 'Holiday'
        verbose_name_plural = 'Holidays'
        unique_together = ['name', 'date', 'country']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['country']),
            models.Index(fields=['holiday_type']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.date})"

    def clean(self):
        """Validate the holiday data"""
        # Check if date is in the past (optional validation)
        # You can add more validation logic here if needed
        pass


