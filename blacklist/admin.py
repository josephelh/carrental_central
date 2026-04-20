from django.contrib import admin

from .models import GlobalReputationEntry


@admin.register(GlobalReputationEntry)
class GlobalReputationEntryAdmin(admin.ModelAdmin):
    list_display = (
        'identity_hash',
        'rating',
        'reported_by',
        'created_at',
    )
    list_filter = ('rating',)
    readonly_fields = ('created_at',)
    search_fields = ('identity_hash', 'reason', 'reported_by__name')
