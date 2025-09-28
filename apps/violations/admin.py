from django.contrib import admin
from .models import Violation


@admin.register(Violation)
class ViolationAdmin(admin.ModelAdmin):
    list_display = ('employee', 'violation_type', 'date', 'time', 'severity', 'status', 'action_taken', 'created_by', 'created_at')
    list_filter = ('violation_type', 'severity', 'status', 'action_taken', 'date', 'created_at')
    search_fields = ('employee__first_name', 'employee__last_name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'investigation_date', 'resolution_date', 'archived_at')
    
    fieldsets = (
        ('المخالفة', {
            'fields': ('employee', 'violation_type', 'date', 'time', 'severity')
        }),
        ('الوصف والتفاصيل', {
            'fields': ('description', 'witnesses', 'evidence')
        }),
        ('الحالة والإجراء', {
            'fields': ('status', 'action_taken', 'action_description')
        }),
        ('التحقيق', {
            'fields': ('investigated_by', 'investigation_date'),
            'classes': ('collapse',)
        }),
        ('الإنشاء والتتبع', {
            'fields': ('created_by', 'resolution_date', 'archived_at')
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
    
    actions = ['resolve_violations', 'archive_violations']
    
    def resolve_violations(self, request, queryset):
        for violation in queryset.filter(status__in=['pending', 'investigating']):
            violation.resolve('warning', 'تم حل المخالفة من الإدارة')
        self.message_user(request, f"تم حل {queryset.count()} مخالفة")
    resolve_violations.short_description = "حل المخالفات المحددة"
    
    def archive_violations(self, request, queryset):
        for violation in queryset.filter(status='resolved'):
            violation.archive()
        self.message_user(request, f"تم أرشفة {queryset.count()} مخالفة")
    archive_violations.short_description = "أرشفة المخالفات المحددة"
    
    def save_model(self, request, obj, form, change):
        if not change:  # إذا كان إنشاء جديد
            obj.created_by = request.user
        super().save_model(request, obj, form, change)