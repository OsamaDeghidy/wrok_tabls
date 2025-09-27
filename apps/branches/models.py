from django.db import models
from apps.users.models import User
import json


class Branch(models.Model):
    """نموذج الفرع/المعرض"""
    
    TYPE_CHOICES = [
        ('main', 'الفرع الرئيسي'),
        ('branch', 'فرع فرعي'),
        ('warehouse', 'مستودع'),
        ('office', 'مكتب'),
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
    ]
    
    # المعلومات الأساسية
    name = models.CharField(max_length=200, verbose_name='اسم الفرع')
    code = models.CharField(max_length=50, unique=True, verbose_name='كود الفرع')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='branch', verbose_name='نوع الفرع')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='الحالة')
    
    # معلومات الموقع
    address = models.TextField(verbose_name='العنوان')
    city = models.CharField(max_length=100, blank=True, verbose_name='المدينة')
    region = models.CharField(max_length=20, choices=REGION_CHOICES, blank=True, verbose_name='المنطقة')
    postal_code = models.CharField(max_length=20, blank=True, verbose_name='الرمز البريدي')
    
    # معلومات الاتصال
    phone = models.CharField(max_length=20, blank=True, verbose_name='رقم الهاتف')
    email = models.EmailField(blank=True, verbose_name='البريد الإلكتروني')
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='مدير الفرع', related_name='managed_branches')
    
    # إعدادات التشغيل
    capacity = models.PositiveIntegerField(default=50, verbose_name='السعة الاستيعابية')
    working_days = models.JSONField(default=list, verbose_name='أيام العمل')
    shifts = models.JSONField(default=list, verbose_name='الشفتات')
    
    # معلومات إضافية
    opening_date = models.DateField(null=True, blank=True, verbose_name='تاريخ الافتتاح')
    description = models.TextField(blank=True, verbose_name='وصف الفرع')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    
    # تواريخ النظام
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='أنشأ بواسطة', related_name='created_branches')
    
    class Meta:
        verbose_name = 'فرع'
        verbose_name_plural = 'الفروع'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def get_working_days_display(self):
        """عرض أيام العمل بشكل مقروء"""
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
    
    def get_shifts_count(self):
        """عدد الشفتات"""
        return len(self.shifts) if self.shifts else 0
    
    def is_active(self):
        return self.status == 'active'


class Shift(models.Model):
    """نموذج الشفت"""
    
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='shift_set', verbose_name='الفرع')
    name = models.CharField(max_length=100, verbose_name='اسم الشفت')
    start_time = models.TimeField(verbose_name='ساعة البداية')
    end_time = models.TimeField(verbose_name='ساعة النهاية')
    break_start = models.TimeField(null=True, blank=True, verbose_name='ساعة بداية الاستراحة')
    break_end = models.TimeField(null=True, blank=True, verbose_name='ساعة نهاية الاستراحة')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    
    # تواريخ النظام
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    
    class Meta:
        verbose_name = 'شفت'
        verbose_name_plural = 'الشفتات'
        ordering = ['start_time']
        unique_together = ['branch', 'name']
    
    def __str__(self):
        return f"{self.branch.name} - {self.name} ({self.start_time} - {self.end_time})"
    
    def duration(self):
        """حساب مدة الشفت بالساعات"""
        from datetime import datetime, timedelta
        
        start = datetime.combine(datetime.today(), self.start_time)
        end = datetime.combine(datetime.today(), self.end_time)
        
        # التعامل مع الشفتات التي تمتد لليوم التالي
        if end <= start:
            end += timedelta(days=1)
        
        # حساب مدة الاستراحة
        break_duration = timedelta()
        if self.break_start and self.break_end:
            break_start = datetime.combine(datetime.today(), self.break_start)
            break_end = datetime.combine(datetime.today(), self.break_end)
            if break_end <= break_start:
                break_end += timedelta(days=1)
            break_duration = break_end - break_start
        
        total_duration = end - start - break_duration
        return total_duration.total_seconds() / 3600  # تحويل إلى ساعات