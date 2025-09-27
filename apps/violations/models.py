from django.db import models
from apps.users.models import User


class Violation(models.Model):
    """نموذج المخالفة"""
    
    VIOLATION_TYPE_CHOICES = [
        ('attendance', 'مخالفة حضور وانصراف'),
        ('behavior', 'مخالفة سلوكية'),
        ('performance', 'مخالفة أداء'),
        ('safety', 'مخالفة أمان'),
        ('other', 'أخرى'),
    ]
    
    SEVERITY_CHOICES = [
        ('minor', 'بسيطة'),
        ('moderate', 'متوسطة'),
        ('major', 'كبيرة'),
        ('critical', 'حرجة'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'في الانتظار'),
        ('investigating', 'قيد التحقيق'),
        ('resolved', 'محلولة'),
        ('closed', 'مغلقة'),
    ]
    
    ACTION_CHOICES = [
        ('warning', 'تحذير شفوي'),
        ('written_warning', 'تحذير كتابي'),
        ('suspension', 'إيقاف'),
        ('fine', 'غرامة مالية'),
        ('termination', 'فصل'),
        ('other', 'أخرى'),
    ]
    
    # المعلومات الأساسية
    employee = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='الموظف', related_name='violations')
    violation_type = models.CharField(max_length=20, choices=VIOLATION_TYPE_CHOICES, verbose_name='نوع المخالفة')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, verbose_name='درجة الخطورة')
    
    # تفاصيل المخالفة
    description = models.TextField(verbose_name='وصف المخالفة')
    date_occurred = models.DateTimeField(verbose_name='تاريخ وقوع المخالفة')
    location = models.CharField(max_length=200, blank=True, verbose_name='مكان وقوع المخالفة')
    
    # الإجراءات المتخذة
    action_taken = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name='الإجراء المتخذ')
    action_description = models.TextField(blank=True, verbose_name='وصف الإجراء')
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='مبلغ الغرامة')
    
    # الحالة والموافقات
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='الحالة')
    
    # معلومات إضافية
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    witnesses = models.TextField(blank=True, verbose_name='الشهود')
    
    # الموافقات
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='اعتمد بواسطة')
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ الموافقة')
    
    # تواريخ النظام
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_violations', verbose_name='أنشأ بواسطة')
    
    class Meta:
        verbose_name = 'مخالفة'
        verbose_name_plural = 'المخالفات'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.get_violation_type_display()} ({self.date_occurred.date()})"
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def is_resolved(self):
        return self.status == 'resolved'
    
    @property
    def is_closed(self):
        return self.status == 'closed'