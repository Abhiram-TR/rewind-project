from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Sum
from bus_route.models import Route, Schedule, Trip
from passenger_distribution.models import KsrtcFromData, KsrtcToData
from .models import BusOverlapData, RouteAnalysis
from datetime import datetime, time, date
import json
import random

def estimate_passenger_count(route_no, selected_date, start_time, end_time):
    """Estimate passenger count for a bus trip based on historical data"""
    try:
        # Format date and time for passenger data lookup
        date_str = selected_date.strftime('%Y-%m-%d')
        hour_start = start_time.hour
        hour_end = end_time.hour
        
        # Get route stops for the given route
        route_stops = Route.objects.filter(route_no=route_no).values_list('stop_name', flat=True)
        
        total_passengers = 0
        
        # Look for passenger data within the time range
        for hour in range(hour_start, hour_end + 1):
            date_hour = f"{date_str} {hour:02d}:00:00"
            
            # Get passenger data from/to stops on this route
            from_passengers = KsrtcFromData.objects.filter(
                date_hour__startswith=date_str,
                from_stop_name__in=route_stops
            ).aggregate(total=Sum('total_passenger'))['total'] or 0
            
            to_passengers = KsrtcToData.objects.filter(
                date_hour__startswith=date_str,
                to_stop_name__in=route_stops
            ).aggregate(total=Sum('total_passenger'))['total'] or 0
            
            # Average the from and to passengers to avoid double counting
            total_passengers += (from_passengers + to_passengers) // 2
        
        # If no historical data, estimate based on time of day and service type
        if total_passengers == 0:
            # Peak hours (7-9 AM, 5-7 PM): higher passenger count
            if (7 <= hour_start <= 9) or (17 <= hour_start <= 19):
                base_passengers = random.randint(35, 50)
            # Regular hours: moderate passenger count
            elif 6 <= hour_start <= 22:
                base_passengers = random.randint(20, 35)
            # Off-peak hours: lower passenger count
            else:
                base_passengers = random.randint(10, 25)
            
            # Adjust based on trip duration (longer trips = more passengers)
            duration_hours = (datetime.combine(date.today(), end_time) - 
                            datetime.combine(date.today(), start_time)).seconds / 3600
            total_passengers = int(base_passengers * max(1, duration_hours))
        
        return max(1, total_passengers)  # Ensure at least 1 passenger
        
    except Exception as e:
        # Fallback to a reasonable estimate
        return random.randint(15, 40)

def analyzer_home(request):
    """Main analyzer interface with route selection"""
    routes = Route.objects.values('route_no').distinct().order_by('route_no')
    return render(request, 'analyzer/analyzer_home.html', {'routes': routes})

def get_route_data(request):
    """Get all available routes for selection"""
    routes = Route.objects.values('route_no').distinct().order_by('route_no')
    route_list = [{'route_no': route['route_no']} for route in routes]
    return JsonResponse({'routes': route_list})

@csrf_exempt
def analyze_route_overlap(request):
    """Analyze bus overlaps for a specific route, date, and time period"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            route_no = data.get('route_no')
            selected_date = data.get('selected_date')
            start_time = data.get('start_time')
            end_time = data.get('end_time')
            interval_minutes = data.get('interval_minutes', 30)
            
            if not all([route_no, selected_date, start_time, end_time]):
                return JsonResponse({'error': 'Missing required parameters'}, status=400)
            
            # Convert strings to appropriate objects
            selected_date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
            start_time_obj = datetime.strptime(start_time, '%H:%M').time()
            end_time_obj = datetime.strptime(end_time, '%H:%M').time()
            
            # Get schedules for the route
            schedules = Schedule.objects.filter(route_no=route_no.upper())
            
            # Check if there are actual trips for this route on the selected date
            actual_trips = Trip.objects.filter(
                schedule_no__in=schedules.values_list('schedule_no', flat=True),
                date=selected_date_obj
            )
            
            # Create or update BusOverlapData for the selected date
            BusOverlapData.objects.filter(route_no=route_no.upper(), selected_date=selected_date_obj).delete()
            
            # If we have actual trip data, use it; otherwise use schedule data
            if actual_trips.exists():
                for trip in actual_trips:
                    try:
                        schedule = schedules.get(schedule_no=trip.schedule_no, trip_no=trip.trip_no)
                        if schedule.start_time and schedule.end_time:
                            # Estimate passenger count for this trip
                            passenger_count = estimate_passenger_count(
                                route_no.upper(), 
                                selected_date_obj, 
                                schedule.start_time, 
                                schedule.end_time
                            )
                            
                            BusOverlapData.objects.create(
                                route_no=route_no.upper(),
                                schedule_no=schedule.schedule_no,
                                trip_no=schedule.trip_no,
                                selected_date=selected_date_obj,
                                start_time=schedule.start_time,
                                end_time=schedule.end_time,
                                service_type=schedule.service_type,
                                estimated_passengers=passenger_count
                            )
                    except Schedule.DoesNotExist:
                        continue
            else:
                # Use schedule data as fallback
                for schedule in schedules:
                    if schedule.start_time and schedule.end_time:
                        # Estimate passenger count for this trip
                        passenger_count = estimate_passenger_count(
                            route_no.upper(), 
                            selected_date_obj, 
                            schedule.start_time, 
                            schedule.end_time
                        )
                        
                        BusOverlapData.objects.create(
                            route_no=route_no.upper(),
                            schedule_no=schedule.schedule_no,
                            trip_no=schedule.trip_no,
                            selected_date=selected_date_obj,
                            start_time=schedule.start_time,
                            end_time=schedule.end_time,
                            service_type=schedule.service_type,
                            estimated_passengers=passenger_count
                        )
            
            # Calculate overlap intensity
            overlap_data = BusOverlapData.calculate_overlap_intensity(
                route_no.upper(), 
                selected_date_obj,
                interval_minutes
            )
            
            # Filter data for the selected time period
            filtered_overlap = []
            for interval in overlap_data:
                if (interval['start_time'] >= start_time_obj and 
                    interval['end_time'] <= end_time_obj):
                    filtered_overlap.append({
                        'start_time': interval['start_time'].strftime('%H:%M'),
                        'end_time': interval['end_time'].strftime('%H:%M'),
                        'bus_count': interval['bus_count']
                    })
            
            # Get overlapping buses for the entire period
            overlapping_buses = BusOverlapData.get_overlapping_buses(
                route_no.upper(), 
                selected_date_obj,
                start_time_obj, 
                end_time_obj
            )
            
            bus_details = []
            total_passengers_in_period = 0
            for bus in overlapping_buses:
                bus_details.append({
                    'schedule_no': bus.schedule_no,
                    'trip_no': bus.trip_no,
                    'start_time': bus.start_time.strftime('%H:%M'),
                    'end_time': bus.end_time.strftime('%H:%M'),
                    'service_type': bus.service_type,
                    'estimated_passengers': bus.estimated_passengers
                })
                total_passengers_in_period += bus.estimated_passengers
            
            # Save analysis
            RouteAnalysis.objects.update_or_create(
                route_no=route_no.upper(),
                selected_date=selected_date_obj,
                time_period_start=start_time_obj,
                time_period_end=end_time_obj,
                defaults={
                    'total_buses': len(bus_details),
                    'overlap_score': sum(interval['bus_count'] for interval in filtered_overlap) / len(filtered_overlap) if filtered_overlap else 0
                }
            )
            
            # Calculate passenger overlap impact
            passenger_overlap_impact = 0
            if len(bus_details) > 1:
                passenger_overlap_impact = sum(bus['estimated_passengers'] for bus in bus_details) - max((bus['estimated_passengers'] for bus in bus_details), default=0)
            
            return JsonResponse({
                'success': True,
                'route_no': route_no.upper(),
                'selected_date': selected_date,
                'time_period': f"{start_time} - {end_time}",
                'total_buses': len(bus_details),
                'total_passengers': total_passengers_in_period,
                'overlap_intervals': filtered_overlap,
                'bus_details': bus_details,
                'analysis_summary': {
                    'peak_overlap': max([interval['bus_count'] for interval in filtered_overlap]) if filtered_overlap else 0,
                    'average_overlap': sum([interval['bus_count'] for interval in filtered_overlap]) / len(filtered_overlap) if filtered_overlap else 0,
                    'passenger_overlap_impact': passenger_overlap_impact,
                    'avg_passengers_per_bus': total_passengers_in_period // len(bus_details) if bus_details else 0
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def get_analysis_history(request):
    """Get historical analysis data"""
    analyses = RouteAnalysis.objects.all().order_by('-analysis_date')[:10]
    history = []
    
    for analysis in analyses:
        history.append({
            'route_no': analysis.route_no,
            'selected_date': analysis.selected_date.strftime('%Y-%m-%d'),
            'analysis_date': analysis.analysis_date.strftime('%Y-%m-%d %H:%M'),
            'time_period': f"{analysis.time_period_start.strftime('%H:%M')} - {analysis.time_period_end.strftime('%H:%M')}",
            'total_buses': analysis.total_buses,
            'overlap_score': round(analysis.overlap_score, 2)
        })
    
    return JsonResponse({'history': history})
