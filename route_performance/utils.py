from django.db.models import Q, Avg, Sum, Count
from django.utils import timezone
from datetime import date, timedelta
from bus_route.models import Trip, Schedule, Route
from .models import RoutePerformanceMetrics, RouteComparison, RoutePerformanceTrend

class RoutePerformanceCalculator:
    """Utility class for calculating route performance metrics"""
    
    @staticmethod
    def get_route_epkm_data(route_no=None, start_date=None, end_date=None):
        """Get EPKM data for routes with optional filtering"""
        if start_date is None:
            start_date = date.today() - timedelta(days=30)
        if end_date is None:
            end_date = date.today()
        
        # Base query for trips with revenue data
        trips_query = Trip.objects.filter(
            revenue__isnull=False,
            date__range=[start_date, end_date]
        )
        
        if route_no:
            trips_query = trips_query.filter(
                schedule_no__in=Schedule.objects.filter(route_no=route_no).values_list('schedule_no', flat=True)
            )
        
        # Calculate EPKM for each trip
        route_data = {}
        for trip in trips_query:
            try:
                schedule = Schedule.objects.get(schedule_no=trip.schedule_no, trip_no=trip.trip_no)
                trip_route = schedule.route_no
                
                # Calculate EPKM manually since it's a property
                epkm_value = trip.epkm  # This uses the property method
                
                if trip_route not in route_data:
                    route_data[trip_route] = {
                        'epkm_values': [],
                        'total_revenue': 0,
                        'total_km': 0,
                        'trip_count': 0
                    }
                
                # Always add trip data, even if EPKM is None
                route_data[trip_route]['total_revenue'] += trip.revenue or 0
                route_data[trip_route]['trip_count'] += 1
                
                if epkm_value is not None:
                    route_data[trip_route]['epkm_values'].append(epkm_value)
                
                if schedule.trip_km:
                    route_data[trip_route]['total_km'] += schedule.trip_km
            except Schedule.DoesNotExist:
                continue
        
        # Calculate averages and rankings
        route_performance = []
        for route_no, data in route_data.items():
            avg_epkm = sum(data['epkm_values']) / len(data['epkm_values']) if data['epkm_values'] else 0
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
    def get_top_performers(limit=10, start_date=None, end_date=None):
        """Get top performing routes by EPKM"""
        performance_data = RoutePerformanceCalculator.get_route_epkm_data(start_date=start_date, end_date=end_date)
        return performance_data[:limit]
    
    @staticmethod
    def get_underperformers(limit=10, start_date=None, end_date=None):
        """Get underperforming routes by EPKM"""
        performance_data = RoutePerformanceCalculator.get_route_epkm_data(start_date=start_date, end_date=end_date)
        return performance_data[-limit:]
    
    @staticmethod
    def calculate_industry_benchmarks(start_date=None, end_date=None):
        """Calculate industry benchmarks and averages"""
        performance_data = RoutePerformanceCalculator.get_route_epkm_data(start_date=start_date, end_date=end_date)
        
        if not performance_data:
            return None
        
        epkm_values = [route['avg_epkm'] for route in performance_data]
        revenue_values = [route['total_revenue'] for route in performance_data]
        
        benchmarks = {
            'avg_epkm': round(sum(epkm_values) / len(epkm_values), 2),
            'median_epkm': round(sorted(epkm_values)[len(epkm_values) // 2], 2),
            'max_epkm': max(epkm_values),
            'min_epkm': min(epkm_values),
            'total_routes': len(performance_data),
            'avg_revenue': round(sum(revenue_values) / len(revenue_values), 2),
            'total_revenue': sum(revenue_values),
        }
        
        return benchmarks
    
    @staticmethod
    def bulk_calculate_performance(start_date=None, end_date=None, period_type='daily'):
        """Bulk calculate and store performance metrics for all routes"""
        if start_date is None:
            start_date = date.today() - timedelta(days=30)
        if end_date is None:
            end_date = date.today()
        
        performance_data = RoutePerformanceCalculator.get_route_epkm_data(start_date=start_date, end_date=end_date)
        
        # Store performance metrics
        for route_data in performance_data:
            RoutePerformanceMetrics.calculate_route_performance(
                route_no=route_data['route_no'],
                start_date=start_date,
                end_date=end_date,
                period_type=period_type
            )
        
        # Generate comparison data
        RouteComparison.generate_daily_comparison(target_date=end_date)
        
        return len(performance_data)

class RouteAnalyzer:
    """Advanced route analysis utilities"""
    
    @staticmethod
    def get_route_trends(route_no, days=30):
        """Get performance trends for a specific route"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        trends = RoutePerformanceTrend.objects.filter(
            route_no=route_no,
            date__range=[start_date, end_date]
        ).order_by('date')
        
        return list(trends.values('date', 'epkm', 'revenue', 'trip_count'))
    
    @staticmethod
    def categorize_route_performance(epkm_value):
        """Categorize route performance based on EPKM value"""
        if epkm_value >= 15:
            return 'high'
        elif epkm_value >= 10:
            return 'medium'
        else:
            return 'low'
    
    @staticmethod
    def analyze_route_stability(route_no, days=30):
        """Analyze route performance stability"""
        trends = RouteAnalyzer.get_route_trends(route_no, days)
        
        if len(trends) < 7:
            return {'stability': 'insufficient_data', 'trend': 'unknown'}
        
        epkm_values = [trend['epkm'] for trend in trends]
        
        # Calculate coefficient of variation
        avg_epkm = sum(epkm_values) / len(epkm_values)
        variance = sum((x - avg_epkm) ** 2 for x in epkm_values) / len(epkm_values)
        std_dev = variance ** 0.5
        cv = std_dev / avg_epkm if avg_epkm > 0 else 0
        
        # Determine stability
        if cv < 0.1:
            stability = 'very_stable'
        elif cv < 0.2:
            stability = 'stable'
        elif cv < 0.3:
            stability = 'moderate'
        else:
            stability = 'unstable'
        
        # Determine trend
        if len(epkm_values) >= 3:
            recent_avg = sum(epkm_values[-3:]) / 3
            earlier_avg = sum(epkm_values[:3]) / 3
            
            if recent_avg > earlier_avg * 1.05:
                trend = 'improving'
            elif recent_avg < earlier_avg * 0.95:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'unknown'
        
        return {
            'stability': stability,
            'trend': trend,
            'coefficient_of_variation': round(cv, 3),
            'avg_epkm': round(avg_epkm, 2),
            'std_deviation': round(std_dev, 2)
        }