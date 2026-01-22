from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Count, Q
from datetime import date, timedelta
from depot_portal.models import Depot, Employee, ScheduleAssignment, Attendance
import csv


@login_required
def office_dashboard(request):
    total_depots = Depot.objects.filter(is_active=True).count()
    total_employees = Employee.objects.filter(is_active=True).count()
    
    today = date.today()
    todays_assignments = ScheduleAssignment.objects.filter(date=today).count()
    present_today = Attendance.objects.filter(date=today, status='present').count()
    
    # Recent attendance summary by depot
    depot_summary = []
    for depot in Depot.objects.filter(is_active=True)[:5]:
        depot_employees = Employee.objects.filter(depot=depot, is_active=True).count()
        depot_present = Attendance.objects.filter(
            employee__depot=depot,
            date=today,
            status='present'
        ).count()
        
        depot_summary.append({
            'depot': depot,
            'total_employees': depot_employees,
            'present_today': depot_present,
            'attendance_rate': round((depot_present / depot_employees * 100) if depot_employees > 0 else 0, 1)
        })
    
    context = {
        'total_depots': total_depots,
        'total_employees': total_employees,
        'todays_assignments': todays_assignments,
        'present_today': present_today,
        'depot_summary': depot_summary,
    }
    return render(request, 'main_office/dashboard.html', context)


@login_required
def attendance_report(request):
    depots = Depot.objects.filter(is_active=True)
    
    # Date range filter
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    if request.GET.get('start_date'):
        start_date = date.fromisoformat(request.GET.get('start_date'))
    if request.GET.get('end_date'):
        end_date = date.fromisoformat(request.GET.get('end_date'))
    
    selected_depot = request.GET.get('depot')
    
    # Filter attendance records
    attendance_query = Attendance.objects.filter(
        date__range=[start_date, end_date]
    )
    
    if selected_depot:
        attendance_query = attendance_query.filter(employee__depot_id=selected_depot)
    
    attendance_records = attendance_query.select_related('employee', 'employee__depot').order_by('-date', 'employee__depot__depot_name')
    
    context = {
        'attendance_records': attendance_records,
        'depots': depots,
        'selected_depot': selected_depot,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'main_office/attendance_report.html', context)


@login_required
def depot_overview(request):
    depots = Depot.objects.filter(is_active=True)
    
    depot_stats = []
    for depot in depots:
        total_emp = Employee.objects.filter(depot=depot, is_active=True).count()
        drivers = Employee.objects.filter(depot=depot, role='driver', is_active=True).count()
        conductors = Employee.objects.filter(depot=depot, role='conductor', is_active=True).count()
        
        today = date.today()
        present_today = Attendance.objects.filter(
            employee__depot=depot,
            date=today,
            status='present'
        ).count()
        
        depot_stats.append({
            'depot': depot,
            'total_employees': total_emp,
            'drivers': drivers,
            'conductors': conductors,
            'present_today': present_today,
            'attendance_rate': round((present_today / total_emp * 100) if total_emp > 0 else 0, 1)
        })
    
    context = {
        'depot_stats': depot_stats,
    }
    return render(request, 'main_office/depot_overview.html', context)


@login_required
def employee_analytics(request):
    total_employees = Employee.objects.filter(is_active=True).count()
    total_drivers = Employee.objects.filter(role='driver', is_active=True).count()
    total_conductors = Employee.objects.filter(role='conductor', is_active=True).count()
    
    # Weekly attendance trends
    week_ago = date.today() - timedelta(days=7)
    daily_attendance = []
    
    for i in range(7):
        check_date = week_ago + timedelta(days=i)
        present_count = Attendance.objects.filter(
            date=check_date,
            status='present'
        ).count()
        daily_attendance.append({
            'date': check_date,
            'present': present_count
        })
    
    context = {
        'total_employees': total_employees,
        'total_drivers': total_drivers,
        'total_conductors': total_conductors,
        'daily_attendance': daily_attendance,
    }
    return render(request, 'main_office/employee_analytics.html', context)


@login_required
def export_attendance(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Employee ID', 'Employee Name', 'Depot', 'Status', 'Check In', 'Check Out'])
    
    # Get attendance records for export
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    if request.GET.get('start_date'):
        start_date = date.fromisoformat(request.GET.get('start_date'))
    if request.GET.get('end_date'):
        end_date = date.fromisoformat(request.GET.get('end_date'))
    
    attendance_records = Attendance.objects.filter(
        date__range=[start_date, end_date]
    ).select_related('employee', 'employee__depot').order_by('-date')
    
    for record in attendance_records:
        writer.writerow([
            record.date,
            record.employee.employee_id,
            record.employee.employee_name,
            record.employee.depot.depot_name,
            record.status,
            record.check_in_time or '',
            record.check_out_time or '',
        ])
    
    return response