from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Report URLs
    path('reports/', views.ReportListView, name='list'),
    path('reports/create/', views.ReportCreateView, name='create'),
    path('reports/<int:pk>/', views.ReportDetailView, name='detail'),
    path('reports/<int:pk>/download/', views.ReportDownloadView, name='download'),
    path('reports/<int:pk>/delete/', views.ReportDeleteView, name='delete'),
]
