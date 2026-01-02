from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Authentication URLs
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # User Management
    path('', views.user_list_view, name='list'),
    path('create/', views.user_create_view, name='create'),
    path('<int:user_id>/', views.user_detail_view, name='detail'),
    path('<int:user_id>/edit/', views.user_edit_view, name='edit'),
    path('<int:user_id>/delete/', views.user_delete_view, name='delete'),
    
    # Profile Management
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('change-password/', views.change_password_view, name='change_password'),
    
    # API URLs
    path('api/users/', views.api_user_list, name='api_list'),
    path('api/users/<int:user_id>/', views.api_user_detail, name='api_detail'),
    path('api/regions/', views.api_regions, name='api_regions'),
]
