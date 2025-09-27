from django.contrib.auth.models import User
from django.db import models
from django.core.validators import RegexValidator


class UserProfile(models.Model):
    """نموذج الملف الشخصي للمستخدم - يوسع User الموجود في Django"""
    
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
    
    # ربط مع المستخدم الأساسي في Django
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='المستخدم')
    
    # معلومات الاتصال
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(
            regex=r'^(\+966|0)?[5-9][0-9]{8}$',
            message='رقم الهاتف غير صحيح. يجب أن يبدأ بـ +966 أو 0 ويحتوي على 9 أرقام'
        )],
        verbose_name='رقم الهاتف'
    )
    
    # معلومات العمل
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='employee',
        verbose_name='الدور'
    )
    
    job_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='الرقم الوظيفي'
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
    
    position = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='المنصب'
    )
    
    department = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='القسم'
    )
    
    # ربط مع الفرع
    branch = models.ForeignKey(
        'branches.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='الفرع'
    )
    
    # معلومات إضافية
    hire_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='تاريخ التعيين'
    )
    
    salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
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
    
    # تواريخ
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    
    class Meta:
        verbose_name = 'ملف المستخدم'
        verbose_name_plural = 'ملفات المستخدمين'
        ordering = ['user__first_name', 'user__last_name']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"
    
    def save(self, *args, **kwargs):
        """حفظ مع تحديث عدد أيام العمل"""
        # تحديث عدد أيام العمل حسب ساعات العمل
        if self.work_hours == 8:
            self.work_days = 6
        elif self.work_hours == 9:
            self.work_days = 5
        
        # إنشاء الرقم الوظيفي إذا لم يكن موجود
        if not self.job_id:
            self.job_id = self.generate_job_id()
        
        super().save(*args, **kwargs)
    
    def generate_job_id(self):
        """إنشاء رقم وظيفي فريد"""
        from django.utils import timezone
        year = timezone.now().year
        last_user = UserProfile.objects.filter(
            job_id__startswith=f"EMP{year}"
        ).order_by('-job_id').first()
        
        if last_user and last_user.job_id:
            try:
                last_number = int(last_user.job_id.split(year)[1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1
        
        return f"EMP{year}{new_number:04d}"
    
    # خصائص الأدوار
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
    
    # خصائص الصلاحيات
    @property
    def can_manage_branches(self):
        """هل يمكن إدارة الفروع"""
        return self.role in ['coordinator', 'region_manager', 'operations_manager', 'admin_manager', 'super_admin']
    
    @property
    def can_manage_employees(self):
        """هل يمكن إدارة الموظفين"""
        return self.role in ['branch_manager', 'coordinator', 'region_manager', 'operations_manager', 'admin_manager', 'super_admin']
    
    @property
    def can_create_schedules(self):
        """هل يمكن إنشاء الجداول"""
        return self.role in ['branch_manager', 'coordinator', 'region_manager', 'operations_manager', 'admin_manager', 'super_admin']
    
    @property
    def can_approve(self):
        """هل يمكن الموافقة"""
        return self.role in ['coordinator', 'region_manager', 'operations_manager', 'admin_manager', 'super_admin']
    
    @property
    def can_view_all_branches(self):
        """هل يمكن رؤية جميع الفروع"""
        return self.role in ['coordinator', 'region_manager', 'operations_manager', 'admin_manager', 'super_admin']
    
    @property
    def can_manage_own_branch_only(self):
        """هل يمكن إدارة فرعه فقط"""
        return self.role == 'branch_manager'
    
    @property
    def can_view_schedules(self):
        """هل يمكن رؤية الجداول"""
        return self.role in ['employee', 'branch_manager', 'coordinator', 'region_manager', 'operations_manager', 'admin_manager', 'super_admin']
    
    @property
    def can_request_leaves(self):
        """هل يمكن طلب الإجازات"""
        return self.role in ['employee', 'branch_manager', 'coordinator', 'region_manager', 'operations_manager', 'admin_manager', 'super_admin']
    
    @property
    def can_manage_violations(self):
        """هل يمكن إدارة المخالفات"""
        return self.role in ['branch_manager', 'coordinator', 'region_manager', 'operations_manager', 'admin_manager', 'super_admin']
    
    # خصائص العرض
    @property
    def full_name_arabic(self):
        """الاسم الكامل بالعربية"""
        return f"{self.user.first_name} {self.user.last_name}".strip()
    
    @property
    def work_hours_display(self):
        """عرض ساعات العمل"""
        return f"{self.work_hours} ساعات ({self.work_days} أيام عمل)"
    
    @property
    def branch_name(self):
        """اسم الفرع"""
        return self.branch.name if self.branch else "غير محدد"
    
    @property
    def is_working_today(self):
        """هل يعمل اليوم"""
        from django.utils import timezone
        today = timezone.now().date()
        return self.status == 'active' and (not self.hire_date or self.hire_date <= today)
    
    def get_managed_employees(self):
        """الحصول على الموظفين الذين يديرهم"""
        if self.is_branch_manager and self.branch:
            return UserProfile.objects.filter(
                branch=self.branch,
                role='employee',
                status='active'
            )
        return UserProfile.objects.none()
    
    def get_accessible_branches(self):
        """الحصول على الفروع التي يمكن الوصول إليها"""
        if self.can_view_all_branches:
            from apps.branches.models import Branch
            return Branch.objects.filter(is_active=True)
        elif self.branch:
            return [self.branch]
        return []