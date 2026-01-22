from django.urls import path
from django.shortcuts import render
from . import views

app_name = 'route_performance'

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # API endpoints
    path('api/performance/', views.RoutePerformanceAPIView.as_view(), name='api_performance'),
    path('api/top-performers/', views.TopPerformersAPIView.as_view(), name='api_top_performers'),
    path('api/underperformers/', views.UnderperformersAPIView.as_view(), name='api_underperformers'),
    path('api/comparison/', views.RouteComparisonAPIView.as_view(), name='api_comparison'),
    path('api/trends/', views.RouteTrendsAPIView.as_view(), name='api_trends'),
    path('api/bulk-calculate/', views.BulkCalculateView.as_view(), name='api_bulk_calculate'),
    
    # Route detail
    path('route/<str:route_no>/', views.RouteDetailView.as_view(), name='route_detail'),
    
    # Test page
    path('test/', lambda request: render(request, 'route_performance/test.html'), name='test'),
]