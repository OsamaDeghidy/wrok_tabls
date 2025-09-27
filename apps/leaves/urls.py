from django.urls import path
from . import views

app_name = 'leaves'

urlpatterns = [
    # Leave URLs
    path('leaves/', views.LeaveListView, name='list'),
    path('leaves/create/', views.LeaveCreateView, name='create'),
    path('leaves/<int:pk>/', views.LeaveDetailView, name='detail'),
    path('leaves/<int:pk>/edit/', views.LeaveEditView, name='edit'),
    path('leaves/<int:pk>/delete/', views.LeaveDeleteView, name='delete'),
    
    # Leave Actions
    path('leaves/<int:pk>/approve/', views.LeaveApproveView, name='approve'),
    path('leaves/<int:pk>/reject/', views.LeaveRejectView, name='reject'),
]
