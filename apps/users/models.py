from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError


class UserProfile(models.Model):
    """نموذج ملف المستخدم المرتبط بـ Django User"""
    
    # Choices
    ROLE_CHOICES = [
        ('employee', 'موظف'),
        ('branch_manager', 'مدير معرض'),
        ('coordinator', 'منسق'),
        ('region_manager', 'مدير منطقة'),
        ('operations_manager', 'مدير عمليات'),
        ('admin_manager', 'مدير إدارة'),
        ('super_admin', 'مدير عام'),
    ]
    
    WORK_HOURS_CHOICES = [
        (8, '8 ساعات (6 أيام عمل)'),
        (9, '9 ساعات (5 أيام عمل)'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'نشط'),
        ('inactive', 'غير نشط'),
        ('suspended', 'معلق'),
        ('terminated', 'منتهي الخدمة'),
    ]
    
    DEPARTMENT_CHOICES = [
        ('hr', 'الموارد البشرية'),
        ('it', 'تقنية المعلومات'),
        ('finance', 'المالية'),
        ('operations', 'العمليات'),
        ('sales', 'المبيعات'),
        ('marketing', 'التسويق'),
    ]

    REGION_CHOICES = [
        ('north', 'المنطقة الشمالية'),
        ('south', 'المنطقة الجنوبية'),
        ('east', 'المنطقة الشرقية'),
        ('center', 'المنطقة الوسطى'),
        ('west', 'المنطقة الغربية'),
    ]
    
    # Fields
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        verbose_name='المستخدم',
        related_name='profile'
    )
    
    phone = models.CharField(
        max_length=20, 
        blank=True, 
        validators=[
            RegexValidator(
                regex=r'^(\+966|0)?[5-9][0-9]{8}$',
                message='رقم الهاتف غير صحيح. يجب أن يبدأ بـ +966 أو 0 ويحتوي على 9 أرقام'
            )
        ],
        verbose_name='رقم الهاتف'
    )
    
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='employee', 
        verbose_name='الدور'
    )
    
    job_id = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name='الرقم الوظيفي',
        help_text='سيتم إنشاؤه تلقائياً إذا لم يتم تحديده'
    )
    
    work_hours = models.PositiveIntegerField(
        choices=WORK_HOURS_CHOICES, 
        default=8, 
        verbose_name='عدد ساعات العمل'
    )
    
    work_days = models.PositiveIntegerField(
        default=6, 
        verbose_name='عدد أيام العمل'
    )
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='active', 
        verbose_name='الحالة'
    )
    
    branch = models.ForeignKey(
        'branches.Branch', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name='الفرع',
        related_name='employees'
    )
    
    position = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name='المنصب'
    )
    
    department = models.CharField(
        max_length=100, 
        choices=DEPARTMENT_CHOICES,
        blank=True, 
        verbose_name='القسم'
    )

    region = models.CharField(
        max_length=50,
        choices=REGION_CHOICES,
        blank=True,
        verbose_name='المنطقة'
    )
    
    hire_date = models.DateField(
        null=True, 
        blank=True, 
        verbose_name='تاريخ التعيين'
    )
    
    salary = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        verbose_name='الراتب'
    )
    
    address = models.TextField(
        blank=True, 
        verbose_name='العنوان'
    )
    
    emergency_contact = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name='جهة الاتصال في الطوارئ'
    )
    
    emergency_phone = models.CharField(
        max_length=20, 
        blank=True, 
        verbose_name='رقم الطوارئ'
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
        verbose_name = 'ملف المستخدم'
        verbose_name_plural = 'ملفات المستخدمين'
        ordering = ['user__first_name', 'user__last_name']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"
    
    def save(self, *args, **kwargs):
        # إنشاء الرقم الوظيفي تلقائياً إذا لم يتم تحديده
        if not self.job_id:
            # إذا كان رقم الموظف يبدأ بـ 98979 (عامل خارجي)
            if self.user.username.startswith('98979'):
                self.work_hours = 9  # العامل الخارجي يعمل 9 ساعات
                self.work_days = 5   # 5 أيام عمل
            else:
                # حساب عدد أيام العمل بناءً على ساعات العمل
                self.work_days = 6 if self.work_hours == 8 else 5
            
            # إنشاء الرقم الوظيفي
            last_profile = UserProfile.objects.order_by('-id').first()
            if last_profile and last_profile.job_id:
                try:
                    last_number = int(last_profile.job_id.split('-')[-1])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1001
            else:
                new_number = 1001
            
            self.job_id = f"EMP-{new_number:04d}"
        
        super().save(*args, **kwargs)
    
    # Properties للتحقق من الأدوار
    @property
    def is_employee(self):
        return self.role == 'employee'
    
    @property
    def is_branch_manager(self):
        return self.role == 'branch_manager'
    
    @property
    def is_coordinator(self):
        return self.role == 'coordinator'
    
    @property
    def is_region_manager(self):
        return self.role == 'region_manager'
    
    @property
    def is_operations_manager(self):
        return self.role == 'operations_manager'
    
    @property
    def is_admin_manager(self):
        return self.role == 'admin_manager'
    
    @property
    def is_super_admin(self):
        return self.role == 'super_admin'
    
    # Properties للصلاحيات
    @property
    def can_manage_branches(self):
        return self.role in ['super_admin', 'region_manager', 'operations_manager', 'admin_manager']
    
    @property
    def can_create_schedules(self):
        return self.role in ['super_admin', 'branch_manager', 'coordinator', 'region_manager', 'operations_manager', 'admin_manager']
    
    @property
    def can_approve_schedules(self):
        return self.role in ['super_admin', 'coordinator', 'region_manager', 'operations_manager', 'admin_manager']
    
    @property
    def can_manage_employees(self):
        return self.role in ['super_admin', 'branch_manager', 'coordinator', 'region_manager', 'operations_manager', 'admin_manager']
    
    @property
    def can_view_all_data(self):
        return self.role in ['super_admin', 'admin_manager', 'operations_manager']
    
    @property
    def can_approve_leaves(self):
        """التحقق من صلاحية الموافقة على الإجازات"""
        return self.role in ['super_admin', 'branch_manager', 'coordinator', 'region_manager', 'operations_manager', 'admin_manager']
    
    def get_managed_branches(self):
        """الحصول على الفروع التي يمكن للمستخدم إدارتها"""
        if self.is_super_admin or self.is_admin_manager or self.is_operations_manager:
            from apps.branches.models import Branch
            return Branch.objects.all()
        elif self.is_region_manager:
            from apps.branches.models import Branch
            # سيتم تفعيل هذا بعد إضافة حقل الفرع
            # return Branch.objects.filter(region=self.branch.region if self.branch else None)
            return Branch.objects.all()
        elif self.is_branch_manager:
            # سيتم تفعيل هذا بعد إضافة حقل الفرع
            # return [self.branch] if self.branch else []
            return []
        else:
            return []
    
    def clean(self):
        """التحقق من صحة البيانات"""
        super().clean()
        
        # التحقق من أن مدير المعرض يجب أن يكون مرتبط بفرع
        # سيتم تفعيل هذا التحقق بعد إضافة حقل الفرع
        # if self.role == 'branch_manager' and not self.branch:
        #     raise ValidationError({
        #         'branch': 'مدير المعرض يجب أن يكون مرتبط بفرع'
        #     })
        
        # التحقق من أن الموظف يجب أن يكون مرتبط بفرع
        # if self.role == 'employee' and not self.branch:
        #     raise ValidationError({
        #         'branch': 'الموظف يجب أن يكون مرتبط بفرع'
        #     })
        pass


# Signal لإنتاج UserProfile تلقائياً عند إنشاء User
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()