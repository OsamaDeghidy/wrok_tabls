from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError
import json
from django.utils import timezone


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

    def _load_notes(self):
        try:
            data = json.loads(self.notes) if self.notes else {}
            if not isinstance(data, dict):
                data = {}
        except Exception:
            data = {}
        return data

    def _save_notes(self, data):
        self.notes = json.dumps(data, ensure_ascii=False)
        self.save(update_fields=['notes', 'updated_at'])

    def _serialize_related_object(self):
        obj = self.related_object
        if not obj:
            return {}
        data = {
            'model': self.content_type.model,
            'id': getattr(obj, 'id', None),
        }
        if hasattr(obj, 'status'):
            data['status'] = getattr(obj, 'status')
        if hasattr(obj, 'branch') and getattr(obj, 'branch', None):
            branch = getattr(obj, 'branch')
            data['branch_id'] = getattr(branch, 'id', None)
            data['branch_name'] = getattr(branch, 'name', '')
            data['region'] = getattr(branch, 'region', '')
        if hasattr(obj, 'start_date'):
            data['start_date'] = getattr(obj, 'start_date', None).isoformat() if getattr(obj, 'start_date', None) else None
        if hasattr(obj, 'end_date'):
            data['end_date'] = getattr(obj, 'end_date', None).isoformat() if getattr(obj, 'end_date', None) else None
        return data

    def add_snapshot(self, step_order, status_label):
        data = self._load_notes()
        snapshots = data.get('snapshots', [])
        snapshots.append({
            'step': step_order,
            'status': status_label,
            'at': timezone.now().isoformat(),
            'object': self._serialize_related_object()
        })
        data['snapshots'] = snapshots
        self._save_notes(data)

    def add_notification(self, message, recipients):
        data = self._load_notes()
        notifications = data.get('notifications', [])
        notifications.append({
            'message': message,
            'to': list(recipients) if recipients else [],
            'step': self.current_step,
            'at': timezone.now().isoformat()
        })
        data['notifications'] = notifications
        self._save_notes(data)
        
        # إنشاء تنبيهات حقيقية في قاعدة البيانات
        from apps.notifications.models import Notification
        for user_id in recipients:
            Notification.objects.create(
                recipient_id=user_id,
                title="تنبيه نظام الموافقات",
                message=message,
                link=f"/approvals/{self.id}/"
            )
            
    def sync_related_object_status(self):
        """مزامنة حالة الكائن المرتبط مع الخطوة الحالية"""
        obj = self.related_object
        if not obj or not hasattr(obj, 'status'):
            return
            
        if self.status == 'approved':
            obj.status = 'approved'
        elif self.status == 'rejected':
            obj.status = 'rejected'
        elif self.status == 'cancelled':
            obj.status = 'draft' # العودة للمسودة عند الإلغاء
        elif self.status == 'in_progress':
            # تعيين الحالة بناءً على الدور المطلوب في الخطوة الحالية
            role = self.get_current_step_info()
            status_map = {
                'coordinator': 'pending_coordinator',
                'region_manager': 'pending_region_manager',
                'operations_manager': 'pending_operations_manager',
                'admin_manager': 'pending_admin_manager',
                'super_admin': 'pending_admin_manager',
            }
            obj.status = status_map.get(role, obj.status)
            
        obj.save()
    
    def approve_current_step(self, user, comment=''):
        """الموافقة على الخطوة الحالية"""
        step = ApprovalStep.objects.get(approval_flow=self, step_order=self.current_step)
        if step.status == 'pending':
            step.assigned_to = user
            step.status = 'approved'
            step.action = 'approve'
            step.comment = comment
            step.acted_at = timezone.now()
            step.save()
            self.add_snapshot(step.step_order, 'approved')
        
        self.current_step += 1
        
        # تخطي الخطوات التى لا يوجد لها مستخدمون مؤهلون
        while self.current_step <= self.total_steps:
            pending = self.get_pending_users()
            if pending.exists():
                self.add_notification('تم ترحيل الطلب إلى المرحلة التالية', pending.values_list('id', flat=True))
                break
            auto_step = ApprovalStep.objects.get(approval_flow=self, step_order=self.current_step)
            if auto_step.status == 'pending':
                auto_step.assigned_to = None
                auto_step.status = 'approved'
                auto_step.action = 'approve'
                auto_step.comment = ''
                auto_step.acted_at = timezone.now()
                auto_step.save()
                self.add_snapshot(auto_step.step_order, 'auto_approved')
            self.current_step += 1
        
        if self.current_step > self.total_steps:
            self.status = 'approved'
            self.approved_by = user
            self.approved_at = timezone.now()
            self.add_notification('تم اعتماد الطلب نهائياً', [self.created_by.id])
        
        self.save()
        self.sync_related_object_status()
    
    def reject(self, user, reason=''):
        """رفض الموافقة"""
        step = ApprovalStep.objects.get(approval_flow=self, step_order=self.current_step)
        if step.status == 'pending':
            step.assigned_to = user
            step.status = 'rejected'
            step.action = 'reject'
            step.comment = reason
            step.acted_at = timezone.now()
            step.save()
            self.add_snapshot(step.step_order, 'rejected')
            self.add_notification('تم رفض الطلب', [self.created_by.id])
        self.status = 'rejected'
        self.rejection_reason = reason
        self.save()
        self.sync_related_object_status()
    
    def cancel(self, user, reason=''):
        """إلغاء الموافقة"""
        step = ApprovalStep.objects.get(approval_flow=self, step_order=self.current_step)
        if step.status == 'pending':
            step.assigned_to = user
            step.status = 'cancelled'
            step.action = 'cancel'
            step.comment = reason
            step.acted_at = timezone.now()
            step.save()
            self.add_snapshot(step.step_order, 'cancelled')
            self.add_notification('تم إلغاء الطلب', [self.created_by.id])
        self.status = 'cancelled'
        self.notes = reason
        self.save()
        self.sync_related_object_status()
    
    def get_current_step_info(self):
        """الحصول على معلومات الخطوة الحالية"""
        if self.current_step <= self.total_steps:
            return self.get_step_role(self.current_step)
        return None
    
    def get_step_role(self, step_number):
        """الحصول على الدور المطلوب للخطوة"""
        roles = [
            'region_manager',   # الخطوة 1: مدير المنطقة
            'coordinator',      # الخطوة 2: المنسق
            'operations_manager', # الخطوة 3: مدير العمليات
            'admin_manager',    # الخطوة 4: مدير الإدارة
        ]
        
        if step_number <= len(roles):
            return roles[step_number - 1]
        return 'super_admin'  # الخطوات الإضافية للمدير العام
    
    def get_pending_users(self):
        """الحصول على المستخدمين المطلوب منهم موافقة"""
        current_role = self.get_current_step_info()
        if not current_role:
            return User.objects.none()

        qs = User.objects.filter(
            profile__role=current_role,
            profile__status='active'
        )

        if current_role == 'region_manager':
            related = self.related_object
            region = None
            if related is not None:
                if hasattr(related, 'branch') and getattr(related, 'branch', None):
                    region = related.branch.region
                elif hasattr(related, 'employee') and getattr(related, 'employee', None):
                    emp_profile = getattr(related.employee, 'profile', None)
                    if emp_profile and getattr(emp_profile, 'region', ''):
                        region = emp_profile.region
            if region:
                qs = qs.filter(profile__region=region)

        return qs

    def advance_until_assignable(self):
        while self.current_step <= self.total_steps:
            pending = self.get_pending_users()
            if pending.exists():
                self.add_notification('تم ترحيل الطلب إلى المرحلة التالية', pending.values_list('id', flat=True))
                break
            step = ApprovalStep.objects.get(approval_flow=self, step_order=self.current_step)
            if step.status == 'pending':
                step.assigned_to = None
                step.status = 'approved'
                step.action = 'approve'
                step.comment = ''
                step.acted_at = timezone.now()
                step.save()
                self.add_snapshot(step.step_order, 'auto_approved')
            self.current_step += 1
        if self.current_step > self.total_steps:
            self.status = 'approved'
            self.approved_at = timezone.now()
            self.add_notification('تم اعتماد الطلب نهائياً', [self.created_by.id])
        self.save()
        self.sync_related_object_status()


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
            # للجداول: مدير المنطقة -> منسق -> مدير العمليات -> مدير الإدارة
            steps = [
                ('region_manager', 'مدير المنطقة'),
                ('coordinator', 'منسق'),
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