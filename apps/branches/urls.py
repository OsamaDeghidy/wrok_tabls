from django.urls import path
from . import views

app_name = 'branches'

urlpatterns = [
    # Branch URLs
    path('branches/', views.BranchListView, name='list'),
    path('branches/create/', views.BranchCreateView, name='create'),
    path('branches/<int:pk>/', views.BranchDetailView, name='detail'),
    path('branches/<int:pk>/edit/', views.BranchEditView, name='edit'),
    path('branches/<int:pk>/delete/', views.BranchDeleteView, name='delete'),
]
