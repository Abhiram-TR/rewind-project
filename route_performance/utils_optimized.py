from django.db import models
from django.db.models import Avg, Sum, Count, F, Q
from bus_route.models import Trip, Schedule
from datetime import date, timedelta

class OptimizedRoutePerformanceCalculator:
    """Optimized version with database-level aggregations"""
    
    @staticmethod
    def get_route_epkm_data_fast(route_no=None, start_date=None, end_date=None):
        """Optimized version using database aggregation"""
        if start_date is None:
            start_date = date.today() - timedelta(days=30)
        if end_date is None:
            end_date = date.today()
        
        # Use database-level JOIN and aggregation instead of Python loops
        query = Trip.objects.filter(
            revenue__isnull=False,
            date__range=[start_date, end_date]
        ).select_related(
            # This prevents N+1 queries by JOINing schedules
        ).values(
            # Group by route using schedule lookup
            'schedule_no'
        ).annotate(
            total_revenue=Sum('revenue'),
            trip_count=Count('id'),
            avg_revenue=Avg('revenue')
        )
        
        if route_no:
            # Filter by route if specified
            route_schedules = Schedule.objects.filter(route_no=route_no).values_list('schedule_no', flat=True)
            query = query.filter(schedule_no__in=route_schedules)
        
        # Get schedule info in one query
        schedule_lookup = {
            s.schedule_no: {'route_no': s.route_no, 'trip_km': s.trip_km}
            for s in Schedule.objects.all()
        }
        
        route_data = {}
        
        for trip_data in query:
            schedule_no = trip_data['schedule_no']
            if schedule_no not in schedule_lookup:
                continue
                
            schedule_info = schedule_lookup[schedule_no]
            route_no = schedule_info['route_no']
            trip_km = schedule_info['trip_km'] or 0
            
            if route_no not in route_data:
                route_data[route_no] = {
                    'total_revenue': 0,
                    'total_km': 0,
                    'trip_count': 0,
                    'epkm_values': []
                }
            
            # Calculate EPKM at database level
            if trip_km > 0:
                avg_epkm = trip_data['avg_revenue'] / trip_km
                route_data[route_no]['epkm_values'].append(avg_epkm)
            
            route_data[route_no]['total_revenue'] += trip_data['total_revenue']
            route_data[route_no]['total_km'] += trip_km * trip_data['trip_count']
            route_data[route_no]['trip_count'] += trip_data['trip_count']
        
        # Build final result
        route_performance = []
        for route_no, data in route_data.items():
            if data['epkm_values']:
                avg_epkm = sum(data['epkm_values']) / len(data['epkm_values'])
                route_performance.append({
                    'route_no': route_no,
                    'avg_epkm': round(avg_epkm, 2),
                    'total_revenue': data['total_revenue'],
                    'total_km': data['total_km'],
                    'trip_count': data['trip_count'],
                    'revenue_per_trip': round(data['total_revenue'] / data['trip_count'], 2) if data['trip_count'] > 0 else 0
                })
        
        # Sort by EPKM descending
        route_performance.sort(key=lambda x: x['avg_epkm'], reverse=True)
        return route_performance
    
    @staticmethod
    def get_route_epkm_data_ultra_fast(route_no=None, start_date=None, end_date=None):
        """Ultra-fast version using raw SQL"""
        from django.db import connection
        
        if start_date is None:
            start_date = date.today() - timedelta(days=30)
        if end_date is None:
            end_date = date.today()
        
        # Raw SQL query matching the original (buggy) logic
        # This matches the original code's behavior of requiring exact schedule_no + trip_no matches
        sql = """
        SELECT 
            s.route_no,
            COUNT(t.id) as trip_count,
            SUM(t.revenue) as total_revenue,
            SUM(s.trip_km) as total_km,
            AVG(t.revenue / s.trip_km) as avg_epkm
        FROM bus_route_trip t
        JOIN bus_route_schedule s ON t.schedule_no = s.schedule_no AND t.trip_no = s.trip_no
        WHERE t.date >= %s AND t.date <= %s AND t.revenue IS NOT NULL AND s.trip_km IS NOT NULL AND s.trip_km > 0
        """
        
        params = [start_date, end_date]
        
        if route_no:
            sql += " AND s.route_no = %s"
            params.append(route_no)
        
        sql += """
        GROUP BY s.route_no
        HAVING COUNT(t.id) > 0 AND SUM(s.trip_km) > 0
        ORDER BY avg_epkm DESC
        """
        
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Format results
        route_performance = []
        for row in results:
            route_performance.append({
                'route_no': row['route_no'],
                'avg_epkm': round(float(row['avg_epkm']), 2),
                'total_revenue': float(row['total_revenue']),
                'total_km': float(row['total_km']),
                'trip_count': int(row['trip_count']),
                'revenue_per_trip': round(float(row['total_revenue']) / int(row['trip_count']), 2) if int(row['trip_count']) > 0 else 0
            })
        
        return route_performance