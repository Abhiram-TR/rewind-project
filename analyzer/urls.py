from django.urls import path
from . import views

app_name = 'analyzer'

urlpatterns = [
    path('', views.analyzer_home, name='analyzer_home'),
    path('api/routes/', views.get_route_data, name='get_route_data'),
    path('api/analyze/', views.analyze_route_overlap, name='analyze_route_overlap'),
    path('api/history/', views.get_analysis_history, name='get_analysis_history'),
]