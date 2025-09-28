from django.contrib import admin
from .models import Schedule, ScheduleEntry


class ScheduleEntryInline(admin.TabularInline):
    model = ScheduleEntry
    extra = 0
    fields = ('employee', 'date', 'shift', 'start_time', 'end_time', 'hours', 'is_cover')
    readonly_fields = ('hours',)


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'branch', 'schedule_type', 'status', 'get_entries_count', 'get_employees_count', 'created_by', 'created_at')
    list_filter = ('schedule_type', 'status', 'branch', 'created_at')
    search_fields = ('branch__name', 'notes')
    readonly_fields = ('version', 'created_at', 'updated_at')
    inlines = [ScheduleEntryInline]
    
    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('branch', 'schedule_type', 'start_date', 'end_date', 'status')
        }),
        ('الإدارة', {
            'fields': ('created_by', 'version')
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
    
    def get_entries_count(self, obj):
        return obj.get_entries_count()
    get_entries_count.short_description = 'عدد الإدخالات'
    
    def get_employees_count(self, obj):
        return obj.get_employees_count()
    get_employees_count.short_description = 'عدد الموظفين'
    
    def save_model(self, request, obj, form, change):
        if not change:  # إذا كان إنشاء جديد
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

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


@admin.register(ScheduleEntry)
class ScheduleEntryAdmin(admin.ModelAdmin):
    list_display = ('schedule', 'employee', 'date', 'shift', 'start_time', 'end_time', 'hours', 'is_cover')
    list_filter = ('is_cover', 'date', 'schedule__branch', 'shift')
    search_fields = ('employee__first_name', 'employee__last_name', 'schedule__branch__name')
    readonly_fields = ('hours', 'created_at', 'updated_at')
    
    fieldsets = (
        ('الجدول والموظف', {
            'fields': ('schedule', 'employee')
        }),
        ('التوقيت', {
            'fields': ('date', 'shift', 'start_time', 'end_time', 'hours')
        }),
        ('معلومات إضافية', {
            'fields': ('is_cover', 'notes'),
            'classes': ('collapse',)
        }),
        ('معلومات النظام', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )