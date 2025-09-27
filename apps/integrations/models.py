from django.db import models
from django.contrib.auth.models import User


class Integration(models.Model):
    """نموذج التكامل"""
    
    INTEGRATION_TYPE_CHOICES = [
        ('hr_system', 'نظام الموارد البشرية'),
        ('payroll', 'نظام الرواتب'),
        ('attendance', 'نظام الحضور والانصراف'),
        ('external_api', 'API خارجي'),
        ('file_import', 'استيراد ملفات'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'نشط'),
        ('inactive', 'غير نشط'),
        ('error', 'خطأ'),
        ('maintenance', 'تحت الصيانة'),
    ]
    
    # المعلومات الأساسية
    name = models.CharField(max_length=200, verbose_name='اسم التكامل')
    integration_type = models.CharField(max_length=20, choices=INTEGRATION_TYPE_CHOICES, verbose_name='نوع التكامل')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inactive', verbose_name='الحالة')
    
    # إعدادات التكامل
    configuration = models.JSONField(default=dict, verbose_name='إعدادات التكامل')
    
    # معلومات إضافية
    description = models.TextField(blank=True, verbose_name='وصف التكامل')
    last_sync = models.DateTimeField(null=True, blank=True, verbose_name='آخر مزامنة')
    
    # تواريخ النظام
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='أنشأ بواسطة')
    
    class Meta:
        verbose_name = 'تكامل'
        verbose_name_plural = 'التكاملات'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_integration_type_display()})"
    
    @property
    def is_active(self):
        return self.status == 'active'


class ImportJob(models.Model):
    """نموذج مهمة الاستيراد"""
    
    STATUS_CHOICES = [
        ('pending', 'في الانتظار'),
        ('processing', 'قيد المعالجة'),
        ('completed', 'مكتمل'),
        ('failed', 'فشل'),
        ('cancelled', 'ملغي'),
    ]
    
    # المعلومات الأساسية
    name = models.CharField(max_length=200, verbose_name='اسم المهمة')
    file_path = models.CharField(max_length=500, verbose_name='مسار الملف')
    file_size = models.PositiveIntegerField(verbose_name='حجم الملف')
    
    # الحالة والنتائج
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='الحالة')
    total_rows = models.PositiveIntegerField(default=0, verbose_name='إجمالي الصفوف')
    processed_rows = models.PositiveIntegerField(default=0, verbose_name='الصفوف المعالجة')
    success_rows = models.PositiveIntegerField(default=0, verbose_name='الصفوف الناجحة')
    error_rows = models.PositiveIntegerField(default=0, verbose_name='الصفوف الخاطئة')
    
    # معلومات إضافية
    errors = models.JSONField(default=list, verbose_name='الأخطاء')
    mapping = models.JSONField(default=dict, verbose_name='خريطة الحقول')
    
    # تواريخ النظام
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ الإكمال')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='أنشأ بواسطة')
    
    class Meta:
        verbose_name = 'مهمة استيراد'
        verbose_name_plural = 'مهام الاستيراد'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def is_completed(self):
        return self.status == 'completed'
    
    @property
    def is_failed(self):
        return self.status == 'failed'
    
    @property
    def progress_percentage(self):
        """نسبة التقدم"""
        if self.total_rows == 0:
            return 0
        return (self.processed_rows / self.total_rows) * 100


class ExportJob(models.Model):
    """نموذج مهمة التصدير"""
    
    STATUS_CHOICES = [
        ('pending', 'في الانتظار'),
        ('processing', 'قيد المعالجة'),
        ('completed', 'مكتمل'),
        ('failed', 'فشل'),
        ('cancelled', 'ملغي'),
    ]
    
    EXPORT_TYPE_CHOICES = [
        ('employees', 'الموظفين'),
        ('schedules', 'الجداول التشغيلية'),
        ('leaves', 'الإجازات'),
        ('violations', 'المخالفات'),
        ('reports', 'التقارير'),
    ]
    
    # المعلومات الأساسية
    name = models.CharField(max_length=200, verbose_name='اسم المهمة')
    export_type = models.CharField(max_length=20, choices=EXPORT_TYPE_CHOICES, verbose_name='نوع التصدير')
    file_format = models.CharField(max_length=10, default='excel', verbose_name='تنسيق الملف')
    
    # الحالة والنتائج
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='الحالة')
    file_path = models.CharField(max_length=500, blank=True, verbose_name='مسار الملف')
    file_size = models.PositiveIntegerField(null=True, blank=True, verbose_name='حجم الملف')
    
    # معلومات إضافية
    filters = models.JSONField(default=dict, verbose_name='الفلاتر')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    
    # تواريخ النظام
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ الإكمال')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='أنشأ بواسطة')
    
    class Meta:
        verbose_name = 'مهمة تصدير'
        verbose_name_plural = 'مهام التصدير'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_export_type_display()})"
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def is_completed(self):
        return self.status == 'completed'
    
    @property
    def is_failed(self):
        return self.status == 'failed'