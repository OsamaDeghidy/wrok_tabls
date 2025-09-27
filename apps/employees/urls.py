from django.urls import path
from . import views

app_name = 'employees'

urlpatterns = [
    # Employee URLs
    path('employees/', views.EmployeeListView, name='list'),
    path('employees/create/', views.EmployeeCreateView, name='create'),
    path('employees/<int:pk>/', views.EmployeeDetailView, name='detail'),
    path('employees/<int:pk>/edit/', views.EmployeeEditView, name='edit'),
    path('employees/<int:pk>/delete/', views.EmployeeDeleteView, name='delete'),
    
    # Import/Export URLs
    path('employees/import/', views.EmployeeImportView, name='import'),
    path('employees/export/', views.EmployeeExportView, name='export'),
]
