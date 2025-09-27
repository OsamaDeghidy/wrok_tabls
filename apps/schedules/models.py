from django.db import models
from apps.users.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Schedule(models.Model):
    """نموذج الجدول التشغيلي"""
    
    SCHEDULE_TYPE_CHOICES = [
        ('weekly', 'أسبوعي'),
        ('monthly', 'شهري'),
        ('quarterly', 'ربع سنوي'),
        ('yearly', 'سنوي'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'مسودة'),
        ('pending_coordinator', 'في انتظار موافقة المنسق'),
        ('pending_region_manager', 'في انتظار موافقة مدير المنطقة'),
        ('pending_operations_manager', 'في انتظار موافقة مدير العمليات'),
        ('pending_admin_manager', 'في انتظار موافقة مدير الإدارة'),
        ('approved', 'معتمد'),
        ('rejected', 'مرفوض'),
        ('active', 'نشط'),
        ('completed', 'مكتمل'),
    ]
    
    # المعلومات الأساسية
    name = models.CharField(max_length=200, verbose_name='اسم الجدول')
    branch = models.ForeignKey('branches.Branch', on_delete=models.CASCADE, verbose_name='الفرع')
    schedule_type = models.CharField(max_length=20, choices=SCHEDULE_TYPE_CHOICES, verbose_name='نوع الجدول')
    
    # الفترة الزمنية
    start_date = models.DateField(verbose_name='تاريخ البداية')
    end_date = models.DateField(verbose_name='تاريخ النهاية')
    
    # الحالة والموافقات
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft', verbose_name='الحالة')
    
    # معلومات إضافية
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    
    # تواريخ النظام
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='أنشأ بواسطة')
    
    class Meta:
        verbose_name = 'جدول تشغيلي'
        verbose_name_plural = 'الجداول التشغيلية'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.branch.name} ({self.start_date} إلى {self.end_date})"
    
    @property
    def duration_days(self):
        """عدد أيام الجدول"""
        return (self.end_date - self.start_date).days + 1
    
    @property
    def is_approved(self):
        return self.status == 'approved'
    
    @property
    def can_be_edited(self):
        """هل يمكن تعديل الجدول"""
        return self.status in ['draft', 'rejected']


class ScheduleEntry(models.Model):
    """نموذج دخول الجدول التشغيلي"""
    
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='entries', verbose_name='الجدول')
    employee = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='الموظف', related_name='schedule_entries')
    shift = models.ForeignKey('branches.Shift', on_delete=models.CASCADE, verbose_name='الشفت')
    date = models.DateField(verbose_name='التاريخ')
    
    # معلومات إضافية
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    
    # تواريخ النظام
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    
    class Meta:
        verbose_name = 'دخول الجدول'
        verbose_name_plural = 'دخول الجداول'
        ordering = ['date', 'shift__start_time']
        unique_together = ['schedule', 'employee', 'shift', 'date']
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.shift.name} - {self.date}"
    
    @property
    def work_hours(self):
        """ساعات العمل لهذا الدخول"""
        return self.shift.duration()


class ScheduleApproval(models.Model):
    """نموذج موافقات الجدول التشغيلي"""
    
    APPROVAL_STATUS_CHOICES = [
        ('pending', 'في الانتظار'),
        ('approved', 'معتمد'),
        ('rejected', 'مرفوض'),
    ]
    
    APPROVAL_LEVEL_CHOICES = [
        ('coordinator', 'منسق'),
        ('region_manager', 'مدير المنطقة'),
        ('operations_manager', 'مدير العمليات'),
        ('admin_manager', 'مدير الإدارة'),
    ]
    
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='approvals', verbose_name='الجدول')
    level = models.CharField(max_length=20, choices=APPROVAL_LEVEL_CHOICES, verbose_name='مستوى الموافقة')
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='المعتمد')
    status = models.CharField(max_length=20, choices=APPROVAL_STATUS_CHOICES, default='pending', verbose_name='الحالة')
    comments = models.TextField(blank=True, verbose_name='تعليقات')
    
    # تواريخ النظام
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ الموافقة')
    
    class Meta:
        verbose_name = 'موافقة الجدول'
        verbose_name_plural = 'موافقات الجداول'
        ordering = ['level', 'created_at']
        unique_together = ['schedule', 'level']
    
    def __str__(self):
        return f"{self.schedule.name} - {self.get_level_display()}"
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def is_approved(self):
        return self.status == 'approved'
    
    @property
    def is_rejected(self):
        return self.status == 'rejected'