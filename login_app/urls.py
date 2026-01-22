from django.urls import path
from . import views  # This line is important - it imports your views module

app_name = 'login_app'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('main_home/', views.main_home_view, name='main_home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
]



