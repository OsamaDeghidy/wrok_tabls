from django.db.models import Q
from .models import ApprovalFlow

def pending_approvals(request):
    """
    سياق الإشعارات للموافقات المعلقة
    """
    # القيم الافتراضية
    context = {
        'pending_approvals_count': 0,
        'unread_notifications_count': 0,
        'recent_notifications': []
    }
    
    if not request.user.is_authenticated:
        return context
        
    try:
        # التنبيهات من تطبيق التنبيهات
        from apps.notifications.models import Notification
        
        # استخدام معرف المستخدم المباشر للتأكد من دقة الاستعلام
        user_notifications = Notification.objects.filter(recipient_id=request.user.id)
        unread_count = user_notifications.filter(is_read=False).count()
        recent = list(user_notifications[:5])
        
        context['unread_notifications_count'] = unread_count
        context['recent_notifications'] = recent
        
        # طباعة للتأكد من عمل الكود في الـ Terminal
        print(f"DEBUG NOTIFICATIONS: User={request.user.username}, Unread={unread_count}")

        # الموافقات (تعتمد على البروفايل والدور)
        user_profile = getattr(request.user, 'profile', None)
        if user_profile:
            if user_profile.role == 'super_admin':
                 context['pending_approvals_count'] = ApprovalFlow.objects.filter(status__in=['pending', 'in_progress']).count()
            elif user_profile.role in ['coordinator', 'region_manager', 'operations_manager', 'admin_manager']:
                all_pending = ApprovalFlow.objects.filter(status__in=['pending', 'in_progress'])
                pending_count = 0
                for flow in all_pending:
                    # نستخدم طريقة مباشرة للتحقق من الصلاحية
                    eligible = flow.get_pending_users()
                    if eligible.filter(id=request.user.id).exists():
                        pending_count += 1
                context['pending_approvals_count'] = pending_count
                
        return context
    except Exception as e:
        import traceback
        print(f"CRITICAL ERROR in context_processor: {str(e)}")
        # traceback.print_exc()
        return context
