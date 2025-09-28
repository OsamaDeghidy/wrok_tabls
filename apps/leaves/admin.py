from django.contrib import admin
from .models import LeaveRequest, LeaveBalance


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'days_count', 'status', 'approved_by', 'created_at')
    list_filter = ('leave_type', 'status', 'start_date', 'created_at')
    search_fields = ('employee__first_name', 'employee__last_name', 'reason')
    readonly_fields = ('days_count', 'created_at', 'updated_at')
    
    fieldsets = (
        ('الموظف والإجازة', {
            'fields': ('employee', 'leave_type', 'start_date', 'end_date', 'days_count')
        }),
        ('السبب والتفاصيل', {
            'fields': ('reason', 'emergency_contact', 'attachments')
        }),
        ('الموافقة', {
            'fields': ('status', 'approved_by', 'approved_at', 'manager_notes')
        }),
        ('ملاحظات إضافية', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('معلومات النظام', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_leaves', 'reject_leaves']
    
    def approve_leaves(self, request, queryset):
        for leave in queryset.filter(status='pending'):
            leave.approve(request.user)
        self.message_user(request, f"تم الموافقة على {queryset.count()} طلب إجازة")
    approve_leaves.short_description = "الموافقة على طلبات الإجازة المحددة"
    
    def reject_leaves(self, request, queryset):
        for leave in queryset.filter(status='pending'):
            leave.reject(request.user, "تم الرفض من الإدارة")
        self.message_user(request, f"تم رفض {queryset.count()} طلب إجازة")
    reject_leaves.short_description = "رفض طلبات الإجازة المحددة"


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'total_days', 'used_days', 'remaining_days', 'year')
    list_filter = ('leave_type', 'year', 'created_at')
    search_fields = ('employee__first_name', 'employee__last_name')
    readonly_fields = ('remaining_days', 'created_at', 'updated_at')
    
    fieldsets = (
        ('الموظف والنوع', {
            'fields': ('employee', 'leave_type', 'year')
        }),
        ('الرصيد', {
            'fields': ('total_days', 'used_days', 'remaining_days')
        }),
        ('معلومات النظام', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )