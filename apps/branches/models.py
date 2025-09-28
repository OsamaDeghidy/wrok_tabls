from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Branch(models.Model):
    """نموذج الفرع"""
    
    TYPE_CHOICES = [
        ('main', 'الفرع الرئيسي'),
        ('branch', 'فرع فرعي'),
        ('warehouse', 'مستودع'),
        ('office', 'مكتب'),
    ]
    
    CATEGORY_CHOICES = [
        ('A', 'الفئة أ'),
        ('B', 'الفئة ب'),
        ('C', 'الفئة ج'),
        ('D', 'الفئة د'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'نشط'),
        ('inactive', 'غير نشط'),
        ('maintenance', 'تحت الصيانة'),
    ]
    
    REGION_CHOICES = [
        ('riyadh', 'الرياض'),
        ('makkah', 'مكة المكرمة'),
        ('eastern', 'المنطقة الشرقية'),
        ('asir', 'عسير'),
        ('jazan', 'جازان'),
        ('medina', 'المدينة المنورة'),
        ('qassim', 'القصيم'),
        ('hail', 'حائل'),
        ('tabuk', 'تبوك'),
        ('northern', 'الحدود الشمالية'),
        ('jazan', 'جازان'),
        ('najran', 'نجران'),
        ('albaha', 'الباحة'),
        ('jouf', 'الجوف'),
    ]
    
    # Fields
    name = models.CharField(
        max_length=200, 
        verbose_name='اسم الفرع'
    )
    
    code = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name='كود الفرع'
    )
    
    type = models.CharField(
        max_length=20, 
        choices=TYPE_CHOICES,
        verbose_name='نوع الفرع'
    )
    
    category = models.CharField(
        max_length=1,
        choices=CATEGORY_CHOICES,
        default='B',
        verbose_name='فئة الفرع'
    )
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='active',
        verbose_name='الحالة'
    )
    
    address = models.TextField(
        verbose_name='العنوان'
    )
    
    city = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name='المدينة'
    )
    
    region = models.CharField(
        max_length=50, 
        choices=REGION_CHOICES,
        verbose_name='المنطقة'
    )
    
    postal_code = models.CharField(
        max_length=20, 
        blank=True,
        verbose_name='الرمز البريدي'
    )
    
    phone = models.CharField(
        max_length=20, 
        blank=True,
        verbose_name='رقم الهاتف'
    )
    
    email = models.EmailField(
        blank=True,
        verbose_name='البريد الإلكتروني'
    )
    
    manager = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='مدير الفرع',
        related_name='managed_branches'
    )
    
    capacity = models.PositiveIntegerField(
        default=1,
        verbose_name='السعة الاستيعابية'
    )
    
    opening_date = models.DateField(
        null=True, 
        blank=True,
        verbose_name='تاريخ الافتتاح'
    )
    
    working_days = models.JSONField(
        default=list,
        verbose_name='أيام العمل',
        help_text='قائمة بأيام العمل مثل ["saturday", "sunday", "monday"]'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='وصف الفرع'
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name='ملاحظات'
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
        verbose_name = 'الفرع'
        verbose_name_plural = 'الفروع'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def get_working_days_display(self):
        """عرض أيام العمل بصورة مقروءة"""
        days_map = {
            'saturday': 'السبت',
            'sunday': 'الأحد',
            'monday': 'الاثنين',
            'tuesday': 'الثلاثاء',
            'wednesday': 'الأربعاء',
            'thursday': 'الخميس',
            'friday': 'الجمعة',
        }
        return [days_map.get(day, day) for day in self.working_days]
    
    def get_employees_count(self):
        """عدد الموظفين في الفرع"""
        return self.employees.filter(status='active').count()
    
    def get_active_shifts_count(self):
        """عدد الشفتات النشطة"""
        return self.shifts.filter(is_active=True).count()
    
    def clean(self):
        """التحقق من صحة البيانات"""
        super().clean()
        
        # التحقق من أن المدير له دور مدير معرض
        if self.manager:
            if hasattr(self.manager, 'profile'):
                if not self.manager.profile.is_branch_manager:
                    raise ValidationError({
                        'manager': 'المدير يجب أن يكون له دور مدير معرض'
                    })


class BranchShift(models.Model):
    """نموذج شفت الفرع"""
    
    branch = models.ForeignKey(
        Branch, 
        on_delete=models.CASCADE, 
        related_name='shifts',
        verbose_name='الفرع'
    )
    
    name = models.CharField(
        max_length=100,
        verbose_name='اسم الشفت'
    )
    
    start_time = models.TimeField(
        verbose_name='ساعة البداية'
    )
    
    end_time = models.TimeField(
        verbose_name='ساعة النهاية'
    )
    
    break_start = models.TimeField(
        null=True, 
        blank=True,
        verbose_name='ساعة بداية الاستراحة'
    )
    
    break_end = models.TimeField(
        null=True, 
        blank=True,
        verbose_name='ساعة نهاية الاستراحة'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط'
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
        verbose_name = 'شفت الفرع'
        verbose_name_plural = 'شفتات الفروع'
        ordering = ['start_time']
        unique_together = ['branch', 'name']
    
    def __str__(self):
        return f"{self.branch.name} - {self.name}"
    
    def get_duration(self):
        """حساب مدة الشفت بالساعات"""
        from datetime import datetime, timedelta
        
        start = datetime.combine(datetime.today(), self.start_time)
        end = datetime.combine(datetime.today(), self.end_time)
        
        # إذا كان وقت النهاية أقل من وقت البداية، فهذا يعني أنه شفت ليلي
        if end <= start:
            end += timedelta(days=1)
        
        duration = end - start
        
        # طرح وقت الاستراحة إذا كان محدداً
        if self.break_start and self.break_end:
            break_start = datetime.combine(datetime.today(), self.break_start)
            break_end = datetime.combine(datetime.today(), self.break_end)
            
            # إذا كان وقت نهاية الاستراحة أقل من وقت البداية، فهذا يعني أنه استراحة ليلية
            if break_end <= break_start:
                break_end += timedelta(days=1)
            
            break_duration = break_end - break_start
            duration -= break_duration
        
        return duration.total_seconds() / 3600  # تحويل إلى ساعات
    
    def clean(self):
        """التحقق من صحة البيانات"""
        super().clean()
        
        # التحقق من أن وقت النهاية بعد وقت البداية (أو في اليوم التالي)
        if self.start_time and self.end_time:
            # إذا كان وقت النهاية أقل من وقت البداية، فهذا يعني أنه شفت ليلي (مقبول)
            if self.end_time <= self.start_time:
                # شفت ليلي - مقبول
                pass
            else:
                # شفت نهاري عادي - مقبول
                pass
        
        # التحقق من وقت الاستراحة
        if self.break_start and self.break_end:
            if self.break_end <= self.break_start:
                # استراحة ليلية - مقبول
                pass
            else:
                # استراحة نهارية عادية - مقبول
                pass