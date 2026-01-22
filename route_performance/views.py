from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db.models import Avg, Sum, Count, Q
from datetime import date, timedelta, datetime
import json

from .models import RoutePerformanceMetrics, RouteComparison, RoutePerformanceTrend
from .utils import RoutePerformanceCalculator, RouteAnalyzer
from .utils_optimized import OptimizedRoutePerformanceCalculator
from bus_route.models import Trip, Schedule

class RoutePerformanceAPIView(View):
    """API endpoints for route performance data"""
    
    def get(self, request):
        """Get route performance overview"""
        try:
            # Get date range from request
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            route_no = request.GET.get('route_no')
            
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            else:
                start_date = date.today() - timedelta(days=30)
            
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            else:
                end_date = date.today()
            
            # Get performance data
            performance_data = RoutePerformanceCalculator.get_route_epkm_data(
                route_no=route_no,
                start_date=start_date,
                end_date=end_date
            )
            
            # Get benchmarks (simplified to avoid timeout)
            benchmarks = None
            if performance_data:
                epkm_values = [route['avg_epkm'] for route in performance_data if route['avg_epkm']]
                if epkm_values:
                    benchmarks = {
                        'avg_epkm': round(sum(epkm_values) / len(epkm_values), 2),
                        'max_epkm': max(epkm_values),
                        'min_epkm': min(epkm_values),
                        'total_routes': len(performance_data),
                        'total_revenue': sum(route['total_revenue'] for route in performance_data)
                    }
            
            return JsonResponse({
                'success': True,
                'data': {
                    'routes': performance_data,
                    'benchmarks': benchmarks,
                    'date_range': {
                        'start': start_date.isoformat(),
                        'end': end_date.isoformat()
                    }
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

class TopPerformersAPIView(View):
    """API for top performing routes"""
    
    def get(self, request):
        try:
            limit = int(request.GET.get('limit', 10))
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            else:
                start_date = date.today() - timedelta(days=7)  # Default to last week
                
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            else:
                end_date = date.today()
            
            # Limit date range to prevent timeouts
            date_diff = (end_date - start_date).days
            if date_diff > 30:
                start_date = end_date - timedelta(days=30)
            
            # Use optimized calculator
            all_performance = OptimizedRoutePerformanceCalculator.get_route_epkm_data_ultra_fast(
                start_date=start_date,
                end_date=end_date
            )
            top_performers = all_performance[:limit]
            
            return JsonResponse({
                'success': True,
                'data': {
                    'top_performers': top_performers,
                    'count': len(top_performers)
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

class UnderperformersAPIView(View):
    """API for underperforming routes"""
    
    def get(self, request):
        try:
            limit = int(request.GET.get('limit', 10))
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            else:
                start_date = date.today() - timedelta(days=7)  # Default to last week
                
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            else:
                end_date = date.today()
            
            # Limit date range to prevent timeouts
            date_diff = (end_date - start_date).days
            if date_diff > 30:
                start_date = end_date - timedelta(days=30)
            
            # Use optimized calculator
            all_performance = OptimizedRoutePerformanceCalculator.get_route_epkm_data_ultra_fast(
                start_date=start_date,
                end_date=end_date
            )
            underperformers = all_performance[-limit:] if len(all_performance) >= limit else all_performance
            
            return JsonResponse({
                'success': True,
                'data': {
                    'underperformers': underperformers,
                    'count': len(underperformers)
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

class RouteComparisonAPIView(View):
    """API for route comparison data"""
    
    def get(self, request):
        try:
            comparison_date = request.GET.get('date')
            
            if comparison_date:
                comparison_date = datetime.strptime(comparison_date, '%Y-%m-%d').date()
            else:
                comparison_date = date.today()
            
            # Get or create comparison data
            comparison = RouteComparison.generate_daily_comparison(comparison_date)
            
            if not comparison:
                return JsonResponse({
                    'success': False,
                    'error': 'No data available for the specified date'
                }, status=404)
            
            return JsonResponse({
                'success': True,
                'data': {
                    'comparison_date': comparison.comparison_date.isoformat(),
                    'best_performing_routes': comparison.best_performing_routes,
                    'underperforming_routes': comparison.underperforming_routes,
                    'total_routes_analyzed': comparison.total_routes_analyzed,
                    'industry_avg_epkm': float(comparison.industry_avg_epkm) if comparison.industry_avg_epkm else None
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

class RouteTrendsAPIView(View):
    """API for route performance trends"""
    
    def get(self, request):
        try:
            route_no = request.GET.get('route_no')
            days = int(request.GET.get('days', 30))
            
            if not route_no:
                return JsonResponse({
                    'success': False,
                    'error': 'route_no parameter is required'
                }, status=400)
            
            # Get trend data
            trends = RouteAnalyzer.get_route_trends(route_no, days)
            
            # Get stability analysis
            stability = RouteAnalyzer.analyze_route_stability(route_no, days)
            
            return JsonResponse({
                'success': True,
                'data': {
                    'route_no': route_no,
                    'trends': trends,
                    'stability_analysis': stability,
                    'period_days': days
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

class DashboardView(View):
    """Main dashboard view"""
    
    def get(self, request):
        try:
            # Get recent comparison data
            recent_comparison = RouteComparison.objects.order_by('-comparison_date').first()
            
            # Don't load any data initially - wait for user to select date range
            # Just find the available data range for display
            latest_trip = Trip.objects.order_by('-date').first()
            earliest_trip = Trip.objects.order_by('date').first()
            
            context = {
                'recent_comparison': recent_comparison,
                'performance_summary': None,  # Don't load initially
                'sample_routes_count': 0,     # Don't show count initially
                'date_range': {
                    'available_start': earliest_trip.date.isoformat() if earliest_trip else None,
                    'available_end': latest_trip.date.isoformat() if latest_trip else None,
                    'start': None,  # No initial range
                    'end': None
                },
                'show_initial_data': False  # Flag to hide initial data display
            }
            
            return render(request, 'route_performance/dashboard.html', context)
            
        except Exception as e:
            return render(request, 'route_performance/error.html', {'error': str(e)})

@method_decorator(csrf_exempt, name='dispatch')
class BulkCalculateView(View):
    """Bulk calculate performance metrics"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            period_type = data.get('period_type', 'daily')
            
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # Bulk calculate performance metrics
            routes_processed = RoutePerformanceCalculator.bulk_calculate_performance(
                start_date=start_date,
                end_date=end_date,
                period_type=period_type
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully processed {routes_processed} routes',
                'routes_processed': routes_processed
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

class RouteDetailView(View):
    """Detailed view for individual route performance"""
    
    def get(self, request, route_no):
        try:
            # Get recent performance data
            today = date.today()
            last_30_days = today - timedelta(days=30)
            
            route_data = RoutePerformanceCalculator.get_route_epkm_data(
                route_no=route_no,
                start_date=last_30_days,
                end_date=today
            )
            
            if not route_data:
                return JsonResponse({
                    'success': False,
                    'error': f'No data found for route {route_no}'
                }, status=404)
            
            # Get trend analysis
            trends = RouteAnalyzer.get_route_trends(route_no, 30)
            stability = RouteAnalyzer.analyze_route_stability(route_no, 30)
            
            # Get recent trips for this route
            recent_trips = Trip.objects.filter(
                schedule_no__in=Schedule.objects.filter(route_no=route_no).values_list('schedule_no', flat=True),
                date__range=[last_30_days, today],
                revenue__isnull=False
            ).order_by('-date')[:10]
            
            trip_data = []
            for trip in recent_trips:
                trip_data.append({
                    'date': trip.date.isoformat(),
                    'schedule_no': trip.schedule_no,
                    'trip_no': trip.trip_no,
                    'revenue': trip.revenue,
                    'epkm': trip.epkm
                })
            
            return JsonResponse({
                'success': True,
                'data': {
                    'route_no': route_no,
                    'performance_summary': route_data[0],
                    'trends': trends,
                    'stability_analysis': stability,
                    'recent_trips': trip_data
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
