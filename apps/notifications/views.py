from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Notification

@login_required
def notification_list(request):
    """عرض قائمة جميع التنبيهات"""
    notifications = request.user.notifications.all()
    
    # تحديث جميع التنبيهات كـ "مقروءة" عند فتح الصفحة
    notifications.filter(is_read=False).update(is_read=True)
    
    return render(request, 'notifications/list.html', {
        'notifications': notifications
    })

@login_required
def mark_as_read(request, notification_id):
    """تحديد تنبيه معين كمقروء"""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    
    if notification.link:
        return redirect(notification.link)
    return redirect('notifications:list')
