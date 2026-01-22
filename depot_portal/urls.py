from django.urls import path
from . import views

app_name = 'depot_portal'

urlpatterns = [
    # Authentication
    path('login/', views.depot_login, name='login'),
    path('logout/', views.depot_logout, name='logout'),
    path('dashboard/', views.depot_dashboard, name='dashboard'),
    
    # Employee Management
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/add/', views.employee_add, name='employee_add'),
    path('employees/<str:employee_id>/edit/', views.employee_edit, name='employee_edit'),
    path('employees/<str:employee_id>/delete/', views.employee_delete, name='employee_delete'),
    
    # Schedule Assignment
    path('assignments/', views.assignment_list, name='assignment_list'),
    path('assignments/add/', views.assignment_add, name='assignment_add'),
    path('assignments/<int:assignment_id>/edit/', views.assignment_edit, name='assignment_edit'),
    path('assignments/daily-pdf/', views.daily_assignments_pdf, name='daily_assignments_pdf'),
    
    # Attendance Management
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('attendance/mark/', views.attendance_mark, name='attendance_mark'),
    path('attendance/<int:attendance_id>/edit/', views.attendance_edit, name='attendance_edit'),
    
    # AJAX endpoints
    path('ajax/get-schedules/', views.get_schedules_ajax, name='get_schedules_ajax'),
    path('ajax/test-assignment/', views.test_assignment_creation, name='test_assignment_creation'),
]



