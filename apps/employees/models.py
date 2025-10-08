from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Employee(models.Model):
    """نموذج الموظف - مرتبط بـ UserProfile"""
    
    EMPLOYMENT_TYPE_CHOICES = [
        ('full_time', 'دوام كامل'),
        ('part_time', 'دوام جزئي'),
        ('contract', 'عقد'),
        ('temporary', 'مؤقت'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'نشط'),
        ('inactive', 'غير نشط'),
        ('suspended', 'معلق'),
        ('terminated', 'منتهي الخدمة'),
    ]
    
    # العلاقة مع User
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        verbose_name='المستخدم',
        related_name='employee_profile'
    )
    
    # المعلومات الأساسية
    employee_number = models.CharField(
        max_length=50, 
        unique=True,
        blank=True,
        null=False,
        verbose_name='الرقم الوظيفي',
        help_text='سيتم إنشاؤه تلقائياً إذا لم يتم تحديده'
    )
    
    job_title = models.CharField(
        max_length=100, 
        verbose_name='المسمى الوظيفي'
    )
    
    employment_type = models.CharField(
        max_length=20, 
        choices=EMPLOYMENT_TYPE_CHOICES, 
        default='full_time',
        verbose_name='نوع التوظيف'
    )
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='active',
        verbose_name='الحالة'
    )
    
    # معلومات التوظيف
    hire_date = models.DateField(
        verbose_name='تاريخ التعيين'
    )
    
    termination_date = models.DateField(
        null=True, 
        blank=True,
        verbose_name='تاريخ إنهاء الخدمة'
    )
    
    # معلومات العمل
    work_location = models.CharField(
        max_length=200, 
        blank=True,
        verbose_name='مكان العمل'
    )
    
    direct_manager = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='managed_employees',
        verbose_name='المدير المباشر'
    )
    
    # معلومات إضافية
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
        verbose_name = 'الموظف'
        verbose_name_plural = 'الموظفين'
        ordering = ['user__first_name', 'user__last_name']
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_number})"
    
    def save(self, *args, **kwargs):
        # إنشاء الرقم الوظيفي تلقائياً إذا لم يتم تحديده
        if not self.employee_number:
            last_employee = Employee.objects.order_by('-id').first()
            if last_employee and last_employee.employee_number:
                try:
                    last_number = int(last_employee.employee_number.split('-')[-1])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1001
            else:
                new_number = 1001
            
            self.employee_number = f"EMP-{new_number:04d}"
        
        super().save(*args, **kwargs)
    
    def get_work_hours(self):
        """الحصول على ساعات العمل من UserProfile"""
        if hasattr(self.user, 'profile'):
            return self.user.profile.work_hours
        return 8  # افتراضي
    
    def get_branch(self):
        """الحصول على الفرع من UserProfile"""
        if hasattr(self.user, 'profile'):
            return self.user.profile.branch
        return None
    
    def get_role(self):
        """الحصول على الدور من UserProfile"""
        if hasattr(self.user, 'profile'):
            return self.user.profile.get_role_display()
        return 'غير محدد'
    
    def clean(self):
        """التحقق من صحة البيانات"""
        super().clean()
        
        # التحقق من أن تاريخ إنهاء الخدمة بعد تاريخ التعيين
        if self.termination_date and self.hire_date:
            if self.termination_date <= self.hire_date:
                raise ValidationError({
                    'termination_date': 'تاريخ إنهاء الخدمة يجب أن يكون بعد تاريخ التعيين'
                })


class EmployeeDocument(models.Model):
    """نموذج وثائق الموظف"""
    
    DOCUMENT_TYPE_CHOICES = [
        ('contract', 'عقد العمل'),
        ('id_copy', 'صورة الهوية'),
        ('certificate', 'شهادة'),
        ('cv', 'السيرة الذاتية'),
        ('other', 'أخرى'),
    ]
    
    employee = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE, 
        related_name='documents',
        verbose_name='الموظف'
    )
    
    document_type = models.CharField(
        max_length=20, 
        choices=DOCUMENT_TYPE_CHOICES,
        verbose_name='نوع الوثيقة'
    )
    
    title = models.CharField(
        max_length=200, 
        verbose_name='عنوان الوثيقة'
    )
    
    file = models.FileField(
        upload_to='employee_documents/%Y/%m/',
        verbose_name='الملف'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='الوصف'
    )
    
    uploaded_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='تاريخ الرفع'
    )
    
    class Meta:
        verbose_name = 'وثيقة الموظف'
        verbose_name_plural = 'وثائق الموظفين'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.employee.user.get_full_name()} - {self.title}"


class EmployeeEmergencyContact(models.Model):
    """نموذج جهات الاتصال في الطوارئ"""
    
    RELATIONSHIP_CHOICES = [
        ('spouse', 'الزوج/الزوجة'),
        ('parent', 'الوالد/الوالدة'),
        ('sibling', 'الأخ/الأخت'),
        ('child', 'الابن/الابنة'),
        ('friend', 'صديق'),
        ('other', 'أخرى'),
    ]
    
    employee = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE, 
        related_name='emergency_contacts',
        verbose_name='الموظف'
    )
    
    name = models.CharField(
        max_length=100, 
        verbose_name='الاسم'
    )
    
    relationship = models.CharField(
        max_length=20, 
        choices=RELATIONSHIP_CHOICES,
        verbose_name='العلاقة'
    )
    
    phone = models.CharField(
        max_length=20, 
        verbose_name='رقم الهاتف'
    )
    
    email = models.EmailField(
        blank=True,
        verbose_name='البريد الإلكتروني'
    )
    
    address = models.TextField(
        blank=True,
        verbose_name='العنوان'
    )
    
    is_primary = models.BooleanField(
        default=False,
        verbose_name='جهة اتصال أساسية'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='تاريخ الإنشاء'
    )
    
    class Meta:
        verbose_name = 'جهة الاتصال في الطوارئ'
        verbose_name_plural = 'جهات الاتصال في الطوارئ'
        ordering = ['-is_primary', 'name']
    
    def __str__(self):
        return f"{self.employee.user.get_full_name()} - {self.name}"
    
    def clean(self):
        """التحقق من صحة البيانات"""
        super().clean()
        
        # التحقق من وجود جهة اتصال أساسية واحدة فقط لكل موظف
        if self.is_primary:
            existing_primary = EmployeeEmergencyContact.objects.filter(
                employee=self.employee, 
                is_primary=True
            ).exclude(pk=self.pk)
            
            if existing_primary.exists():
                raise ValidationError({
                    'is_primary': 'يمكن أن يكون هناك جهة اتصال أساسية واحدة فقط لكل موظف'
                })