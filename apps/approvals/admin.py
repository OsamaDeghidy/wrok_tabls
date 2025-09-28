from django.contrib import admin
from .models import ApprovalFlow, ApprovalStep


class ApprovalStepInline(admin.TabularInline):
    model = ApprovalStep
    extra = 0
    fields = ('step_order', 'required_role', 'assigned_to', 'status', 'action', 'acted_at')
    readonly_fields = ('acted_at',)


@admin.register(ApprovalFlow)
class ApprovalFlowAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_related_object_display', 'current_step', 'total_steps', 'status', 'created_by', 'created_at')
    list_filter = ('status', 'content_type', 'created_at')
    search_fields = ('object_id', 'created_by__username')
    readonly_fields = ('content_type', 'object_id', 'approved_at', 'created_at', 'updated_at')
    inlines = [ApprovalStepInline]
    
    fieldsets = (
        ('الكائن المرتبط', {
            'fields': ('content_type', 'object_id')
        }),
        ('مسار الموافقة', {
            'fields': ('current_step', 'total_steps', 'status')
        }),
        ('الموافقة', {
            'fields': ('created_by', 'approved_by', 'approved_at', 'rejection_reason')
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
    
    actions = ['approve_flows', 'reject_flows']
    
    def approve_flows(self, request, queryset):
        for flow in queryset.filter(status='pending'):
            flow.approve_current_step(request.user, 'تم الموافقة من الإدارة')
        self.message_user(request, f"تم الموافقة على {queryset.count()} مسار")
    approve_flows.short_description = "الموافقة على المسارات المحددة"
    
    def reject_flows(self, request, queryset):
        for flow in queryset.filter(status='pending'):
            flow.reject(request.user, 'تم الرفض من الإدارة')
        self.message_user(request, f"تم رفض {queryset.count()} مسار")
    reject_flows.short_description = "رفض المسارات المحددة"


@admin.register(ApprovalStep)
class ApprovalStepAdmin(admin.ModelAdmin):
    list_display = ('approval_flow', 'step_order', 'required_role', 'assigned_to', 'status', 'action', 'acted_at')
    list_filter = ('status', 'action', 'required_role', 'created_at')
    search_fields = ('approval_flow__id', 'assigned_to__username', 'comment')
    readonly_fields = ('acted_at', 'created_at')
    
    fieldsets = (
        ('الخطوة', {
            'fields': ('approval_flow', 'step_order', 'required_role')
        }),
        ('التعيين', {
            'fields': ('assigned_to', 'status', 'action')
        }),
        ('التعليق', {
            'fields': ('comment', 'acted_at')
        }),
        ('معلومات النظام', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )