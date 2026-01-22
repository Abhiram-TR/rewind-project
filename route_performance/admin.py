from django.contrib import admin
from .models import RoutePerformanceMetrics, RouteComparison, RoutePerformanceTrend

@admin.register(RoutePerformanceMetrics)
class RoutePerformanceMetricsAdmin(admin.ModelAdmin):
    list_display = ('route_no', 'date_range', 'period_start', 'period_end', 'avg_epkm', 'total_revenue', 'trip_count', 'performance_rank')
    list_filter = ('date_range', 'period_start', 'performance_rank')
    search_fields = ('route_no',)
    ordering = ('-avg_epkm',)
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()

@admin.register(RouteComparison)
class RouteComparisonAdmin(admin.ModelAdmin):
    list_display = ('comparison_date', 'total_routes_analyzed', 'industry_avg_epkm', 'created_at')
    list_filter = ('comparison_date',)
    readonly_fields = ('created_at', 'updated_at')
    
    def best_routes_count(self, obj):
        return len(obj.best_performing_routes)
    best_routes_count.short_description = 'Best Routes Count'
    
    def underperforming_routes_count(self, obj):
        return len(obj.underperforming_routes)
    underperforming_routes_count.short_description = 'Underperforming Routes Count'

@admin.register(RoutePerformanceTrend)
class RoutePerformanceTrendAdmin(admin.ModelAdmin):
    list_display = ('route_no', 'date', 'epkm', 'revenue', 'trip_count', 'epkm_trend', 'performance_category')
    list_filter = ('date', 'epkm_trend', 'performance_category')
    search_fields = ('route_no',)
    ordering = ('-date', '-epkm')
    readonly_fields = ('created_at',)
