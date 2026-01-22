from django.contrib import admin
from .models import RouteAnalysis, BusOverlapData

@admin.register(RouteAnalysis)
class RouteAnalysisAdmin(admin.ModelAdmin):
    list_display = ('route_no', 'selected_date', 'analysis_date', 'time_period_start', 'time_period_end', 'total_buses', 'overlap_score')
    list_filter = ('route_no', 'selected_date', 'analysis_date')
    search_fields = ('route_no',)
    readonly_fields = ('analysis_date',)

@admin.register(BusOverlapData)
class BusOverlapDataAdmin(admin.ModelAdmin):
    list_display = ('route_no', 'schedule_no', 'trip_no', 'selected_date', 'start_time', 'end_time', 'estimated_passengers', 'service_type', 'created_at')
    list_filter = ('route_no', 'selected_date', 'service_type', 'created_at')
    search_fields = ('route_no', 'schedule_no')
    readonly_fields = ('created_at',)
