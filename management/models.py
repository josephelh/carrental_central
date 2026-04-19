import uuid

from django.db import models


class Tier(models.Model):
    name = models.CharField(max_length=64, unique=True)
    max_cars = models.PositiveIntegerField()
    price_per_month = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class Agency(models.Model):
    name = models.CharField(max_length=255)
    license_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    contact_email = models.EmailField()
    subdomain = models.CharField(max_length=255, unique=True)
    tier = models.ForeignKey(Tier, on_delete=models.PROTECT, related_name='agencies')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Agencies'

    def __str__(self) -> str:
        return self.name
