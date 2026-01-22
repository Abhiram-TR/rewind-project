from django.db import models
from django.db.models import Avg, Sum, Count
from bus_route.models import Trip, Schedule
from datetime import date, timedelta

class RoutePerformanceMetrics(models.Model):
    """Aggregated route performance metrics for different time periods"""
    
    PERIOD_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    route_no = models.CharField(max_length=20)
    date_range = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Performance metrics
    avg_epkm = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_km = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    trip_count = models.IntegerField(default=0)
    performance_rank = models.IntegerField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = (('route_no', 'date_range', 'period_start', 'period_end'),)
        indexes = [
            models.Index(fields=['route_no', 'date_range']),
            models.Index(fields=['avg_epkm']),
            models.Index(fields=['performance_rank']),
        ]
    
    def __str__(self):
        return f"Route {self.route_no} - {self.date_range} ({self.period_start} to {self.period_end})"
    
    @classmethod
    def calculate_route_performance(cls, route_no, start_date, end_date, period_type='daily'):
        """Calculate performance metrics for a route within a date range"""
        trips = Trip.objects.filter(
            schedule_no__in=Schedule.objects.filter(route_no=route_no).values_list('schedule_no', flat=True),
            date__range=[start_date, end_date],
            revenue__isnull=False
        )
        
        if not trips.exists():
            return None
        
        # Calculate metrics
        total_revenue = trips.aggregate(Sum('revenue'))['revenue__sum'] or 0
        trip_count = trips.count()
        
        # Calculate total km and avg EPKM
        total_km = 0
        epkm_values = []
        
        for trip in trips:
            if trip.epkm is not None:
                epkm_values.append(trip.epkm)
                try:
                    schedule = Schedule.objects.get(
                        schedule_no=trip.schedule_no, 
                        trip_no=trip.trip_no
                    )
                    if schedule.trip_km:
                        total_km += schedule.trip_km
                except Schedule.DoesNotExist:
                    continue
        
        avg_epkm = sum(epkm_values) / len(epkm_values) if epkm_values else None
        
        # Create or update performance record
        performance, created = cls.objects.get_or_create(
            route_no=route_no,
            date_range=period_type,
            period_start=start_date,
            period_end=end_date,
            defaults={
                'avg_epkm': avg_epkm,
                'total_revenue': total_revenue,
                'total_km': total_km,
                'trip_count': trip_count,
            }
        )
        
        if not created:
            performance.avg_epkm = avg_epkm
            performance.total_revenue = total_revenue
            performance.total_km = total_km
            performance.trip_count = trip_count
            performance.save()
        
        return performance

class RouteComparison(models.Model):
    """Daily route comparison rankings"""
    
    comparison_date = models.DateField(default=date.today)
    best_performing_routes = models.JSONField(default=list)  # Top 10 routes
    underperforming_routes = models.JSONField(default=list)  # Bottom 10 routes
    total_routes_analyzed = models.IntegerField(default=0)
    industry_avg_epkm = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = (('comparison_date',),)
    
    def __str__(self):
        return f"Route Comparison for {self.comparison_date}"
    
    @classmethod
    def generate_daily_comparison(cls, target_date=None):
        """Generate route comparison for a specific date"""
        if target_date is None:
            target_date = date.today()
        
        # Get all routes with performance data
        route_performances = RoutePerformanceMetrics.objects.filter(
            date_range='daily',
            period_start=target_date,
            avg_epkm__isnull=False
        ).order_by('-avg_epkm')
        
        if not route_performances.exists():
            return None
        
        # Update performance ranks
        for idx, performance in enumerate(route_performances, 1):
            performance.performance_rank = idx
            performance.save()
        
        # Get top and bottom performers
        best_performers = list(route_performances[:10].values(
            'route_no', 'avg_epkm', 'total_revenue', 'trip_count'
        ))
        
        underperformers = list(route_performances.reverse()[:10].values(
            'route_no', 'avg_epkm', 'total_revenue', 'trip_count'
        ))
        
        # Calculate industry average
        industry_avg = route_performances.aggregate(
            avg_epkm=Avg('avg_epkm')
        )['avg_epkm']
        
        # Create or update comparison record
        comparison, created = cls.objects.get_or_create(
            comparison_date=target_date,
            defaults={
                'best_performing_routes': best_performers,
                'underperforming_routes': underperformers,
                'total_routes_analyzed': route_performances.count(),
                'industry_avg_epkm': industry_avg,
            }
        )
        
        if not created:
            comparison.best_performing_routes = best_performers
            comparison.underperforming_routes = underperformers
            comparison.total_routes_analyzed = route_performances.count()
            comparison.industry_avg_epkm = industry_avg
            comparison.save()
        
        return comparison

class RoutePerformanceTrend(models.Model):
    """Track route performance trends over time"""
    
    route_no = models.CharField(max_length=20)
    date = models.DateField()
    epkm = models.DecimalField(max_digits=10, decimal_places=2)
    revenue = models.DecimalField(max_digits=12, decimal_places=2)
    trip_count = models.IntegerField()
    
    # Trend indicators
    epkm_trend = models.CharField(max_length=20, null=True, blank=True)  # 'improving', 'declining', 'stable'
    performance_category = models.CharField(max_length=20, null=True, blank=True)  # 'high', 'medium', 'low'
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = (('route_no', 'date'),)
        indexes = [
            models.Index(fields=['route_no', 'date']),
            models.Index(fields=['epkm_trend']),
        ]
    
    def __str__(self):
        return f"Route {self.route_no} - {self.date}: EPKM {self.epkm}"
