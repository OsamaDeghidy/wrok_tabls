from django.urls import path
from . import views

app_name = 'approvals'

urlpatterns = [
    path('', views.approvals_list_view, name='list'),
    path('my-approvals/', views.my_approvals_view, name='my_approvals'),
    path('<int:approval_id>/', views.approval_detail_view, name='detail'),
    path('<int:approval_id>/approve/', views.approve_request_view, name='approve'),
    path('<int:approval_id>/reject/', views.reject_request_view, name='reject'),
    path('create-for-schedule/<int:schedule_id>/', views.create_approval_for_schedule, name='create_for_schedule'),
]