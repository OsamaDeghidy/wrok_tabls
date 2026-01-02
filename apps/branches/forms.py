from django import forms
from django.contrib.auth.models import User
from .models import Branch, BranchShift


class BranchForm(forms.ModelForm):
    """نموذج إنشاء وتعديل الفرع"""
    
    class Meta:
        model = Branch
        fields = [
            'name', 'code', 'type', 'category', 'status', 'address', 'city', 'region', 
            'postal_code', 'phone', 'email', 'manager', 'capacity', 
            'opening_date', 'working_days', 'description', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'region': forms.Select(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'manager': forms.Select(attrs={'class': 'form-control'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control'}),
            'opening_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # تخصيص choices للمديرين
        self.fields['manager'].queryset = User.objects.filter(
            profile__role__in=['branch_manager', 'coordinator', 'region_manager', 'operations_manager', 'admin_manager', 'super_admin']
        )
        self.fields['manager'].empty_label = "اختر مدير الفرع"
        
        # إضافة labels
        self.fields['name'].label = 'اسم الفرع'
        self.fields['code'].label = 'كود الفرع'
        self.fields['type'].label = 'نوع الفرع'
        self.fields['category'].label = 'فئة الفرع'
        self.fields['status'].label = 'الحالة'
        self.fields['address'].label = 'العنوان'
        self.fields['city'].label = 'المدينة'
        self.fields['region'].label = 'المنطقة'
        self.fields['postal_code'].label = 'الرمز البريدي'
        self.fields['phone'].label = 'رقم الهاتف'
        self.fields['email'].label = 'البريد الإلكتروني'
        self.fields['manager'].label = 'مدير الفرع'
        self.fields['capacity'].label = 'السعة الاستيعابية للموظفين'
        self.fields['opening_date'].label = 'تاريخ الافتتاح'
        self.fields['working_days'].label = 'أيام العمل'
        self.fields['description'].label = 'وصف الفرع'
        self.fields['notes'].label = 'ملاحظات'
    
    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code:
            # التحقق من عدم تكرار الكود
            queryset = Branch.objects.filter(code=code)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise forms.ValidationError('هذا الكود مستخدم بالفعل')
        return code
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # التحقق من عدم تكرار البريد الإلكتروني
            queryset = Branch.objects.filter(email=email)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise forms.ValidationError('هذا البريد الإلكتروني مستخدم بالفعل')
        return email


class BranchShiftForm(forms.ModelForm):
    """نموذج إنشاء وتعديل شفت الفرع"""
    
    class Meta:
        model = BranchShift
        fields = ['name', 'start_time', 'end_time', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # إضافة labels
        self.fields['name'].label = 'اسم الشفت'
        self.fields['start_time'].label = 'وقت البداية'
        self.fields['end_time'].label = 'وقت النهاية'
        self.fields['is_active'].label = 'نشط'
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        break_start = cleaned_data.get('break_start')
        break_end = cleaned_data.get('break_end')
        
        # التحقق من صحة الأوقات
        if start_time and end_time:
            if start_time >= end_time:
                raise forms.ValidationError('وقت البداية يجب أن يكون قبل وقت النهاية')
        
        if break_start and break_end:
            if break_start >= break_end:
                raise forms.ValidationError('بداية الاستراحة يجب أن تكون قبل نهاية الاستراحة')
            
            # التحقق من أن الاستراحة ضمن أوقات العمل
            if start_time and end_time:
                if break_start < start_time or break_end > end_time:
                    raise forms.ValidationError('أوقات الاستراحة يجب أن تكون ضمن أوقات العمل')
        
        return cleaned_data
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            # التحقق من عدم تكرار اسم الشفت في نفس الفرع
            branch = getattr(self, 'branch', None)
            if branch:
                queryset = BranchShift.objects.filter(branch=branch, name=name)
                if self.instance.pk:
                    queryset = queryset.exclude(pk=self.instance.pk)
                if queryset.exists():
                    raise forms.ValidationError('اسم الشفت مستخدم بالفعل في هذا الفرع')
        return name


class BranchFilterForm(forms.Form):
    """نموذج فلترة الفروع"""
    search = forms.CharField(
        required=False,
        label='البحث',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'ابحث في الفروع...'
        })
    )
    type = forms.ChoiceField(
        choices=[('', 'جميع الأنواع')] + list(Branch.TYPE_CHOICES),
        required=False,
        label='نوع الفرع',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        choices=[('', 'جميع الحالات')] + list(Branch.STATUS_CHOICES),
        required=False,
        label='الحالة',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    region = forms.ChoiceField(
        choices=[('', 'جميع المناطق')] + list(Branch.REGION_CHOICES),
        required=False,
        label='المنطقة',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['search'].widget.attrs.update({'class': 'form-control'})
        self.fields['type'].widget.attrs.update({'class': 'form-control'})
        self.fields['status'].widget.attrs.update({'class': 'form-control'})
        self.fields['region'].widget.attrs.update({'class': 'form-control'})


class BranchShiftFilterForm(forms.Form):
    """نموذج فلترة شفتات الفرع"""
    search = forms.CharField(
        required=False,
        label='البحث',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'ابحث في الشفتات...'
        })
    )
    is_active = forms.ChoiceField(
        choices=[('', 'جميع الشفتات'), ('true', 'نشط'), ('false', 'غير نشط')],
        required=False,
        label='الحالة',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['search'].widget.attrs.update({'class': 'form-control'})
        self.fields['is_active'].widget.attrs.update({'class': 'form-control'})


class BranchImportForm(forms.Form):
    """نموذج استيراد المعارض من Excel"""
    
    file = forms.FileField(
        label='ملف Excel',
        help_text='يرجى رفع ملف Excel يحتوي على بيانات المعارض',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls'})
    )
    
    update_existing = forms.BooleanField(
        label='تحديث المعارض الموجودة',
        required=False,
        help_text='إذا تم تحديد هذا الخيار، سيتم تحديث بيانات المعارض الموجودة',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
