from django.contrib import admin

from .models import AnalyticsSnapshot


@admin.register(AnalyticsSnapshot)
class AnalyticsSnapshotAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'total_contracts', 'total_amount',
        'active_contracts', 'completed_contracts',
        'new_contracts', 'new_amount',
    ]
    list_filter = ['date']
    ordering = ['-date']
    readonly_fields = ['created_at', 'updated_at']
