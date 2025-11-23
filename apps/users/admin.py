from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'ملف المستخدم'
    fk_name = 'user'
    
    fieldsets = (
        ('المعلومات الوظيفية', {
            'fields': ('role', 'branch', 'region', 'job_id', 'work_hours', 'work_days', 'status')
        }),
        ('المعلومات الشخصية', {
            'fields': ('phone', 'position', 'department', 'hire_date', 'salary')
        }),
        ('معلومات إضافية', {
            'fields': ('address', 'emergency_contact', 'emergency_phone', 'notes'),
            'classes': ('collapse',)
        }),
    )


class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'get_branch', 'get_status', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined', 'profile__role', 'profile__branch', 'profile__region', 'profile__status')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'profile__job_id')
    
    def get_role(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.get_role_display()
        return '-'
    get_role.short_description = 'الدور'
    
    def get_branch(self, obj):
        if hasattr(obj, 'profile') and obj.profile.branch:
            return obj.profile.branch.name
        return '-'
    get_branch.short_description = 'الفرع'
    
    def get_status(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.get_status_display()
        return '-'
    get_status.short_description = 'الحالة'
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_full_name', 'role', 'branch', 'region', 'status', 'job_id', 'work_hours', 'created_at')
    list_filter = ('role', 'branch', 'region', 'status', 'work_hours', 'work_days', 'department', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'job_id', 'phone')
    readonly_fields = ('job_id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('المستخدم', {
            'fields': ('user',)
        }),
        ('المعلومات الوظيفية', {
            'fields': ('role', 'branch', 'region', 'job_id', 'work_hours', 'work_days', 'status', 'position', 'department', 'hire_date', 'salary')
        }),
        ('المعلومات الشخصية', {
            'fields': ('phone', 'address', 'emergency_contact', 'emergency_phone')
        }),
        ('ملاحظات', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('معلومات النظام', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_full_name.short_description = 'الاسم الكامل'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        
        # إذا كان مدير معرض، عرض موظفي فرعه فقط
        if hasattr(request.user, 'profile') and request.user.profile.role == 'branch_manager':
            if request.user.profile.branch:
                return qs.filter(branch=request.user.profile.branch)
            return qs.filter(user=request.user)
        
        return qs

    def has_view_permission(self, request, obj=None):
        """التحقق من صلاحية عرض البيانات"""
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'profile'):
            # المدير العام، المنسق، ومدير المنطقة يمكنهم عرض البيانات
            return request.user.profile.role in ['super_admin', 'coordinator', 'region_manager']
        return False

    def has_add_permission(self, request):
        """التحقق من صلاحية إضافة بيانات جديدة"""
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'profile'):
            # المدير العام، المنسق، ومدير المنطقة يمكنهم إضافة بيانات
            return request.user.profile.role in ['super_admin', 'coordinator', 'region_manager']
        return False

    def has_change_permission(self, request, obj=None):
        """التحقق من صلاحية تعديل البيانات"""
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'profile'):
            # المدير العام، المنسق، ومدير المنطقة يمكنهم تعديل البيانات
            return request.user.profile.role in ['super_admin', 'coordinator', 'region_manager']
        return False

    def has_delete_permission(self, request, obj=None):
        """التحقق من صلاحية حذف البيانات"""
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'profile'):
            # فقط المدير العام يمكنه حذف البيانات
            return request.user.profile.role == 'super_admin'
        return False


# إلغاء تسجيل UserAdmin الافتراضي وتسجيل الجديد
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Override admin site settings
admin.site.site_header = "نظام إدارة الجداول التشغيلية"
admin.site.site_title = "إدارة الجداول"
admin.site.index_title = "لوحة التحكم"