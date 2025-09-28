from django.urls import path
from . import views
from . import api_views

app_name = 'schedules'

urlpatterns = [
    # قائمة الجداول التشغيلية
    path('', views.schedule_list_view, name='list'),
    
    # إنشاء جدول تشغيلي جديد
    path('create/', views.schedule_create_view, name='create'),
    
    # تفاصيل الجدول التشغيلي
    path('<int:schedule_id>/', views.schedule_detail_view, name='detail'),
    
    # تعديل الجدول التشغيلي
    path('<int:schedule_id>/edit/', views.schedule_edit_view, name='edit'),
    
    # إدارة إدخالات الجدول
    path('<int:schedule_id>/entries/', views.schedule_entries_view, name='entries'),
    
    # تحليلات الجدول
    path('<int:schedule_id>/analytics/', views.schedule_analytics_view, name='analytics'),
    
    # اعتماد الجدول
    path('<int:schedule_id>/approve/', views.schedule_approve_view, name='approve'),
    
    # رفض الجدول
    path('<int:schedule_id>/reject/', views.schedule_reject_view, name='reject'),
    
    # تفعيل الجدول
    path('<int:schedule_id>/activate/', views.schedule_activate_view, name='activate'),
    
    # API Endpoints
    path('api/branches/<int:branch_id>/', views.branch_info_api, name='branch_info_api'),
    path('api/employees/', views.employees_api, name='employees_api'),
    path('api/branches/<int:branch_id>/shifts/', views.branch_shifts_api, name='branch_shifts_api'),
    path('api/leaves/conflicts/', views.leave_conflicts_api, name='leave_conflicts_api'),
    path('api/create/', views.create_schedule_api, name='create_schedule_api'),
    path('api/<int:schedule_id>/save-entries/', views.save_schedule_entries_api, name='save_schedule_entries_api'),
    path('api/<int:schedule_id>/delete-day-entries/', api_views.delete_day_entries_api, name='delete_day_entries_api'),
    path('api/<int:schedule_id>/get-day-entries/', api_views.get_day_entries_api, name='get_day_entries_api'),
]