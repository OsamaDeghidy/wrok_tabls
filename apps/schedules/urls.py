from django.urls import path
from . import views

app_name = 'schedules'

urlpatterns = [
    # Schedule URLs
    path('schedules/', views.ScheduleListView, name='list'),
    path('schedules/create/', views.ScheduleCreateView, name='create'),
    path('schedules/<int:pk>/', views.ScheduleDetailView, name='detail'),
    path('schedules/<int:pk>/edit/', views.ScheduleEditView, name='edit'),
    path('schedules/<int:pk>/delete/', views.ScheduleDeleteView, name='delete'),
    
    # Schedule Actions
    path('schedules/<int:pk>/approve/', views.ScheduleApproveView, name='approve'),
    path('schedules/<int:pk>/reject/', views.ScheduleRejectView, name='reject'),
    path('schedules/<int:pk>/copy/', views.ScheduleCopyView, name='copy'),
]
