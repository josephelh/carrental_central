from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Severity(models.TextChoices):
    LOW = 'low', 'Low'
    MEDIUM = 'medium', 'Medium'
    HIGH = 'high', 'High'

class GlobalReputationEntry(models.Model):
    cin_hash = models.CharField(max_length=64, db_index=True, null=True, blank=True)
    license_hash = models.CharField(max_length=64, db_index=True, null=True, blank=True)
    reason = models.TextField()
    rating = models.PositiveSmallIntegerField(
        default=3, 
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    reported_by = models.ForeignKey(
        'management.Agency',
        on_delete=models.PROTECT,
        related_name='reputation_reports',
    )
    severity = models.CharField(
        max_length=16,
        choices=Severity.choices,
        default=Severity.MEDIUM,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('cin_hash', 'reported_by')

    def __str__(self) -> str:
        return f'{self.cin_hash[:12]}... ({self.rating}/5)'