from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import datetime, date
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from bus_route.models import Schedule
from .models import DepotUser, Employee, ScheduleAssignment, Attendance, Depot
from .forms import DepotLoginForm, EmployeeForm, ScheduleAssignmentForm, AttendanceForm
import json


def depot_login(request):
    if request.method == 'POST':
        form = DepotLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            try:
                depot_user = DepotUser.objects.get(username=username, is_active=True)
                if depot_user.check_password(password):
                    request.session['depot_user_id'] = depot_user.depot_user_id
                    depot_user.last_login = timezone.now()
                    depot_user.save()
                    messages.success(request, f"Welcome back, {depot_user.full_name}!")
                    return redirect('depot_portal:dashboard')
                else:
                    messages.error(request, "Invalid credentials.")
            except DepotUser.DoesNotExist:
                messages.error(request, "Invalid credentials.")
    else:
        form = DepotLoginForm()
    return render(request, 'depot_portal/login.html', {'form': form})


def depot_logout(request):
    request.session.flush()
    messages.info(request, "You have successfully logged out.")
    return redirect('depot_portal:login')


def depot_dashboard(request):
    if 'depot_user_id' not in request.session:
        return redirect('depot_portal:login')
    
    depot_user = get_object_or_404(DepotUser, depot_user_id=request.session['depot_user_id'])
    
    # Dashboard statistics
    today = date.today()
    total_employees = Employee.objects.filter(depot=depot_user.depot, is_active=True).count()
    todays_assignments = ScheduleAssignment.objects.filter(
        employee__depot=depot_user.depot, 
        date=today
    ).count()
    present_today = Attendance.objects.filter(
        employee__depot=depot_user.depot,
        date=today,
        status='present'
    ).count()
    
    context = {
        'depot_user': depot_user,
        'total_employees': total_employees,
        'todays_assignments': todays_assignments,
        'present_today': present_today,
    }
    return render(request, 'depot_portal/dashboard.html', context)


def employee_list(request):
    if 'depot_user_id' not in request.session:
        return redirect('depot_portal:login')
    
    depot_user = get_object_or_404(DepotUser, depot_user_id=request.session['depot_user_id'])
    
    # Start with base queryset
    employees = Employee.objects.filter(depot=depot_user.depot, is_active=True)
    
    # Apply role filter if provided
    role_filter = request.GET.get('role')
    if role_filter and role_filter in ['driver', 'conductor']:
        employees = employees.filter(role=role_filter)
    
    # Apply search filter if provided
    search_filter = request.GET.get('search')
    if search_filter:
        employees = employees.filter(
            Q(employee_name__icontains=search_filter) |
            Q(employee_id__icontains=search_filter) |
            Q(phone_number__icontains=search_filter) |
            Q(license_number__icontains=search_filter)
        )
    
    # Order results
    employees = employees.order_by('employee_name')
    
    return render(request, 'depot_portal/employee_list.html', {
        'employees': employees,
        'depot_user': depot_user,
        'current_role_filter': role_filter,
        'current_search_filter': search_filter,
    })


def employee_add(request):
    if 'depot_user_id' not in request.session:
        return redirect('depot_portal:login')
    
    depot_user = get_object_or_404(DepotUser, depot_user_id=request.session['depot_user_id'])
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save(commit=False)
            employee.depot = depot_user.depot
            employee.save()
            messages.success(request, f"Employee {employee.employee_name} added successfully!")
            return redirect('depot_portal:employee_list')
    else:
        form = EmployeeForm()
    
    return render(request, 'depot_portal/employee_form.html', {
        'form': form,
        'depot_user': depot_user,
        'action': 'Add'
    })


def employee_edit(request, employee_id):
    if 'depot_user_id' not in request.session:
        return redirect('depot_portal:login')
    
    depot_user = get_object_or_404(DepotUser, depot_user_id=request.session['depot_user_id'])
    employee = get_object_or_404(Employee, employee_id=employee_id, depot=depot_user.depot)
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, f"Employee {employee.employee_name} updated successfully!")
            return redirect('depot_portal:employee_list')
    else:
        form = EmployeeForm(instance=employee)
    
    return render(request, 'depot_portal/employee_form.html', {
        'form': form,
        'employee': employee,
        'depot_user': depot_user,
        'action': 'Edit'
    })


def employee_delete(request, employee_id):
    if 'depot_user_id' not in request.session:
        return redirect('depot_portal:login')
    
    depot_user = get_object_or_404(DepotUser, depot_user_id=request.session['depot_user_id'])
    employee = get_object_or_404(Employee, employee_id=employee_id, depot=depot_user.depot)
    
    if request.method == 'POST':
        employee.is_active = False
        employee.save()
        messages.success(request, f"Employee {employee.employee_name} deactivated successfully!")
        return redirect('depot_portal:employee_list')
    
    return render(request, 'depot_portal/employee_confirm_delete.html', {
        'employee': employee,
        'depot_user': depot_user
    })


def assignment_list(request):
    if 'depot_user_id' not in request.session:
        return redirect('depot_portal:login')
    
    depot_user = get_object_or_404(DepotUser, depot_user_id=request.session['depot_user_id'])
    
    # Start with base queryset
    all_assignments = ScheduleAssignment.objects.filter(
        employee__depot=depot_user.depot
    )
    
    # Apply status filter if provided
    status_filter = request.GET.get('status')
    if status_filter and status_filter in ['assigned', 'completed', 'cancelled']:
        all_assignments = all_assignments.filter(status=status_filter)
    
    # Apply date filter if provided
    date_filter = request.GET.get('date')
    if date_filter == 'today':
        from datetime import date
        all_assignments = all_assignments.filter(date=date.today())
    elif date_filter:
        try:
            from datetime import datetime
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            all_assignments = all_assignments.filter(date=filter_date)
        except ValueError:
            pass  # Invalid date format, ignore filter
    
    # Apply search filter if provided
    search_filter = request.GET.get('search')
    if search_filter:
        all_assignments = all_assignments.filter(
            Q(employee__employee_name__icontains=search_filter) |
            Q(employee__employee_id__icontains=search_filter) |
            Q(schedule_no__icontains=search_filter) |
            Q(route_no__icontains=search_filter)
        )
    
    # Order and get assignments
    all_assignments = all_assignments.order_by('-date', '-created_at')
    
    # Group assignments by employee, date, and schedule
    grouped_assignments = {}
    for assignment in all_assignments:
        # Create a unique key for grouping
        key = (assignment.employee.employee_id, assignment.date, assignment.schedule_no)
        
        if key not in grouped_assignments:
            grouped_assignments[key] = {
                'employee': assignment.employee,
                'date': assignment.date,
                'schedule_no': assignment.schedule_no,
                'status': assignment.status,
                'assigned_by': assignment.assigned_by,
                'created_at': assignment.created_at,
                'notes': assignment.notes,
                'trips': [],
                'assignment_ids': []
            }
        
        # Add trip information to the group
        grouped_assignments[key]['trips'].append({
            'trip_no': assignment.trip_no,
            'route_no': assignment.route_no,
            'assignment_id': assignment.assignment_id
        })
        grouped_assignments[key]['assignment_ids'].append(assignment.assignment_id)
    
    # Convert to list and sort by date (newest first)
    assignments = list(grouped_assignments.values())
    assignments.sort(key=lambda x: x['date'], reverse=True)
    
    return render(request, 'depot_portal/assignment_list.html', {
        'assignments': assignments,
        'depot_user': depot_user,
        'current_status_filter': status_filter,
        'current_date_filter': date_filter,
        'current_search_filter': search_filter,
    })


def assignment_add(request):
    if 'depot_user_id' not in request.session:
        return redirect('depot_portal:login')
    
    depot_user = get_object_or_404(DepotUser, depot_user_id=request.session['depot_user_id'])
    
    if request.method == 'POST':
        # Check if multiple trips were submitted
        trip_count = request.POST.get('trip_count')
        
        if trip_count and int(trip_count) >= 1:
            # Handle multiple trip submission
            employee_id = request.POST.get('employee')
            schedule_no = request.POST.get('schedule_no')
            assignment_date = request.POST.get('date')
            notes = request.POST.get('notes', '')
            
            # Validate required fields
            if not all([employee_id, schedule_no, assignment_date]):
                messages.error(request, "Employee, schedule, and date are required.")
                form = ScheduleAssignmentForm(depot=depot_user.depot)
                return render(request, 'depot_portal/assignment_form.html', {
                    'form': form,
                    'depot_user': depot_user,
                    'action': 'Add'
                })
            
            try:
                employee = Employee.objects.get(employee_id=employee_id, depot=depot_user.depot)
                assignment_date = datetime.strptime(assignment_date, '%Y-%m-%d').date()
                
                created_assignments = []
                errors = []
                
                # Process each trip
                for i in range(int(trip_count)):
                    trip_no = request.POST.get(f'trip_{i}')
                    route_no = request.POST.get(f'route_{i}')
                    
                    if trip_no and route_no:
                        # Check for duplicate assignment
                        existing_assignment = ScheduleAssignment.objects.filter(
                            employee=employee,
                            date=assignment_date,
                            schedule_no=schedule_no,
                            trip_no=int(trip_no)
                        ).first()
                        
                        if existing_assignment:
                            errors.append(f"Assignment for Trip {trip_no} already exists")
                        else:
                            # Create new assignment
                            assignment = ScheduleAssignment.objects.create(
                                employee=employee,
                                schedule_no=schedule_no,
                                trip_no=int(trip_no),
                                route_no=route_no,
                                date=assignment_date,
                                assigned_by=depot_user,
                                notes=notes
                            )
                            created_assignments.append(assignment)
                
                # Provide appropriate feedback
                if created_assignments:
                    count = len(created_assignments)
                    if count == int(trip_count):
                        messages.success(request, f"Successfully created {count} schedule assignments!")
                    else:
                        messages.warning(request, f"Created {count} assignments out of {trip_count} requested. Some assignments already existed.")
                    
                    if errors:
                        for error in errors:
                            messages.warning(request, error)
                    
                    return redirect('depot_portal:assignment_list')
                else:
                    messages.error(request, "No assignments were created. All requested assignments already exist.")
                    
            except Employee.DoesNotExist:
                messages.error(request, "Selected employee not found.")
            except ValueError as e:
                messages.error(request, f"Invalid date format: {e}")
            except Exception as e:
                messages.error(request, f"Error creating assignments: {e}")
        else:
            # Handle single trip submission (original logic)
            form = ScheduleAssignmentForm(request.POST, depot=depot_user.depot)
            if form.is_valid():
                assignment = form.save(commit=False)
                assignment.assigned_by = depot_user
                assignment.save()
                messages.success(request, "Schedule assignment created successfully!")
                return redirect('depot_portal:assignment_list')
    else:
        form = ScheduleAssignmentForm(depot=depot_user.depot)
    
    # Always ensure form is defined
    if 'form' not in locals():
        form = ScheduleAssignmentForm(depot=depot_user.depot)
    
    return render(request, 'depot_portal/assignment_form.html', {
        'form': form,
        'depot_user': depot_user,
        'action': 'Add'
    })


def assignment_edit(request, assignment_id):
    if 'depot_user_id' not in request.session:
        return redirect('depot_portal:login')
    
    depot_user = get_object_or_404(DepotUser, depot_user_id=request.session['depot_user_id'])
    assignment = get_object_or_404(ScheduleAssignment, assignment_id=assignment_id, employee__depot=depot_user.depot)
    
    if request.method == 'POST':
        form = ScheduleAssignmentForm(request.POST, instance=assignment, depot=depot_user.depot)
        if form.is_valid():
            form.save()
            messages.success(request, "Schedule assignment updated successfully!")
            return redirect('depot_portal:assignment_list')
    else:
        form = ScheduleAssignmentForm(instance=assignment, depot=depot_user.depot)
    
    return render(request, 'depot_portal/assignment_form.html', {
        'form': form,
        'assignment': assignment,
        'depot_user': depot_user,
        'action': 'Edit'
    })


def attendance_list(request):
    if 'depot_user_id' not in request.session:
        return redirect('depot_portal:login')
    
    depot_user = get_object_or_404(DepotUser, depot_user_id=request.session['depot_user_id'])
    
    # Start with base queryset for statistics (unfiltered)
    base_attendance = Attendance.objects.filter(
        employee__depot=depot_user.depot
    )
    
    # Create filtered queryset for display
    all_attendance = base_attendance
    
    # Apply status filter if provided (only for display)
    status_filter = request.GET.get('status')
    if status_filter and status_filter in ['present', 'absent', 'late', 'half_day']:
        all_attendance = all_attendance.filter(status=status_filter)
    
    # Apply date filter if provided
    date_filter = request.GET.get('date')
    if date_filter:
        try:
            from datetime import datetime
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            all_attendance = all_attendance.filter(date=filter_date)
            # Also apply date filter to base data for statistics
            base_attendance = base_attendance.filter(date=filter_date)
        except ValueError:
            pass  # Invalid date format, ignore filter
    
    # Apply employee filter if provided
    employee_filter = request.GET.get('employee')
    if employee_filter:
        all_attendance = all_attendance.filter(
            Q(employee__employee_name__icontains=employee_filter) |
            Q(employee__employee_id__icontains=employee_filter)
        )
        # Also apply employee filter to base data for statistics
        base_attendance = base_attendance.filter(
            Q(employee__employee_name__icontains=employee_filter) |
            Q(employee__employee_id__icontains=employee_filter)
        )
    
    # Order and get attendance records
    all_attendance = all_attendance.order_by('-date', 'employee__employee_name')
    
    # Group attendance by employee, date, and schedule
    grouped_attendance = {}
    for record in all_attendance:
        # Create a unique key for grouping (considering schedule_no from assignment if available)
        schedule_no = record.schedule_assignment.schedule_no if record.schedule_assignment else 'No Assignment'
        key = (record.employee.employee_id, record.date, schedule_no)
        
        if key not in grouped_attendance:
            grouped_attendance[key] = {
                'employee': record.employee,
                'date': record.date,
                'schedule_no': schedule_no,
                'marked_by': record.marked_by,
                'created_at': record.created_at,
                'notes': record.notes,
                'trips': [],
                'attendance_ids': []
            }
        
        # Add trip information with status to the group
        trip_info = {
            'attendance_id': record.attendance_id,
            'status': record.status,
            'check_in_time': record.check_in_time,
            'check_out_time': record.check_out_time,
            'notes': record.notes
        }
        
        if record.schedule_assignment:
            trip_info.update({
                'trip_no': record.schedule_assignment.trip_no,
                'route_no': record.schedule_assignment.route_no,
                'assignment_id': record.schedule_assignment.assignment_id
            })
        else:
            trip_info.update({
                'trip_no': 'N/A',
                'route_no': 'N/A',
                'assignment_id': None
            })
        
        grouped_attendance[key]['trips'].append(trip_info)
        grouped_attendance[key]['attendance_ids'].append(record.attendance_id)
    
    # Convert to list and sort by date (newest first)
    attendance_records = list(grouped_attendance.values())
    attendance_records.sort(key=lambda x: x['date'], reverse=True)
    
    # Calculate statistics based on base_attendance (unfiltered by status)
    stats = {
        'total_records': 0,
        'present_count': 0,
        'absent_count': 0,
        'late_count': 0,
        'half_day_count': 0
    }
    
    # Group base attendance for statistics (same logic but for unfiltered data)
    base_grouped = {}
    for record in base_attendance:
        schedule_no = record.schedule_assignment.schedule_no if record.schedule_assignment else 'No Assignment'
        key = (record.employee.employee_id, record.date, schedule_no)
        
        if key not in base_grouped:
            base_grouped[key] = {
                'trips': []
            }
        
        trip_info = {
            'status': record.status,
        }
        base_grouped[key]['trips'].append(trip_info)
    
    # Count statistics from base data - count unique employees by status
    stats['total_records'] = len(base_grouped)
    
    # Use sets to track unique employees for each status
    present_employees = set()
    absent_employees = set()
    late_employees = set()
    half_day_employees = set()
    
    for record in base_attendance:
        employee_key = (record.employee.employee_id, record.date)  # Unique employee per day
        
        if record.status == 'present':
            present_employees.add(employee_key)
        elif record.status == 'absent':
            absent_employees.add(employee_key)
        elif record.status == 'late':
            late_employees.add(employee_key)
        elif record.status == 'half_day':
            half_day_employees.add(employee_key)
    
    stats['present_count'] = len(present_employees)
    stats['absent_count'] = len(absent_employees)
    stats['late_count'] = len(late_employees)
    stats['half_day_count'] = len(half_day_employees)
    
    return render(request, 'depot_portal/attendance_list.html', {
        'attendance_records': attendance_records,
        'depot_user': depot_user,
        'current_status_filter': status_filter,
        'current_date_filter': date_filter,
        'current_employee_filter': employee_filter,
        'stats': stats,
    })


def attendance_mark(request):
    if 'depot_user_id' not in request.session:
        return redirect('depot_portal:login')
    
    depot_user = get_object_or_404(DepotUser, depot_user_id=request.session['depot_user_id'])
    
    if request.method == 'POST':
        # Check if multiple assignments were submitted
        assignment_count = request.POST.get('assignment_count')
        
        # Check if multiple trips were submitted (new approach)
        trip_count = request.POST.get('trip_count')
        
        if trip_count and int(trip_count) >= 1:
            # Handle multiple trip attendance submission
            employee_id = request.POST.get('employee')
            attendance_date = request.POST.get('date')
            status = request.POST.get('status')
            check_in_time = request.POST.get('check_in_time')
            check_out_time = request.POST.get('check_out_time')
            notes = request.POST.get('notes', '')
            selected_schedule = request.POST.get('selected_schedule')
            
            # Validate required fields
            if not all([employee_id, attendance_date, status, selected_schedule]):
                messages.error(request, "Employee, date, status, and schedule are required.")
                form = AttendanceForm(depot=depot_user.depot)
                return render(request, 'depot_portal/attendance_form.html', {
                    'form': form,
                    'depot_user': depot_user,
                    'action': 'Mark'
                })
            
            try:
                employee = Employee.objects.get(employee_id=employee_id, depot=depot_user.depot)
                attendance_date = datetime.strptime(attendance_date, '%Y-%m-%d').date()
                
                created_attendances = []
                errors = []
                
                # Process each trip
                for i in range(int(trip_count)):
                    trip_no = request.POST.get(f'trip_{i}')
                    route_no = request.POST.get(f'route_{i}')
                    
                    if trip_no and route_no:
                        # Find existing schedule assignment for this trip
                        try:
                            assignment = ScheduleAssignment.objects.get(
                                employee=employee,
                                schedule_no=selected_schedule,
                                trip_no=int(trip_no),
                                route_no=route_no,
                                date=attendance_date
                            )
                            
                            # Check for duplicate attendance
                            existing_attendance = Attendance.objects.filter(
                                employee=employee,
                                date=attendance_date,
                                schedule_assignment=assignment
                            ).first()
                            
                            if existing_attendance:
                                errors.append(f"Attendance for {selected_schedule}/Trip {trip_no} already exists")
                            else:
                                # Create new attendance record
                                attendance = Attendance.objects.create(
                                    employee=employee,
                                    schedule_assignment=assignment,
                                    date=attendance_date,
                                    check_in_time=check_in_time if check_in_time else None,
                                    check_out_time=check_out_time if check_out_time else None,
                                    status=status,
                                    marked_by=depot_user,
                                    notes=notes
                                )
                                created_attendances.append(attendance)
                        except ScheduleAssignment.DoesNotExist:
                            errors.append(f"No assignment found for {selected_schedule}/Trip {trip_no} on {attendance_date}")
                
                # Provide appropriate feedback
                if created_attendances:
                    count = len(created_attendances)
                    if count == int(trip_count):
                        messages.success(request, f"Successfully marked attendance for {count} trips on {selected_schedule}!")
                    else:
                        messages.warning(request, f"Marked attendance for {count} trips out of {trip_count} requested. Some attendance already existed.")
                    
                    if errors:
                        for error in errors:
                            messages.warning(request, error)
                    
                    return redirect('depot_portal:attendance_list')
                else:
                    messages.error(request, "No attendance records were created. All requested attendance already exists.")
                    
            except Employee.DoesNotExist:
                messages.error(request, "Selected employee not found.")
            except ValueError as e:
                messages.error(request, f"Invalid date format: {e}")
            except Exception as e:
                messages.error(request, f"Error creating attendance records: {e}")
        else:
            # Handle single assignment submission (original logic)
            form = AttendanceForm(request.POST, depot=depot_user.depot)
            if form.is_valid():
                attendance = form.save(commit=False)
                attendance.marked_by = depot_user
                attendance.save()
                messages.success(request, "Attendance marked successfully!")
                return redirect('depot_portal:attendance_list')
    else:
        form = AttendanceForm(depot=depot_user.depot)
    
    # Always ensure form is defined
    if 'form' not in locals():
        form = AttendanceForm(depot=depot_user.depot)
    
    return render(request, 'depot_portal/attendance_form.html', {
        'form': form,
        'depot_user': depot_user,
        'action': 'Mark'
    })


def attendance_edit(request, attendance_id):
    if 'depot_user_id' not in request.session:
        return redirect('depot_portal:login')
    
    depot_user = get_object_or_404(DepotUser, depot_user_id=request.session['depot_user_id'])
    attendance = get_object_or_404(Attendance, attendance_id=attendance_id, employee__depot=depot_user.depot)
    
    if request.method == 'POST':
        form = AttendanceForm(request.POST, instance=attendance, depot=depot_user.depot)
        if form.is_valid():
            form.save()
            messages.success(request, "Attendance updated successfully!")
            return redirect('depot_portal:attendance_list')
    else:
        form = AttendanceForm(instance=attendance, depot=depot_user.depot)
    
    return render(request, 'depot_portal/attendance_form.html', {
        'form': form,
        'attendance': attendance,
        'depot_user': depot_user,
        'action': 'Edit'
    })


def get_schedules_ajax(request):
    employee_id = request.GET.get('employee_id')
    date = request.GET.get('date')
    
    if employee_id and date:
        # Get assignments for the specific employee and date (for attendance form)
        assignments = ScheduleAssignment.objects.filter(
            employee_id=employee_id,
            date=date
        ).values('schedule_no', 'trip_no', 'route_no')
        return JsonResponse(list(assignments), safe=False)
    else:
        # Return all available schedules from bus_route.Schedule (for assignment form)
        from bus_route.models import Schedule
        schedules = Schedule.objects.all().values('schedule_no', 'trip_no', 'route_no')
        return JsonResponse(list(schedules), safe=False)


@csrf_exempt
def test_assignment_creation(request):
    """Test endpoint to create multiple assignments directly"""
    if request.method == 'POST':
        # Get a test employee and depot user
        employee = Employee.objects.first()
        depot_user = DepotUser.objects.first()
        
        if not employee or not depot_user:
            return JsonResponse({'error': 'No test data available'})
        
        # Create test assignments
        assignments_created = []
        test_date = date.today()
        
        for trip_no in [1, 2, 3]:
            assignment = ScheduleAssignment.objects.create(
                employee=employee,
                schedule_no='S026001',
                trip_no=trip_no,
                route_no='1088A',
                date=test_date,
                assigned_by=depot_user,
                notes=f'Test assignment for trip {trip_no}'
            )
            assignments_created.append({
                'id': assignment.assignment_id,
                'employee': assignment.employee.employee_name,
                'trip': assignment.trip_no,
                'route': assignment.route_no
            })
        
        return JsonResponse({
            'success': True,
            'message': f'Created {len(assignments_created)} test assignments',
            'assignments': assignments_created
        })
    
    return JsonResponse({'error': 'POST required'})


def daily_assignments_pdf(request):
    # PDF generation placeholder - will implement with reportlab
    return HttpResponse("PDF generation coming soon!", content_type="text/plain")