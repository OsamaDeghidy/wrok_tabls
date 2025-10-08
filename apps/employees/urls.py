from django.urls import path
from . import views

app_name = 'employees'

urlpatterns = [
    # Employee Management URLs
    path('', views.employee_list_view, name='list'),
    path('create/', views.employee_create_view, name='create'),
    path('<int:employee_id>/', views.employee_detail_view, name='detail'),
    path('<int:employee_id>/edit/', views.employee_edit_view, name='edit'),
    path('<int:employee_id>/delete/', views.employee_delete_view, name='delete'),
    path('import/', views.employee_import_view, name='import'),
    path('export/', views.employee_export_view, name='export'),
    path('download-sample/', views.download_sample_file, name='download_sample'),
    
    # API URLs
    path('api/', views.api_employee_list, name='api_list'),
    path('api/<int:employee_id>/', views.api_employee_detail, name='api_detail'),
]