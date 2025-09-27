from django.urls import path
from . import views

app_name = 'integrations'

urlpatterns = [
    # Integration URLs
    path('integrations/', views.IntegrationListView, name='list'),
    path('integrations/import/', views.ImportView, name='import'),
    path('integrations/export/', views.ExportView, name='export'),
    path('integrations/jobs/', views.JobListView, name='jobs'),
    path('integrations/jobs/<int:pk>/', views.JobDetailView, name='job_detail'),
]
