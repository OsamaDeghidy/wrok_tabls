from django.urls import path
from . import views

app_name = 'branches'

urlpatterns = [
    # Branch URLs
    path('', views.branch_list_view, name='list'),
    path('create/', views.branch_create_view, name='create'),
    path('<int:branch_id>/', views.branch_detail_view, name='detail'),
    path('<int:branch_id>/edit/', views.branch_edit_view, name='edit'),
    path('<int:branch_id>/delete/', views.branch_delete_view, name='delete'),
    
    # Shift URLs
    path('<int:branch_id>/shifts/create/', views.shift_create_view, name='shift_create'),
    path('<int:branch_id>/shifts/<int:shift_id>/edit/', views.shift_edit_view, name='shift_edit'),
    path('<int:branch_id>/shifts/<int:shift_id>/delete/', views.shift_delete_view, name='shift_delete'),
    
    # API URLs
    path('api/', views.api_branch_list, name='api_list'),
    path('api/<int:branch_id>/', views.api_branch_detail, name='api_detail'),
    path('api/<int:branch_id>/shifts/', views.api_shift_list, name='api_shifts'),
]