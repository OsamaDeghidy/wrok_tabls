from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class LeaveRequest(models.Model):
    """نموذج طلب الإجازة"""
    
    TYPE_CHOICES = [
        ('annual', 'إجازة سنوية'),
        ('sick', 'إجازة مرضية'),
        ('emergency', 'إجازة طارئة'),
        ('maternity', 'إجازة أمومة'),
        ('paternity', 'إجازة أبوة'),
        ('unpaid', 'إجازة بدون راتب'),
        ('personal', 'إجازة شخصية'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'معلق'),
        ('approved', 'معتمد'),
        ('rejected', 'مرفوض'),
        ('cancelled', 'ملغي'),
    ]
    
    # Fields
    employee = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name='الموظف',
        related_name='leave_requests'
    )
    
    leave_type = models.CharField(
        max_length=20, 
        choices=TYPE_CHOICES,
        verbose_name='نوع الإجازة'
    )
    
    start_date = models.DateField(
        verbose_name='تاريخ البداية'
    )
    
    end_date = models.DateField(
        verbose_name='تاريخ النهاية'
    )
    
    days_count = models.PositiveIntegerField(
        verbose_name='عدد الأيام'
    )
    
    reason = models.TextField(
        verbose_name='سبب الإجازة'
    )
    
    emergency_contact = models.CharField(
        max_length=20, 
        blank=True,
        verbose_name='رقم الطوارئ'
    )
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name='الحالة'
    )
    
    manager_notes = models.TextField(
        blank=True,
        verbose_name='ملاحظات المدير'
    )
    
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='approved_leaves',
        verbose_name='وافق بواسطة'
    )
    
    approved_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='تاريخ الموافقة'
    )
    
    attachments = models.JSONField(
        default=list,
        blank=True,
        null=True,
        verbose_name='المرفقات',
        help_text='قائمة بمسارات الملفات المرفقة'
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name='ملاحظات إضافية'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث'
    )
    
    class Meta:
        verbose_name = 'طلب الإجازة'
        verbose_name_plural = 'طلبات الإجازات'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.get_leave_type_display()} ({self.start_date} إلى {self.end_date})"
    
    def clean(self):
        """التحقق من صحة البيانات"""
        super().clean()
        
        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                raise ValidationError({
                    'end_date': 'تاريخ النهاية يجب أن يكون بعد تاريخ البداية'
                })
        
        # التحقق من أن الموظف لا يطلب إجازة في الماضي
        from django.utils import timezone
        if self.start_date and self.start_date < timezone.now().date():
            raise ValidationError({
                'start_date': 'لا يمكن طلب إجازة في الماضي'
            })
        
        # التحقق من عدم وجود إجازات متداخلة
        # فقط إذا كان employee محدد والطلب موجود بالفعل في قاعدة البيانات
        if (hasattr(self, 'employee') and self.employee and 
            self.start_date and self.end_date and self.pk):
            overlapping_leaves = LeaveRequest.objects.filter(
                employee=self.employee,
                status__in=['pending', 'approved'],
                start_date__lte=self.end_date,
                end_date__gte=self.start_date
            ).exclude(pk=self.pk)
            
            if overlapping_leaves.exists():
                raise ValidationError({
                    'start_date': 'يوجد إجازة متداخلة مع هذه الفترة'
                })
    
    def save(self, *args, **kwargs):
        # حساب عدد الأيام تلقائياً
        if self.start_date and self.end_date and not self.days_count:
            from datetime import timedelta
            delta = self.end_date - self.start_date
            self.days_count = delta.days + 1  # +1 لتضمين اليوم الأخير
        
        super().save(*args, **kwargs)
    
    def approve(self, approved_by):
        """موافقة على طلب الإجازة"""
        from django.utils import timezone
        
        self.status = 'approved'
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        self.save()
    
    def reject(self, approved_by, manager_notes=''):
        """رفض طلب الإجازة"""
        from django.utils import timezone
        
        self.status = 'rejected'
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        self.manager_notes = manager_notes
        self.save()
    
    def cancel(self):
        """إلغاء طلب الإجازة"""
        self.status = 'cancelled'
        self.save()
    
    def get_leave_balance(self):
        """الحصول على رصيد الإجازات للموظف"""
        # هذا يمكن تطويره لاحقاً لحساب الرصيد الفعلي
        balances = {
            'annual': 30,  # إجازة سنوية
            'sick': 10,    # إجازة مرضية
            'emergency': 5, # إجازة طارئة
        }
        return balances.get(self.leave_type, 0)


class LeaveBalance(models.Model):
    """نموذج رصيد الإجازات"""
    
    LEAVE_TYPE_CHOICES = [
        ('annual', 'إجازة سنوية'),
        ('sick', 'إجازة مرضية'),
        ('emergency', 'إجازة طارئة'),
        ('maternity', 'إجازة أمومة'),
        ('paternity', 'إجازة أبوة'),
    ]
    
    employee = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name='الموظف',
        related_name='leave_balances'
    )
    
    leave_type = models.CharField(
        max_length=20, 
        choices=LEAVE_TYPE_CHOICES,
        verbose_name='نوع الإجازة'
    )
    
    total_days = models.PositiveIntegerField(
        default=0,
        verbose_name='إجمالي الأيام'
    )
    
    used_days = models.PositiveIntegerField(
        default=0,
        verbose_name='الأيام المستخدمة'
    )
    
    remaining_days = models.PositiveIntegerField(
        default=0,
        verbose_name='الأيام المتبقية'
    )
    
    year = models.PositiveIntegerField(
        verbose_name='السنة'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث'
    )
    
    class Meta:
        verbose_name = 'رصيد الإجازة'
        verbose_name_plural = 'أرصدة الإجازات'
        unique_together = ['employee', 'leave_type', 'year']
        ordering = ['employee', 'leave_type', 'year']
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.get_leave_type_display()} ({self.year})"
    
    def save(self, *args, **kwargs):
        # حساب الأيام المتبقية
        self.remaining_days = self.total_days - self.used_days
        super().save(*args, **kwargs)
    
    @classmethod
    def get_employee_balances(cls, employee, year=None):
        """الحصول على أرصدة الموظف لسنة معينة"""
        from datetime import datetime
        
        if year is None:
            year = datetime.now().year
        
        balances = cls.objects.filter(employee=employee, year=year)
        
        # إنشاء أرصدة افتراضية إذا لم تكن موجودة
        default_balances = {
            'annual': 30,
            'sick': 10,
            'emergency': 5,
        }
        
        for leave_type, default_days in default_balances.items():
            balance, created = cls.objects.get_or_create(
                employee=employee,
                leave_type=leave_type,
                year=year,
                defaults={
                    'total_days': default_days,
                    'used_days': 0,
                    'remaining_days': default_days
                }
            )
        
        return cls.objects.filter(employee=employee, year=year)