from django.db import models
from django.contrib.auth.models import User

class Notification(models.Model):
    """نموذج التنبيهات"""
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name='المستلم')
    title = models.CharField(max_length=255, verbose_name='العنوان')
    message = models.TextField(verbose_name='الرسالة')
    link = models.CharField(max_length=500, blank=True, null=True, verbose_name='الرابط')
    is_read = models.BooleanField(default=False, verbose_name='تمت القراءة')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ التنبيه')

    class Meta:
        verbose_name = 'تنبيه'
        verbose_name_plural = 'التنبيهات'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient.username} - {self.title}"
