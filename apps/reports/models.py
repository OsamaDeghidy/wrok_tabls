from django.db import models
from django.contrib.auth.models import User


class Report(models.Model):
    """نموذج التقرير"""
    
    REPORT_TYPE_CHOICES = [
        ('attendance', 'تقرير الحضور والانصراف'),
        ('schedule', 'تقرير الجداول التشغيلية'),
        ('leaves', 'تقرير الإجازات'),
        ('violations', 'تقرير المخالفات'),
        ('performance', 'تقرير الأداء'),
        ('financial', 'تقرير مالي'),
        ('custom', 'تقرير مخصص'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'مسودة'),
        ('generated', 'مولد'),
        ('scheduled', 'مجدول'),
        ('failed', 'فشل'),
    ]
    
    # المعلومات الأساسية
    name = models.CharField(max_length=200, verbose_name='اسم التقرير')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES, verbose_name='نوع التقرير')
    
    # معايير التقرير
    filters = models.JSONField(default=dict, verbose_name='الفلاتر')
    
    # الحالة
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='الحالة')
    
    # معلومات إضافية
    description = models.TextField(blank=True, verbose_name='وصف التقرير')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    
    # تواريخ النظام
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='أنشأ بواسطة')
    
    class Meta:
        verbose_name = 'تقرير'
        verbose_name_plural = 'التقارير'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"
    
    @property
    def is_draft(self):
        return self.status == 'draft'
    
    @property
    def is_generated(self):
        return self.status == 'generated'


class ReportTemplate(models.Model):
    """نموذج قالب التقرير"""
    
    TEMPLATE_TYPE_CHOICES = [
        ('attendance', 'قالب الحضور والانصراف'),
        ('schedule', 'قالب الجداول التشغيلية'),
        ('leaves', 'قالب الإجازات'),
        ('violations', 'قالب المخالفات'),
        ('performance', 'قالب الأداء'),
        ('financial', 'قالب مالي'),
    ]
    
    # المعلومات الأساسية
    name = models.CharField(max_length=200, verbose_name='اسم القالب')
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES, verbose_name='نوع القالب')
    
    # إعدادات القالب
    settings = models.JSONField(default=dict, verbose_name='إعدادات القالب')
    
    # معلومات إضافية
    description = models.TextField(blank=True, verbose_name='وصف القالب')
    is_default = models.BooleanField(default=False, verbose_name='القالب الافتراضي')
    
    # تواريخ النظام
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='أنشأ بواسطة')
    
    class Meta:
        verbose_name = 'قالب تقرير'
        verbose_name_plural = 'قوالب التقارير'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"