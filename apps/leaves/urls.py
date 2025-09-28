from django.urls import path
from . import views

app_name = 'leaves'

urlpatterns = [
    # قائمة الإجازات
    path('', views.leave_list_view, name='list'),
    
    # إنشاء طلب إجازة جديد
    path('create/', views.leave_create_view, name='create'),
    
    # تفاصيل طلب الإجازة
    path('<int:leave_id>/', views.leave_detail_view, name='detail'),
    
    # تعديل طلب الإجازة
    path('<int:leave_id>/edit/', views.leave_edit_view, name='edit'),
    
    # موافقة على طلب الإجازة
    path('<int:leave_id>/approve/', views.leave_approve_view, name='approve'),
    
    # رفض طلب الإجازة
    path('<int:leave_id>/reject/', views.leave_reject_view, name='reject'),
    
    # إلغاء طلب الإجازة
    path('<int:leave_id>/cancel/', views.leave_cancel_view, name='cancel'),
    
    # رصيد الإجازات
    path('balance/', views.leave_balance_view, name='balance'),
]