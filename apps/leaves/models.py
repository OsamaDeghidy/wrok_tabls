from django.db import models
from apps.users.models import User


class Leave(models.Model):
    """نموذج الإجازة"""
    
    LEAVE_TYPE_CHOICES = [
        ('annual', 'إجازة سنوية'),
        ('sick', 'إجازة مرضية'),
        ('emergency', 'إجازة طارئة'),
        ('maternity', 'إجازة أمومة'),
        ('paternity', 'إجازة أبوة'),
        ('unpaid', 'إجازة بدون راتب'),
        ('other', 'أخرى'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'في الانتظار'),
        ('approved', 'معتمد'),
        ('rejected', 'مرفوض'),
        ('cancelled', 'ملغي'),
    ]
    
    # المعلومات الأساسية
    employee = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='الموظف', related_name='leaves')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES, verbose_name='نوع الإجازة')
    
    # الفترة الزمنية
    start_date = models.DateField(verbose_name='تاريخ البداية')
    end_date = models.DateField(verbose_name='تاريخ النهاية')
    
    # الحالة والموافقات
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='الحالة')
    
    # معلومات إضافية
    reason = models.TextField(verbose_name='سبب الإجازة')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    
    # الموافقات
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='اعتمد بواسطة')
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ الموافقة')
    
    # تواريخ النظام
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_leaves', verbose_name='أنشأ بواسطة')
    
    class Meta:
        verbose_name = 'إجازة'
        verbose_name_plural = 'الإجازات'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.get_leave_type_display()} ({self.start_date} إلى {self.end_date})"
    
    @property
    def duration_days(self):
        """عدد أيام الإجازة"""
        return (self.end_date - self.start_date).days + 1
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def is_approved(self):
        return self.status == 'approved'
    
    @property
    def is_rejected(self):
        return self.status == 'rejected'