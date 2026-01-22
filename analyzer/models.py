from django.db import models
from django.db.models import Q
from bus_route.models import Route, Schedule
from datetime import datetime, timedelta, date
from django.utils import timezone

class RouteAnalysis(models.Model):
    route_no = models.CharField(max_length=20)
    analysis_date = models.DateTimeField(auto_now_add=True)
    selected_date = models.DateField(default=date.today)
    time_period_start = models.TimeField()
    time_period_end = models.TimeField()
    total_buses = models.IntegerField(default=0)
    overlap_score = models.FloatField(default=0.0)
    
    class Meta:
        unique_together = (('route_no', 'selected_date', 'time_period_start', 'time_period_end'),)
    
    def __str__(self):
        return f"Analysis for Route {self.route_no} on {self.selected_date} ({self.time_period_start}-{self.time_period_end})"

class BusOverlapData(models.Model):
    route_no = models.CharField(max_length=20)
    schedule_no = models.CharField(max_length=20)
    trip_no = models.IntegerField()
    selected_date = models.DateField(default=date.today)
    start_time = models.TimeField()
    end_time = models.TimeField()
    service_type = models.CharField(max_length=50)
    estimated_passengers = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = (('route_no', 'schedule_no', 'trip_no', 'selected_date'),)
    
    def __str__(self):
        return f"Bus {self.schedule_no}-{self.trip_no} on Route {self.route_no} ({self.selected_date})"
    
    @classmethod
    def get_overlapping_buses(cls, route_no, selected_date, start_time, end_time):
        """Get all buses that overlap in the given time period for a specific route and date"""
        return cls.objects.filter(
            route_no=route_no,
            selected_date=selected_date,
            start_time__lt=end_time,
            end_time__gt=start_time
        ).order_by('start_time')
    
    @classmethod
    def calculate_overlap_intensity(cls, route_no, selected_date, time_interval_minutes=30):
        """Calculate overlap intensity across different time intervals for a specific date"""
        buses = cls.objects.filter(route_no=route_no, selected_date=selected_date).order_by('start_time')
        if not buses.exists():
            return []
        
        # Create time intervals
        earliest_time = buses.first().start_time
        latest_time = buses.last().end_time
        
        intervals = []
        current_time = datetime.combine(selected_date, earliest_time)
        end_datetime = datetime.combine(selected_date, latest_time)
        
        while current_time < end_datetime:
            interval_end = current_time + timedelta(minutes=time_interval_minutes)
            overlapping_count = cls.get_overlapping_buses(
                route_no, 
                selected_date,
                current_time.time(), 
                interval_end.time()
            ).count()
            
            intervals.append({
                'start_time': current_time.time(),
                'end_time': interval_end.time(),
                'bus_count': overlapping_count
            })
            
            current_time = interval_end
        
        return intervals
