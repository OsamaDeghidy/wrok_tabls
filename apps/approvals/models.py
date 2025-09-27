from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class Approval(models.Model):
    """نموذج الموافقات العام"""
    
    APPROVAL_STATUS_CHOICES = [
        ('pending', 'في الانتظار'),
        ('approved', 'معتمد'),
        ('rejected', 'مرفوض'),
    ]
    
    APPROVAL_TYPE_CHOICES = [
        ('schedule', 'جدول تشغيلي'),
        ('leave', 'إجازة'),
        ('violation', 'مخالفة'),
        ('employee', 'موظف'),
        ('branch', 'فرع'),
        ('other', 'أخرى'),
    ]
    
    # العلاقة العامة مع النماذج الأخرى
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name='نوع المحتوى')
    object_id = models.PositiveIntegerField(verbose_name='معرف الكائن')
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # معلومات الموافقة
    approval_type = models.CharField(max_length=20, choices=APPROVAL_TYPE_CHOICES, verbose_name='نوع الموافقة')
    status = models.CharField(max_length=20, choices=APPROVAL_STATUS_CHOICES, default='pending', verbose_name='الحالة')
    
    # معلومات المعتمد
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='المعتمد')
    comments = models.TextField(blank=True, verbose_name='تعليقات')
    
    # تواريخ النظام
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ الموافقة')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_approvals', verbose_name='أنشأ بواسطة')
    
    class Meta:
        verbose_name = 'موافقة'
        verbose_name_plural = 'الموافقات'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_approval_type_display()} - {self.content_object} ({self.get_status_display()})"
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def is_approved(self):
        return self.status == 'approved'
    
    @property
    def is_rejected(self):
        return self.status == 'rejected'


class ApprovalFlow(models.Model):
    """نموذج مسار الموافقات"""
    
    FLOW_TYPE_CHOICES = [
        ('schedule', 'جدول تشغيلي'),
        ('leave', 'إجازة'),
        ('violation', 'مخالفة'),
        ('employee', 'موظف'),
        ('branch', 'فرع'),
    ]
    
    APPROVAL_LEVEL_CHOICES = [
        ('coordinator', 'منسق'),
        ('region_manager', 'مدير المنطقة'),
        ('operations_manager', 'مدير العمليات'),
        ('admin_manager', 'مدير الإدارة'),
    ]
    
    # معلومات المسار
    name = models.CharField(max_length=100, verbose_name='اسم المسار')
    flow_type = models.CharField(max_length=20, choices=FLOW_TYPE_CHOICES, verbose_name='نوع المسار')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    
    # خطوات الموافقة
    steps = models.JSONField(default=list, verbose_name='خطوات الموافقة')
    
    # تواريخ النظام
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='أنشأ بواسطة')
    
    class Meta:
        verbose_name = 'مسار الموافقات'
        verbose_name_plural = 'مسارات الموافقات'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_flow_type_display()})"
    
    def get_steps_count(self):
        """عدد خطوات الموافقة"""
        return len(self.steps) if self.steps else 0