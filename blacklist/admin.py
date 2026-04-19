from django.contrib import admin

from .models import GlobalBlacklistEntry


@admin.register(GlobalBlacklistEntry)
class GlobalBlacklistEntryAdmin(admin.ModelAdmin):
    list_display = (
        'identity_hash',
        'severity',
        'reported_by',
        'created_at',
    )
    list_filter = ('severity',)
    readonly_fields = ('created_at',)
    search_fields = ('identity_hash', 'reason', 'reported_by__name')
