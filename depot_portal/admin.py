from django.contrib import admin
from .models import Depot, DepotUser, Employee, ScheduleAssignment, Attendance


@admin.register(Depot)
class DepotAdmin(admin.ModelAdmin):
    list_display = ['depot_code', 'depot_name', 'location', 'is_active', 'created_date']
    list_filter = ['is_active', 'created_date']
    search_fields = ['depot_code', 'depot_name', 'location']


@admin.register(DepotUser)
class DepotUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'full_name', 'depot', 'role', 'is_active', 'last_login']
    list_filter = ['role', 'is_active', 'depot']
    search_fields = ['username', 'full_name']
    exclude = ['password_hash']


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'employee_name', 'depot', 'role', 'is_active', 'joining_date']
    list_filter = ['role', 'is_active', 'depot', 'joining_date']
    search_fields = ['employee_id', 'employee_name', 'phone_number']


@admin.register(ScheduleAssignment)
class ScheduleAssignmentAdmin(admin.ModelAdmin):
    list_display = ['employee', 'schedule_no', 'trip_no', 'route_no', 'date', 'status', 'assigned_by']
    list_filter = ['status', 'date', 'employee__depot']
    search_fields = ['employee__employee_name', 'schedule_no', 'route_no']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'status', 'check_in_time', 'check_out_time', 'marked_by']
    list_filter = ['status', 'date', 'employee__depot']
    search_fields = ['employee__employee_name']
