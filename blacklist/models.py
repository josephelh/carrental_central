from django.db import models


class Severity(models.TextChoices):
    LOW = 'low', 'Low'
    MEDIUM = 'medium', 'Medium'
    HIGH = 'high', 'High'


class GlobalBlacklistEntry(models.Model):
    identity_hash = models.CharField(max_length=64, unique=True, db_index=True)
    reason = models.TextField()
    reported_by = models.ForeignKey(
        'management.Agency',
        on_delete=models.PROTECT,
        related_name='blacklist_reports',
    )
    severity = models.CharField(
        max_length=16,
        choices=Severity.choices,
        default=Severity.MEDIUM,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.identity_hash[:12]}...'
