from django import forms
from django.contrib.auth.models import User
from .models import Schedule, ScheduleEntry
from apps.branches.models import Branch, BranchShift


class ScheduleForm(forms.ModelForm):
    """نموذج الجدول التشغيلي"""
    
    class Meta:
        model = Schedule
        fields = [
            'branch', 'schedule_type', 'start_date', 'end_date', 'notes'
        ]
        widgets = {
            'branch': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'schedule_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'required': True
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'required': True
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'أي ملاحظات إضافية...'
            }),
        }
        labels = {
            'branch': 'الفرع',
            'schedule_type': 'نوع الجدول',
            'start_date': 'تاريخ البداية',
            'end_date': 'تاريخ النهاية',
            'notes': 'ملاحظات',
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and not user.is_superuser:
            from apps.users.models import UserProfile
            try:
                profile = user.profile
                if profile.role == 'branch_manager' and profile.branch:
                    self.fields['branch'].queryset = Branch.objects.filter(id=profile.branch.id)
                    self.fields['branch'].initial = profile.branch
                elif profile.role == 'region_manager' and profile.region:
                    self.fields['branch'].queryset = Branch.objects.filter(region=profile.region)
            except UserProfile.DoesNotExist:
                pass

        # جعل الحقول غير مطلوبة
        if 'notes' in self.fields:
            self.fields['notes'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date >= end_date:
                raise forms.ValidationError({
                    'end_date': 'تاريخ النهاية يجب أن يكون بعد تاريخ البداية'
                })
        
        return cleaned_data


class ScheduleEntryForm(forms.ModelForm):
    """نموذج إدخال الجدول التشغيلي"""
    
    class Meta:
        model = ScheduleEntry
        fields = [
            'employee', 'date', 'shift', 'start_time', 'end_time', 'is_cover', 'notes'
        ]
        widgets = {
            'employee': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'required': True
            }),
            'shift': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'start_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
                'required': True
            }),
            'end_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
                'required': True
            }),
            'is_cover': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'أي ملاحظات إضافية...'
            }),
        }
        labels = {
            'employee': 'الموظف',
            'date': 'التاريخ',
            'shift': 'الشفت',
            'start_time': 'ساعة البداية',
            'end_time': 'ساعة النهاية',
            'is_cover': 'تغطية',
            'notes': 'ملاحظات',
        }
    
    def __init__(self, *args, **kwargs):
        schedule = kwargs.pop('schedule', None)
        super().__init__(*args, **kwargs)
        
        # تحديد الموظفين المتاحين حسب الفرع
        if schedule and hasattr(schedule, 'branch'):
            self.fields['employee'].queryset = User.objects.filter(
                profile__branch=schedule.branch
            ).select_related('profile')
            
            # تحديد الشفتات المتاحة حسب الفرع
            self.fields['shift'].queryset = BranchShift.objects.filter(
                branch=schedule.branch,
                is_active=True
            )
        
        # جعل الحقول غير مطلوبة
        if 'notes' in self.fields:
            self.fields['notes'].required = False
        if 'is_cover' in self.fields:
            self.fields['is_cover'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        date = cleaned_data.get('date')
        employee = cleaned_data.get('employee')
        
        if start_time and end_time:
            pass # تم إزالة التحقق للسماح بالشفتات الليلية (start_time > end_time)
        
        # التحقق من الإجازات المتداخلة
        if employee and date:
            from apps.leaves.models import LeaveRequest
            overlapping_leaves = LeaveRequest.objects.filter(
                employee=employee,
                start_date__lte=date,
                end_date__gte=date,
                status='approved'
            )
            if overlapping_leaves.exists():
                raise forms.ValidationError({
                    'employee': 'الموظف في إجازة معتمدة في هذا التاريخ'
                })
        
        return cleaned_data


class ScheduleEditForm(forms.ModelForm):
    """نموذج تعديل الجدول التشغيلي مع التوزيعات"""
    
    class Meta:
        model = Schedule
        fields = [
            'branch', 'schedule_type', 'start_date', 'end_date', 'notes'
        ]
        widgets = {
            'branch': forms.Select(attrs={
                'class': 'form-select',
                'id': 'branch',
                'required': True
            }),
            'schedule_type': forms.Select(attrs={
                'class': 'form-select',
                'id': 'schedule_type',
                'required': True
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'id': 'start_date',
                'required': True
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'id': 'end_date',
                'required': True
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'id': 'notes',
                'rows': 3,
                'placeholder': 'أي ملاحظات إضافية...'
            }),
        }
        labels = {
            'branch': 'الفرع',
            'schedule_type': 'نوع الجدول',
            'start_date': 'تاريخ البداية',
            'end_date': 'تاريخ النهاية',
            'notes': 'ملاحظات',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # جعل الحقول غير مطلوبة
        if 'notes' in self.fields:
            self.fields['notes'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date >= end_date:
                raise forms.ValidationError({
                    'end_date': 'تاريخ النهاية يجب أن يكون بعد تاريخ البداية'
                })
        
        return cleaned_data


class ScheduleEntryEditForm(forms.ModelForm):
    """نموذج تعديل إدخال الجدول التشغيلي"""
    
    class Meta:
        model = ScheduleEntry
        fields = [
            'employee', 'date', 'shift', 'start_time', 'end_time', 'is_cover', 'notes'
        ]
        widgets = {
            'employee': forms.Select(attrs={
                'class': 'form-select form-select-sm entry-employee',
                'required': True
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control form-control-sm entry-date',
                'required': True
            }),
            'shift': forms.Select(attrs={
                'class': 'form-select form-select-sm entry-shift',
                'required': True
            }),
            'start_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control form-control-sm entry-start',
                'required': True
            }),
            'end_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control form-control-sm entry-end',
                'required': True
            }),
            'is_cover': forms.CheckboxInput(attrs={
                'class': 'form-check-input entry-cover'
            }),
            'notes': forms.TextInput(attrs={
                'class': 'form-control form-control-sm entry-notes',
                'placeholder': 'ملاحظات...'
            }),
        }
        labels = {
            'employee': 'الموظف',
            'date': 'التاريخ',
            'shift': 'الشفت',
            'start_time': 'من',
            'end_time': 'إلى',
            'is_cover': 'تغطية',
            'notes': 'ملاحظات',
        }
    
    def __init__(self, *args, **kwargs):
        schedule = kwargs.pop('schedule', None)
        super().__init__(*args, **kwargs)
        
        # تحديد الموظفين المتاحين حسب الفرع
        if schedule and hasattr(schedule, 'branch'):
            self.fields['employee'].queryset = User.objects.filter(
                profile__branch=schedule.branch
            ).select_related('profile')
            
            # تحديد الشفتات المتاحة حسب الفرع
            self.fields['shift'].queryset = BranchShift.objects.filter(
                branch=schedule.branch,
                is_active=True
            )
        
        # جعل الحقول غير مطلوبة
        if 'notes' in self.fields:
            self.fields['notes'].required = False
        if 'is_cover' in self.fields:
            self.fields['is_cover'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        date = cleaned_data.get('date')
        employee = cleaned_data.get('employee')
        
        if start_time and end_time:
            pass # تم إزالة التحقق للسماح بالشفتات الليلية (start_time > end_time)
        
        # التحقق من الإجازات المتداخلة
        if employee and date:
            from apps.leaves.models import LeaveRequest
            overlapping_leaves = LeaveRequest.objects.filter(
                employee=employee,
                start_date__lte=date,
                end_date__gte=date,
                status='approved'
            )
            if overlapping_leaves.exists():
                raise forms.ValidationError({
                    'employee': 'الموظف في إجازة معتمدة في هذا التاريخ'
                })
        
        return cleaned_data


class ScheduleFilterForm(forms.Form):
    """نموذج فلترة الجداول التشغيلية"""
    
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.all(),
        required=False,
        empty_label="جميع الفروع",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='الفرع'
    )
    
    status = forms.ChoiceField(
        choices=[('', 'جميع الحالات')] + Schedule.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='الحالة'
    )
    
    schedule_type = forms.ChoiceField(
        choices=[('', 'جميع الأنواع')] + Schedule.TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='نوع الجدول'
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='من تاريخ'
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='إلى تاريخ'
    )
