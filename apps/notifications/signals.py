from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.schedules.models import Schedule
from .models import Notification

@receiver(post_save, sender=Schedule)
def schedule_status_notification(sender, instance, created, **kwargs):
    """إرسال تنبيهات عند تغيير حالة الجدول"""
    
    # إذا كانت الحالة 'active' أو 'approved'
    if instance.status in ['active', 'approved']:
        # الحصول على جميع الموظفين في هذا الجدول
        employees = instance.entries.values_list('employee', flat=True).distinct()
        
        status_display = instance.get_status_display()
        title = f"تحديث الجدول التشغيلي: {status_display}"
        message = f"تم تحديث حالة الجدول للفرع {instance.branch.name} للفترة من {instance.start_date} إلى {instance.end_date} إلى {status_display}."
        
        for employee_id in employees:
            Notification.objects.get_or_create(
                recipient_id=employee_id,
                title=title,
                message=message,
                link=f"/schedules/detail/{instance.id}/"
            )
