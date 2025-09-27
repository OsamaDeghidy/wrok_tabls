from django.urls import path
from . import views

app_name = 'approvals'

urlpatterns = [
    # Approval URLs
    path('approvals/', views.ApprovalListView, name='list'),
    path('approvals/create/', views.ApprovalCreateView, name='create'),
    path('approvals/<int:pk>/', views.ApprovalDetailView, name='detail'),
    path('approvals/<int:pk>/edit/', views.ApprovalEditView, name='edit'),
    path('approvals/<int:pk>/approve/', views.ApprovalApproveView, name='approve'),
    path('approvals/<int:pk>/reject/', views.ApprovalRejectView, name='reject'),
]
