from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Violation(models.Model):
    """نموذج المخالفة"""
    
    TYPE_CHOICES = [
        ('attendance', 'تأخير'),
        ('absence', 'غياب'),
        ('behavior', 'سلوك'),
        ('performance', 'أداء'),
        ('safety', 'سلامة'),
        ('policy', 'انتهاك سياسة'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'منخفضة'),
        ('medium', 'متوسطة'),
        ('high', 'عالية'),
        ('critical', 'حرجة'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'معلقة'),
        ('investigating', 'قيد التحقيق'),
        ('resolved', 'محلولة'),
        ('escalated', 'مرفوعة'),
        ('archived', 'مؤرشفة'),
    ]
    
    ACTION_CHOICES = [
        ('warning', 'تحذير'),
        ('notice', 'إنذار'),
        ('suspension', 'إيقاف'),
        ('termination', 'فصل'),
        ('training', 'تدريب'),
        ('counseling', 'إرشاد'),
    ]
    
    # Fields
    employee = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name='الموظف',
        related_name='violations'
    )
    
    violation_type = models.CharField(
        max_length=20, 
        choices=TYPE_CHOICES,
        verbose_name='نوع المخالفة'
    )
    
    date = models.DateField(
        verbose_name='التاريخ'
    )
    
    time = models.TimeField(
        verbose_name='الوقت'
    )
    
    description = models.TextField(
        verbose_name='وصف المخالفة'
    )
    
    severity = models.CharField(
        max_length=20, 
        choices=SEVERITY_CHOICES, 
        default='low',
        verbose_name='درجة الخطورة'
    )
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name='الحالة'
    )
    
    action_taken = models.CharField(
        max_length=20, 
        choices=ACTION_CHOICES,
        blank=True,
        verbose_name='الإجراء المتخذ'
    )
    
    action_description = models.TextField(
        blank=True,
        verbose_name='وصف الإجراء المتخذ'
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name='ملاحظات'
    )
    
    witnesses = models.TextField(
        blank=True,
        verbose_name='الشهود',
        help_text='أسماء الشهود إن وجدوا'
    )
    
    evidence = models.JSONField(
        default=list,
        verbose_name='الأدلة',
        help_text='قائمة بمسارات الملفات أو الصور'
    )
    
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_violations',
        verbose_name='أنشأ بواسطة'
    )
    
    investigated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='investigated_violations',
        verbose_name='تحقق بواسطة'
    )
    
    investigation_date = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='تاريخ التحقيق'
    )
    
    resolution_date = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='تاريخ الحل'
    )
    
    archived_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='تاريخ الأرشفة'
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
        verbose_name = 'المخالفة'
        verbose_name_plural = 'المخالفات'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.get_violation_type_display()} ({self.date})"
    
    def clean(self):
        """التحقق من صحة البيانات"""
        super().clean()
        
        # التحقق من أن الموظف والمشرف في نفس الفرع (إذا كان المشرف مدير معرض)
        if self.created_by and hasattr(self.created_by, 'profile'):
            if self.created_by.profile.is_branch_manager:
                if (hasattr(self.employee, 'profile') and 
                    self.employee.profile.branch != self.created_by.profile.branch):
                    raise ValidationError({
                        'employee': 'لا يمكن لمدير المعرض إنشاء مخالفة لموظف من فرع آخر'
                    })
        
        # التحقق من أن المخالفة ليست في المستقبل
        from django.utils import timezone
        violation_datetime = timezone.datetime.combine(self.date, self.time)
        if violation_datetime > timezone.now():
            raise ValidationError({
                'date': 'لا يمكن إنشاء مخالفة في المستقبل'
            })
    
    def save(self, *args, **kwargs):
        # إذا تم تغيير الحالة إلى محلولة، قم بتحديث تاريخ الحل
        if self.status == 'resolved' and not self.resolution_date:
            from django.utils import timezone
            self.resolution_date = timezone.now()
        
        # إذا تم تغيير الحالة إلى مؤرشفة، قم بتحديث تاريخ الأرشفة
        if self.status == 'archived' and not self.archived_at:
            from django.utils import timezone
            self.archived_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def assign_investigator(self, investigator):
        """تعيين محقق للمخالفة"""
        from django.utils import timezone
        
        self.investigated_by = investigator
        self.investigation_date = timezone.now()
        self.status = 'investigating'
        self.save()
    
    def resolve(self, action_taken, action_description='', notes=''):
        """حل المخالفة"""
        from django.utils import timezone
        
        self.status = 'resolved'
        self.action_taken = action_taken
        self.action_description = action_description
        self.notes = notes
        self.resolution_date = timezone.now()
        self.save()
    
    def escalate(self, notes=''):
        """رفع المخالفة"""
        from django.utils import timezone
        
        self.status = 'escalated'
        self.notes = notes
        self.save()
    
    def archive(self):
        """أرشفة المخالفة"""
        from django.utils import timezone
        
        self.status = 'archived'
        self.archived_at = timezone.now()
        self.save()
    
    @classmethod
    def get_employee_violations(cls, employee, year=None):
        """الحصول على مخالفات الموظف لسنة معينة"""
        from datetime import datetime
        
        if year is None:
            year = datetime.now().year
        
        return cls.objects.filter(
            employee=employee,
            date__year=year,
            status__in=['pending', 'investigating', 'resolved']
        ).order_by('-date')
    
    @classmethod
    def get_violations_stats(cls, year=None, month=None):
        """الحصول على إحصائيات المخالفات"""
        from datetime import datetime
        from django.db.models import Count
        
        if year is None:
            year = datetime.now().year
        
        queryset = cls.objects.filter(date__year=year)
        
        if month:
            queryset = queryset.filter(date__month=month)
        
        stats = queryset.aggregate(
            total=Count('id'),
            by_type=Count('violation_type'),
            by_severity=Count('severity'),
            by_status=Count('status')
        )
        
        return stats