from django.contrib import admin
from .models import Employee, EmployeeDocument, EmployeeEmergencyContact


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_number', 'user', 'job_title', 'status', 'hire_date', 'get_branch', 'get_role']
    list_filter = ['status', 'employment_type', 'hire_date', 'user__profile__role', 'user__profile__branch']
    search_fields = ['employee_number', 'user__first_name', 'user__last_name', 'job_title']
    readonly_fields = ['employee_number', 'created_at', 'updated_at']
    
    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('user', 'employee_number', 'job_title', 'employment_type', 'status')
        }),
        ('معلومات التوظيف', {
            'fields': ('hire_date', 'termination_date', 'work_location', 'direct_manager')
        }),
        ('معلومات إضافية', {
            'fields': ('notes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_branch(self, obj):
        return obj.get_branch()
    get_branch.short_description = 'الفرع'
    
    def get_role(self, obj):
        return obj.get_role()
    get_role.short_description = 'الدور'


@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display = ['employee', 'title', 'document_type', 'uploaded_at']
    list_filter = ['document_type', 'uploaded_at']
    search_fields = ['employee__user__first_name', 'employee__user__last_name', 'title']
    readonly_fields = ['uploaded_at']


@admin.register(EmployeeEmergencyContact)
class EmployeeEmergencyContactAdmin(admin.ModelAdmin):
    list_display = ['employee', 'name', 'relationship', 'phone', 'is_primary']
    list_filter = ['relationship', 'is_primary']
    search_fields = ['employee__user__first_name', 'employee__user__last_name', 'name', 'phone']