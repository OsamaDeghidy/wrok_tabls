from django.urls import path
from . import views

app_name = 'violations'

urlpatterns = [
    # Violation URLs
    path('violations/', views.ViolationListView, name='list'),
    path('violations/create/', views.ViolationCreateView, name='create'),
    path('violations/<int:pk>/', views.ViolationDetailView, name='detail'),
    path('violations/<int:pk>/edit/', views.ViolationEditView, name='edit'),
    path('violations/<int:pk>/delete/', views.ViolationDeleteView, name='delete'),
]
