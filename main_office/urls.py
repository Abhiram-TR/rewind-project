from django.urls import path
from . import views

app_name = 'main_office'

urlpatterns = [
    path('dashboard/', views.office_dashboard, name='dashboard'),
    path('attendance-report/', views.attendance_report, name='attendance_report'),
    path('depot-overview/', views.depot_overview, name='depot_overview'),
    path('employee-analytics/', views.employee_analytics, name='employee_analytics'),
    path('export-attendance/', views.export_attendance, name='export_attendance'),
]



