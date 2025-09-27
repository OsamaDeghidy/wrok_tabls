from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """إدارة المستخدمين المخصصة"""
    
    list_display = ('user', 'role', 'job_id', 'work_hours', 'position', 'branch', 'status', 'created_at')
    list_filter = ('role', 'branch', 'department', 'status', 'work_hours', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email', 'job_id', 'phone', 'position')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'job_id')
    
    fieldsets = (
        (_('المستخدم الأساسي'), {
            'fields': ('user',)
        }),
        (_('معلومات العمل'), {
            'fields': ('role', 'job_id', 'work_hours', 'work_days', 'position', 'department', 'branch', 'hire_date', 'salary', 'status')
        }),
        (_('معلومات الاتصال'), {
            'fields': ('phone', 'address', 'emergency_contact', 'emergency_phone')
        }),
        (_('معلومات إضافية'), {
            'fields': ('notes',)
        }),
        (_('تواريخ النظام'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """تصفية المستخدمين حسب الصلاحيات"""
        qs = super().get_queryset(request)
        
        # إذا كان المستخدم مدير فرع، يعرض فقط موظفي فرعه
        if request.user.is_authenticated:
            try:
                user_profile = UserProfile.objects.get(user=request.user)
                if user_profile.is_branch_manager and user_profile.branch:
                    qs = qs.filter(branch=user_profile.branch)
            except UserProfile.DoesNotExist:
                pass
        
        return qs
