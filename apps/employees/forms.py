from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Employee, EmployeeDocument, EmployeeEmergencyContact
from apps.users.models import UserProfile
from apps.branches.models import Branch


class EmployeeForm(forms.ModelForm):
    """نموذج إضافة/تعديل الموظف - متوافق مع UserProfile"""
    
    # حقل الرقم الوظيفي
    employee_number = forms.CharField(
        max_length=50,
        required=False,
        label='الرقم الوظيفي',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'EMP-xxxx أو اتركه فارغاً'}),
        help_text='سيتم إنشاؤه تلقائياً إذا تركته فارغاً'
    )
    
    # حقول User
    username = forms.CharField(
        max_length=150,
        label='اسم المستخدم',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='مطلوب. 150 رمزاً أو أقل، مكونة من حروف وأرقام و @/./+/-/_ فقط'
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        label='الاسم الأول',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        label='الاسم الأخير',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        required=True,
        label='عنوان بريد إلكتروني',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    # حقول UserProfile
    phone = forms.CharField(
        max_length=20,
        required=False,
        label='رقم الهاتف',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+966501234567'})
    )
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        label='الدور',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.all(),
        required=False,
        label='الفرع',
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="---------"
    )
    region = forms.ChoiceField(
        choices=[('', '---------')] + UserProfile.REGION_CHOICES,
        required=False,
        label='المنطقة',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    work_hours = forms.ChoiceField(
        choices=UserProfile.WORK_HOURS_CHOICES,
        label='عدد ساعات العمل',
        initial=8,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    position = forms.CharField(
        max_length=100,
        required=False,
        label='المنصب',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    department = forms.ChoiceField(
        choices=[('', '---------')] + UserProfile.DEPARTMENT_CHOICES,
        required=False,
        label='القسم',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    hire_date = forms.DateField(
        required=False,
        label='تاريخ التعيين',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        input_formats=['%Y-%m-%d']
    )
    salary = forms.DecimalField(
        required=False,
        label='الراتب',
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    address = forms.CharField(
        required=False,
        label='العنوان',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    emergency_contact = forms.CharField(
        required=False,
        label='جهة الاتصال في الطوارئ',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    emergency_phone = forms.CharField(
        required=False,
        label='رقم الطوارئ',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    notes = forms.CharField(
        required=False,
        label='ملاحظات',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    profile_status = forms.ChoiceField(
        choices=UserProfile.STATUS_CHOICES,
        label='الحالة',
        initial='active',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # كلمة المرور (للإنشاء فقط)
    password1 = forms.CharField(
        required=False,
        label='كلمة المرور',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='اتركه فارغاً إذا كنت لا تريد تغيير كلمة المرور'
    )
    password2 = forms.CharField(
        required=False,
        label='تأكيد كلمة المرور',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Employee
        fields = ['job_title', 'employment_type', 'status', 'work_location', 'direct_manager']
        widgets = {
            'job_title': forms.TextInput(attrs={'class': 'form-control'}),
            'employment_type': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'work_location': forms.TextInput(attrs={'class': 'form-control'}),
            'direct_manager': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # تحديث queryset للمدير المباشر
        self.fields['direct_manager'].queryset = User.objects.filter(
            profile__role__in=['branch_manager', 'coordinator', 'region_manager', 'operations_manager', 'admin_manager', 'super_admin']
        )
        self.fields['direct_manager'].required = False
        
        # إذا كان التعديل، املأ الحقول
        if self.instance and self.instance.pk and hasattr(self.instance, 'user'):
            # املأ الرقم الوظيفي
            self.fields['employee_number'].initial = self.instance.employee_number
            
            user = self.instance.user
            self.fields['username'].initial = user.username
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
            
            if hasattr(user, 'profile'):
                profile = user.profile
                self.fields['phone'].initial = profile.phone
                self.fields['role'].initial = profile.role
                self.fields['branch'].initial = profile.branch
                self.fields['region'].initial = profile.region
                self.fields['work_hours'].initial = profile.work_hours
                self.fields['position'].initial = profile.position
                self.fields['department'].initial = profile.department
                self.fields['hire_date'].initial = profile.hire_date
                self.fields['salary'].initial = profile.salary
                self.fields['address'].initial = profile.address
                self.fields['emergency_contact'].initial = profile.emergency_contact
                self.fields['emergency_phone'].initial = profile.emergency_phone
                self.fields['notes'].initial = profile.notes
                self.fields['profile_status'].initial = profile.status
    
    def clean_username(self):
        username = self.cleaned_data['username']
        if self.instance and self.instance.pk:
            # إذا كان التعديل، تجاهل المستخدم الحالي
            if User.objects.filter(username=username).exclude(pk=self.instance.user.pk).exists():
                raise forms.ValidationError('اسم المستخدم مستخدم بالفعل')
        else:
            # إذا كان إنشاء جديد
            if User.objects.filter(username=username).exists():
                raise forms.ValidationError('اسم المستخدم مستخدم بالفعل')
        return username
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if self.instance and self.instance.pk:
            # إذا كان التعديل، تجاهل المستخدم الحالي
            if User.objects.filter(email=email).exclude(pk=self.instance.user.pk).exists():
                raise forms.ValidationError('البريد الإلكتروني مستخدم بالفعل')
        else:
            # إذا كان إنشاء جديد
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError('البريد الإلكتروني مستخدم بالفعل')
        return email
    
    def clean_employee_number(self):
        employee_number = self.cleaned_data.get('employee_number', '').strip()
        
        # إذا تم إدخال رقم وظيفي، تحقق من أنه فريد
        if employee_number:
            if self.instance and self.instance.pk:
                # عند التعديل، تجاهل الموظف الحالي
                if Employee.objects.filter(employee_number=employee_number).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError('الرقم الوظيفي مستخدم بالفعل')
            else:
                # عند الإنشاء
                if Employee.objects.filter(employee_number=employee_number).exists():
                    raise forms.ValidationError('الرقم الوظيفي مستخدم بالفعل')
        
        return employee_number
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('كلمات المرور غير متطابقة')
        
        return password2
    
    def save(self, commit=True):
        employee = super().save(commit=False)
        
        if not self.instance.pk:  # إنشاء جديد
            # إنشاء User جديد
            password = self.cleaned_data.get('password1', 'password123')
            user = User.objects.create_user(
                username=self.cleaned_data['username'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                email=self.cleaned_data['email'],
                password=password,
                is_staff=True,
                is_active=True  # ضمان تفعيل الحساب
            )
            
            # الـ signal سينشئ UserProfile تلقائياً، فقط نحدثه
            # استخدام get_or_create للتأكد من وجود Profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.phone = self.cleaned_data.get('phone', '')
            profile.role = self.cleaned_data['role']
            profile.branch = self.cleaned_data.get('branch')
            profile.work_hours = int(self.cleaned_data.get('work_hours', 8))
            profile.work_days = 6 if profile.work_hours == 8 else 5
            profile.position = self.cleaned_data.get('position', '')
            profile.department = self.cleaned_data.get('department', '')
            profile.hire_date = self.cleaned_data.get('hire_date')
            profile.salary = self.cleaned_data.get('salary')
            profile.address = self.cleaned_data.get('address', '')
            profile.emergency_contact = self.cleaned_data.get('emergency_contact', '')
            profile.emergency_phone = self.cleaned_data.get('emergency_phone', '')
            profile.notes = self.cleaned_data.get('notes', '')
            profile.status = self.cleaned_data.get('profile_status', 'active')
            profile.region = self.cleaned_data.get('region', '')
            profile.save()
            
            employee.user = user
            employee.job_title = self.cleaned_data.get('position', 'موظف')
            employee.hire_date = self.cleaned_data.get('hire_date')
            
            # استخدام الرقم الوظيفي المدخل أو تركه فارغاً ليُنشأ تلقائياً
            custom_employee_number = self.cleaned_data.get('employee_number', '').strip()
            if custom_employee_number:
                employee.employee_number = custom_employee_number
            
        else:  # تعديل
            # تحديث بيانات User
            user = employee.user
            user.username = self.cleaned_data['username']
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            
            # تحديث كلمة المرور إذا تم إدخالها
            password1 = self.cleaned_data.get('password1')
            if password1:
                user.set_password(password1)
            
            user.save()
            
            # تحديث UserProfile
            profile = user.profile
            profile.phone = self.cleaned_data.get('phone', '')
            profile.role = self.cleaned_data['role']
            profile.branch = self.cleaned_data.get('branch')
            profile.region = self.cleaned_data.get('region', '')
            profile.work_hours = int(self.cleaned_data.get('work_hours', 8))
            profile.work_days = 6 if profile.work_hours == 8 else 5
            profile.position = self.cleaned_data.get('position', '')
            profile.department = self.cleaned_data.get('department', '')
            profile.hire_date = self.cleaned_data.get('hire_date')
            profile.salary = self.cleaned_data.get('salary')
            profile.address = self.cleaned_data.get('address', '')
            profile.emergency_contact = self.cleaned_data.get('emergency_contact', '')
            profile.emergency_phone = self.cleaned_data.get('emergency_phone', '')
            profile.notes = self.cleaned_data.get('notes', '')
            profile.status = self.cleaned_data.get('profile_status', 'active')
            profile.save()
            
            employee.job_title = self.cleaned_data.get('position', employee.job_title)
        
        if commit:
            employee.save()
        
        return employee


class EmployeeDocumentForm(forms.ModelForm):
    """نموذج إضافة وثيقة للموظف"""
    
    class Meta:
        model = EmployeeDocument
        fields = ['document_type', 'title', 'file', 'description']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class EmployeeEmergencyContactForm(forms.ModelForm):
    """نموذج إضافة جهة اتصال في الطوارئ"""
    
    class Meta:
        model = EmployeeEmergencyContact
        fields = ['name', 'relationship', 'phone', 'email', 'address', 'is_primary']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'relationship': forms.Select(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class EmployeeImportForm(forms.Form):
    """نموذج استيراد الموظفين من Excel"""
    
    file = forms.FileField(
        label='ملف Excel',
        help_text='يرجى رفع ملف Excel يحتوي على بيانات الموظفين',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls'})
    )
    
    update_existing = forms.BooleanField(
        label='تحديث الموظفين الموجودين',
        required=False,
        help_text='إذا تم تحديد هذا الخيار، سيتم تحديث بيانات الموظفين الموجودين',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class EmployeeSearchForm(forms.Form):
    """نموذج البحث والفلترة"""
    
    search = forms.CharField(
        max_length=100,
        required=False,
        label='البحث',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم الموظف أو الرقم الوظيفي'})
    )
    
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.all(),
        required=False,
        label='الفرع',
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="جميع الفروع"
    )
    
    status = forms.ChoiceField(
        choices=[('', 'جميع الحالات')] + Employee.STATUS_CHOICES,
        required=False,
        label='الحالة',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    employment_type = forms.ChoiceField(
        choices=[('', 'جميع أنواع التوظيف')] + Employee.EMPLOYMENT_TYPE_CHOICES,
        required=False,
        label='نوع التوظيف',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    role = forms.ChoiceField(
        choices=[('', 'جميع الأدوار')] + UserProfile.ROLE_CHOICES,
        required=False,
        label='الدور',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
