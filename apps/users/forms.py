from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile
from apps.branches.models import Branch


class UserRegistrationForm(UserCreationForm):
    """نموذج تسجيل المستخدمين الجدد"""
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
        label='البريد الإلكتروني',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        label='رقم الهاتف',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        required=True,
        label='الدور',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.all(),
        required=False,
        label='الفرع',
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="اختر الفرع"
    )
    region = forms.ChoiceField(
        choices=UserProfile.REGION_CHOICES,
        required=False,
        label='المنطقة',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'phone', 'role', 'branch')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'اسم المستخدم'
        self.fields['password1'].label = 'كلمة المرور'
        self.fields['password2'].label = 'تأكيد كلمة المرور'
        
        # إضافة classes للـ widgets
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        role_val = self.data.get('role') if hasattr(self, 'data') else None
        if role_val == 'region_manager':
            self.fields['region'].required = True
        else:
            self.fields['region'].required = False
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('هذا البريد الإلكتروني مستخدم بالفعل')
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # إنشاء أو تحديث ملف المستخدم
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.phone = self.cleaned_data.get('phone', '')
            profile.role = self.cleaned_data.get('role', 'employee')
            profile.branch = self.cleaned_data.get('branch')
            role = self.cleaned_data.get('role', 'employee')
            profile.region = self.cleaned_data.get('region') if role == 'region_manager' else ''
            profile.save()
        return user


class UserProfileForm(forms.ModelForm):
    """نموذج تعديل ملف المستخدم"""
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
        label='البريد الإلكتروني',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    is_active = forms.BooleanField(
        required=False,
        label='نشط',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    is_staff = forms.BooleanField(
        required=False,
        label='موظف إدارة',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'is_active', 'is_staff')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'اسم المستخدم'
        
        # إضافة حقول الملف الشخصي
        if self.instance and hasattr(self.instance, 'profile'):
            profile = self.instance.profile
            self.fields.update({
                'phone': forms.CharField(
                    max_length=20,
                    required=False,
                    label='رقم الهاتف',
                    initial=profile.phone,
                    widget=forms.TextInput(attrs={'class': 'form-control'})
                ),
                'role': forms.ChoiceField(
                    choices=UserProfile.ROLE_CHOICES,
                    required=True,
                    label='الدور',
                    initial=profile.role,
                    widget=forms.Select(attrs={'class': 'form-control'})
                ),
                'job_id': forms.CharField(
                    max_length=50,
                    required=False,
                    label='الرقم الوظيفي',
                    initial=profile.job_id,
                    widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': True})
                ),
                'is_laborer': forms.BooleanField(
                    required=False,
                    label='عمالة (لا تحتسب في عجز التغطية)',
                    initial=getattr(profile, 'is_laborer', False),
                    widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
                ),
                'work_hours': forms.ChoiceField(
                    choices=UserProfile.WORK_HOURS_CHOICES,
                    required=True,
                    label='نظام ساعات العمل',
                    initial=profile.work_hours,
                    widget=forms.Select(attrs={'class': 'form-control'})
                ),
                'status': forms.ChoiceField(
                    choices=UserProfile.STATUS_CHOICES,
                    required=True,
                    label='الحالة',
                    initial=profile.status,
                    widget=forms.Select(attrs={'class': 'form-control'})
                ),
                'position': forms.CharField(
                    max_length=100,
                    required=False,
                    label='المنصب',
                    initial=profile.position,
                    widget=forms.TextInput(attrs={'class': 'form-control'})
                ),
                'department': forms.CharField(
                    max_length=100,
                    required=False,
                    label='القسم',
                    initial=profile.department,
                    widget=forms.TextInput(attrs={'class': 'form-control'})
                ),
                'hire_date': forms.DateField(
                    required=False,
                    label='تاريخ التوظيف',
                    initial=profile.hire_date,
                    widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
                ),
                'salary': forms.DecimalField(
                    max_digits=10,
                    decimal_places=2,
                    required=False,
                    label='الراتب',
                    initial=profile.salary,
                    widget=forms.NumberInput(attrs={'class': 'form-control'})
                ),
                'address': forms.CharField(
                    required=False,
                    label='العنوان',
                    initial=profile.address,
                    widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
                ),
                'emergency_contact': forms.CharField(
                    max_length=100,
                    required=False,
                    label='جهة اتصال للطوارئ',
                    initial=profile.emergency_contact,
                    widget=forms.TextInput(attrs={'class': 'form-control'})
                ),
                'emergency_phone': forms.CharField(
                    max_length=20,
                    required=False,
                    label='رقم هاتف الطوارئ',
                    initial=profile.emergency_phone,
                    widget=forms.TextInput(attrs={'class': 'form-control'})
                ),
                'notes': forms.CharField(
                    required=False,
                    label='ملاحظات',
                    initial=profile.notes,
                    widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
                ),
                'branch': forms.ModelChoiceField(
                    queryset=Branch.objects.all(),
                    required=False,
                    label='الفرع',
                    initial=profile.branch,
                    widget=forms.Select(attrs={'class': 'form-control'}),
                    empty_label="اختر الفرع"
                ),
                'region': forms.ChoiceField(
                    choices=UserProfile.REGION_CHOICES,
                    required=(profile.role == 'region_manager'),
                    label='المنطقة',
                    initial=profile.region,
                    widget=forms.Select(attrs={'class': 'form-control'})
                ),
            })
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        # حفظ بيانات المستخدم
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            
            # حفظ بيانات الملف الشخصي
            if hasattr(user, 'profile'):
                profile = user.profile
                profile.phone = self.cleaned_data.get('phone', '')
                profile.role = self.cleaned_data.get('role', 'employee')
                profile.is_laborer = self.cleaned_data.get('is_laborer', False)
                profile.work_hours = self.cleaned_data.get('work_hours', 8)
                profile.status = self.cleaned_data.get('status', 'active')
                profile.position = self.cleaned_data.get('position', '')
                profile.department = self.cleaned_data.get('department', '')
                profile.hire_date = self.cleaned_data.get('hire_date')
                profile.salary = self.cleaned_data.get('salary')
                profile.address = self.cleaned_data.get('address', '')
                profile.emergency_contact = self.cleaned_data.get('emergency_contact', '')
                profile.emergency_phone = self.cleaned_data.get('emergency_phone', '')
                profile.notes = self.cleaned_data.get('notes', '')
                profile.branch = self.cleaned_data.get('branch')
                role = self.cleaned_data.get('role', profile.role)
                profile.save()
        
        return user


class ProfileEditForm(forms.ModelForm):
    """نموذج تعديل الملف الشخصي للمستخدم الحالي"""
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
        label='البريد الإلكتروني',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = UserProfile
        fields = ('phone', 'position', 'department', 'address', 'emergency_contact', 'emergency_phone', 'notes')
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        
        if commit:
            profile.save()
            
            # تحديث بيانات المستخدم
            user = profile.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.save()
        
        return profile


class PasswordChangeForm(forms.Form):
    """نموذج تغيير كلمة المرور"""
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='كلمة المرور الحالية'
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='كلمة المرور الجديدة'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='تأكيد كلمة المرور الجديدة'
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise forms.ValidationError('كلمة المرور الحالية غير صحيحة')
        return current_password
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password:
            if new_password != confirm_password:
                raise forms.ValidationError('كلمة المرور الجديدة وتأكيدها غير متطابقين')
        
        return cleaned_data
    
    def save(self):
        password = self.cleaned_data['new_password']
        self.user.set_password(password)
        self.user.save()
