from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError


class ApprovalFlow(models.Model):
    """نموذج مسار الموافقة"""
    
    STATUS_CHOICES = [
        ('pending', 'معلق'),
        ('in_progress', 'قيد المراجعة'),
        ('approved', 'معتمد'),
        ('rejected', 'مرفوض'),
        ('cancelled', 'ملغي'),
    ]
    
    # Fields
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name='نوع الكائن المرتبط'
    )
    
    object_id = models.PositiveIntegerField(
        verbose_name='معرف الكائن المرتبط'
    )
    
    related_object = GenericForeignKey(
        'content_type', 
        'object_id'
    )
    
    current_step = models.PositiveIntegerField(
        default=1,
        verbose_name='الخطوة الحالية'
    )
    
    total_steps = models.PositiveIntegerField(
        verbose_name='إجمالي الخطوات'
    )
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name='الحالة'
    )
    
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name='أنشأ بواسطة',
        related_name='created_approval_flows'
    )
    
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='وافق بواسطة',
        related_name='approved_flows'
    )
    
    approved_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='تاريخ الموافقة'
    )
    
    rejection_reason = models.TextField(
        blank=True,
        verbose_name='سبب الرفض'
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
        verbose_name = 'مسار الموافقة'
        verbose_name_plural = 'مسارات الموافقات'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"مسار الموافقة #{self.id} - {self.get_related_object_display()}"
    
    def get_related_object_display(self):
        """عرض الكائن المرتبط"""
        try:
            model_class = self.content_type.model_class()
            obj = model_class.objects.get(pk=self.object_id)
            return str(obj)
        except:
            return f"{self.content_type.model} #{self.object_id}"
    
    def clean(self):
        """التحقق من صحة البيانات"""
        super().clean()
        
        if self.current_step > self.total_steps:
            raise ValidationError({
                'current_step': 'الخطوة الحالية لا يمكن أن تكون أكبر من إجمالي الخطوات'
            })
    
    def save(self, *args, **kwargs):
        # تحديث الحالة بناءً على الخطوة الحالية
        if self.current_step == 1 and self.status == 'pending':
            self.status = 'in_progress'
        elif self.current_step > self.total_steps:
            self.status = 'approved'
        
        super().save(*args, **kwargs)
    
    def approve_current_step(self, user, comment=''):
        """الموافقة على الخطوة الحالية"""
        from django.utils import timezone
        
        # إنشاء خطوة الموافقة
        ApprovalStep.objects.create(
            approval_flow=self,
            step_order=self.current_step,
            assigned_to=user,
            status='approved',
            action='approve',
            comment=comment,
            acted_at=timezone.now()
        )
        
        # الانتقال للخطوة التالية
        self.current_step += 1
        
        # إذا انتهت جميع الخطوات، قم بالموافقة النهائية
        if self.current_step > self.total_steps:
            self.status = 'approved'
            self.approved_by = user
            self.approved_at = timezone.now()
        
        self.save()
    
    def reject(self, user, reason=''):
        """رفض الموافقة"""
        from django.utils import timezone
        
        # إنشاء خطوة الرفض
        ApprovalStep.objects.create(
            approval_flow=self,
            step_order=self.current_step,
            assigned_to=user,
            status='rejected',
            action='reject',
            comment=reason,
            acted_at=timezone.now()
        )
        
        self.status = 'rejected'
        self.rejection_reason = reason
        self.save()
    
    def cancel(self, user, reason=''):
        """إلغاء الموافقة"""
        from django.utils import timezone
        
        # إنشاء خطوة الإلغاء
        ApprovalStep.objects.create(
            approval_flow=self,
            step_order=self.current_step,
            assigned_to=user,
            status='cancelled',
            action='cancel',
            comment=reason,
            acted_at=timezone.now()
        )
        
        self.status = 'cancelled'
        self.notes = reason
        self.save()
    
    def get_current_step_info(self):
        """الحصول على معلومات الخطوة الحالية"""
        if self.current_step <= self.total_steps:
            return self.get_step_role(self.current_step)
        return None
    
    def get_step_role(self, step_number):
        """الحصول على الدور المطلوب للخطوة"""
        roles = [
            'coordinator',      # الخطوة 1: المنسق
            'region_manager',   # الخطوة 2: مدير المنطقة
            'operations_manager', # الخطوة 3: مدير العمليات
            'admin_manager',    # الخطوة 4: مدير الإدارة
        ]
        
        if step_number <= len(roles):
            return roles[step_number - 1]
        return 'super_admin'  # الخطوات الإضافية للمدير العام
    
    def get_pending_users(self):
        """الحصول على المستخدمين المطلوب منهم موافقة"""
        current_role = self.get_current_step_info()
        if current_role:
            from apps.users.models import UserProfile
            return User.objects.filter(
                profile__role=current_role,
                profile__status='active'
            )
        return User.objects.none()


class ApprovalStep(models.Model):
    """نموذج خطوة الموافقة"""
    
    STATUS_CHOICES = [
        ('pending', 'معلق'),
        ('approved', 'معتمد'),
        ('rejected', 'مرفوض'),
        ('cancelled', 'ملغي'),
    ]
    
    ACTION_CHOICES = [
        ('approve', 'موافقة'),
        ('reject', 'رفض'),
        ('cancel', 'إلغاء'),
        ('request_changes', 'طلب تعديل'),
    ]
    
    # Fields
    approval_flow = models.ForeignKey(
        ApprovalFlow, 
        on_delete=models.CASCADE, 
        related_name='steps',
        verbose_name='مسار الموافقة'
    )
    
    step_order = models.PositiveIntegerField(
        verbose_name='ترتيب الخطوة'
    )
    
    required_role = models.CharField(
        max_length=50,
        verbose_name='الدور المطلوب'
    )
    
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        verbose_name='مُعيَّن لـ',
        related_name='assigned_approval_steps'
    )
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name='الحالة'
    )
    
    action = models.CharField(
        max_length=20, 
        choices=ACTION_CHOICES,
        blank=True,
        verbose_name='الإجراء'
    )
    
    comment = models.TextField(
        blank=True,
        verbose_name='تعليق'
    )
    
    acted_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='تاريخ الإجراء'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء'
    )
    
    class Meta:
        verbose_name = 'خطوة الموافقة'
        verbose_name_plural = 'خطوات الموافقات'
        ordering = ['step_order']
        unique_together = ['approval_flow', 'step_order']
    
    def __str__(self):
        return f"خطوة {self.step_order} - {self.get_required_role_display()}"
    
    def get_required_role_display(self):
        """عرض الدور المطلوب"""
        role_display = {
            'coordinator': 'منسق',
            'region_manager': 'مدير المنطقة',
            'operations_manager': 'مدير العمليات',
            'admin_manager': 'مدير الإدارة',
            'super_admin': 'مدير عام',
        }
        return role_display.get(self.required_role, self.required_role)
    
    def clean(self):
        """التحقق من صحة البيانات"""
        super().clean()
        
        if self.step_order > self.approval_flow.total_steps:
            raise ValidationError({
                'step_order': 'ترتيب الخطوة لا يمكن أن يكون أكبر من إجمالي خطوات المسار'
            })
    
    @classmethod
    def create_default_steps(cls, approval_flow, created_by):
        """إنشاء خطوات الموافقة الافتراضية"""
        from apps.users.models import UserProfile
        
        # تحديد عدد الخطوات بناءً على نوع الكائن
        if approval_flow.content_type.model == 'schedule':
            # للجداول: منسق -> مدير المنطقة -> مدير العمليات -> مدير الإدارة
            steps = [
                ('coordinator', 'منسق'),
                ('region_manager', 'مدير المنطقة'),
                ('operations_manager', 'مدير العمليات'),
                ('admin_manager', 'مدير الإدارة'),
            ]
        elif approval_flow.content_type.model == 'leaverequest':
            # للإجازات: مدير المعرض -> منسق (إذا لزم الأمر)
            if hasattr(created_by, 'profile') and created_by.profile.is_branch_manager:
                steps = [
                    ('coordinator', 'منسق'),
                ]
            else:
                steps = [
                    ('branch_manager', 'مدير المعرض'),
                ]
        else:
            # للمخالفات: مدير المعرض
            steps = [
                ('branch_manager', 'مدير المعرض'),
            ]
        
        approval_flow.total_steps = len(steps)
        approval_flow.save()
        
        # إنشاء الخطوات
        for order, (role, role_display) in enumerate(steps, 1):
            cls.objects.create(
                approval_flow=approval_flow,
                step_order=order,
                required_role=role
            )
        
        return cls.objects.filter(approval_flow=approval_flow)