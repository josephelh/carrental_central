from django.contrib import admin

from .models import Agency, Tier


@admin.register(Tier)
class TierAdmin(admin.ModelAdmin):
    list_display = ('name', 'max_cars', 'price_per_month')


@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'subdomain', 'tier', 'is_active', 'created_at')
    list_filter = ('is_active', 'tier')
    readonly_fields = ('license_key', 'created_at')
