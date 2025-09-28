from django.contrib import admin
from .models import Branch, BranchShift


class BranchShiftInline(admin.TabularInline):
    model = BranchShift
    extra = 1
    fields = ('name', 'start_time', 'end_time', 'break_start', 'break_end', 'is_active')


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'type', 'category', 'status', 'region', 'city', 'manager', 'get_employees_count', 'get_active_shifts_count')
    list_filter = ('type', 'category', 'status', 'region', 'created_at')
    search_fields = ('name', 'code', 'city', 'address')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [BranchShiftInline]
    
    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('name', 'code', 'type', 'category', 'status')
        }),
        ('الموقع', {
            'fields': ('address', 'city', 'region', 'postal_code')
        }),
        ('الاتصال', {
            'fields': ('phone', 'email')
        }),
        ('الإدارة', {
            'fields': ('manager', 'capacity', 'opening_date')
        }),
        ('أيام العمل', {
            'fields': ('working_days',),
            'description': 'اختر أيام العمل للفرع'
        }),
        ('معلومات إضافية', {
            'fields': ('description', 'notes'),
            'classes': ('collapse',)
        }),
        ('معلومات النظام', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_employees_count(self, obj):
        return obj.get_employees_count()
    get_employees_count.short_description = 'عدد الموظفين'
    
    def get_active_shifts_count(self, obj):
        return obj.get_active_shifts_count()
    get_active_shifts_count.short_description = 'عدد الشفتات'

    def has_view_permission(self, request, obj=None):
        """التحقق من صلاحية عرض البيانات"""
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'profile'):
            return request.user.profile.role in ['super_admin', 'coordinator', 'region_manager']
        return False

    def has_add_permission(self, request):
        """التحقق من صلاحية إضافة بيانات جديدة"""
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'profile'):
            return request.user.profile.role in ['super_admin', 'coordinator', 'region_manager']
        return False

    def has_change_permission(self, request, obj=None):
        """التحقق من صلاحية تعديل البيانات"""
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'profile'):
            return request.user.profile.role in ['super_admin', 'coordinator', 'region_manager']
        return False

    def has_delete_permission(self, request, obj=None):
        """التحقق من صلاحية حذف البيانات"""
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'profile'):
            return request.user.profile.role == 'super_admin'
        return False


@admin.register(BranchShift)
class BranchShiftAdmin(admin.ModelAdmin):
    list_display = ('branch', 'name', 'start_time', 'end_time', 'get_duration', 'is_active')
    list_filter = ('is_active', 'branch', 'created_at')
    search_fields = ('name', 'branch__name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('branch', 'name', 'is_active')
        }),
        ('أوقات العمل', {
            'fields': ('start_time', 'end_time')
        }),
        ('أوقات الاستراحة', {
            'fields': ('break_start', 'break_end'),
            'classes': ('collapse',)
        }),
        ('معلومات النظام', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_duration(self, obj):
        return f"{obj.get_duration():.1f} ساعة"
    get_duration.short_description = 'المدة'

    def has_view_permission(self, request, obj=None):
        """التحقق من صلاحية عرض البيانات"""
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'profile'):
            return request.user.profile.role in ['super_admin', 'coordinator', 'region_manager']
        return False

    def has_add_permission(self, request):
        """التحقق من صلاحية إضافة بيانات جديدة"""
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'profile'):
            return request.user.profile.role in ['super_admin', 'coordinator', 'region_manager']
        return False

    def has_change_permission(self, request, obj=None):
        """التحقق من صلاحية تعديل البيانات"""
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'profile'):
            return request.user.profile.role in ['super_admin', 'coordinator', 'region_manager']
        return False

    def has_delete_permission(self, request, obj=None):
        """التحقق من صلاحية حذف البيانات"""
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'profile'):
            return request.user.profile.role == 'super_admin'
        return False