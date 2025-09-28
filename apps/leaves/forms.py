from django import forms
from django.contrib.auth.models import User
from .models import LeaveRequest, LeaveBalance


class LeaveRequestForm(forms.ModelForm):
    """نموذج طلب الإجازة"""
    
    class Meta:
        model = LeaveRequest
        fields = [
            'leave_type', 'start_date', 'end_date', 'reason', 
            'emergency_contact', 'notes'
        ]
        widgets = {
            'leave_type': forms.Select(attrs={
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
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'required': True,
                'placeholder': 'أدخل سبب الإجازة...'
            }),
            'emergency_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الطوارئ (اختياري)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'ملاحظات إضافية (اختياري)'
            }),
        }
        labels = {
            'leave_type': 'نوع الإجازة',
            'start_date': 'تاريخ البداية',
            'end_date': 'تاريخ النهاية',
            'reason': 'سبب الإجازة',
            'emergency_contact': 'رقم الطوارئ',
            'attachments': 'المرفقات',
            'notes': 'ملاحظات إضافية',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # جعل الحقول غير مطلوبة
        if 'emergency_contact' in self.fields:
            self.fields['emergency_contact'].required = False
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
            
            # التحقق من أن التاريخ في المستقبل
            from django.utils import timezone
            if start_date < timezone.now().date():
                raise forms.ValidationError({
                    'start_date': 'لا يمكن طلب إجازة في الماضي'
                })
        
        return cleaned_data


class LeaveBalanceForm(forms.ModelForm):
    """نموذج رصيد الإجازات"""
    
    class Meta:
        model = LeaveBalance
        fields = ['leave_type', 'total_days', 'year']
        widgets = {
            'leave_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'total_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 2020,
                'max': 2050
            }),
        }
        labels = {
            'leave_type': 'نوع الإجازة',
            'total_days': 'إجمالي الأيام',
            'year': 'السنة',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # تعيين السنة الحالية كقيمة افتراضية
        from datetime import datetime
        if not self.instance.pk:
            self.fields['year'].initial = datetime.now().year


class LeaveApprovalForm(forms.Form):
    """نموذج الموافقة/الرفض على طلب الإجازة"""
    
    STATUS_CHOICES = [
        ('approved', 'موافقة'),
        ('rejected', 'رفض'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='القرار'
    )
    
    manager_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'ملاحظات المدير (اختياري)'
        }),
        required=False,
        label='ملاحظات المدير'
    )
