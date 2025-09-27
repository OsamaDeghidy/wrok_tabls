def user_permissions(request):
    """Context processor لإضافة صلاحيات المستخدم للقوالب"""
    if not request.user.is_authenticated:
        return {}
    
    perms = {
        'can_view_dashboard': True,  # جميع المستخدمين يمكنهم رؤية لوحة التحكم
        
        # صلاحيات إدارة الموظفين
        'can_view_employees': request.user.can_manage_employees,
        'can_add_employees': request.user.can_manage_employees,
        'can_edit_employees': request.user.can_manage_employees,
        'can_delete_employees': request.user.can_manage_employees,
        
        # صلاحيات إدارة الفروع
        'can_view_branches': request.user.can_manage_branches,
        'can_add_branches': request.user.can_manage_branches,
        'can_edit_branches': request.user.can_manage_branches,
        'can_delete_branches': request.user.can_manage_branches,
        
        # صلاحيات إدارة الجداول
        'can_view_schedules': True,  # جميع المستخدمين يمكنهم رؤية الجداول
        'can_add_schedules': request.user.can_create_schedules,
        'can_edit_schedules': request.user.can_create_schedules,
        'can_delete_schedules': request.user.can_create_schedules,
        
        # صلاحيات إدارة الإجازات
        'can_view_leaves': True,
        'can_add_leaves': True,
        'can_edit_leaves': request.user.can_manage_employees,
        'can_delete_leaves': request.user.can_manage_employees,
        
        # صلاحيات الموافقات
        'can_view_approvals': request.user.can_approve,
        'can_approve': request.user.can_approve,
        'can_reject': request.user.can_approve,
        
        # صلاحيات إدارة المخالفات
        'can_view_violations': request.user.can_manage_employees,
        'can_add_violations': request.user.can_manage_employees,
        'can_edit_violations': request.user.can_manage_employees,
        'can_delete_violations': request.user.can_manage_employees,
        
        # صلاحيات التقارير
        'can_view_reports': request.user.can_manage_employees,
        'can_generate_reports': request.user.can_manage_employees,
        
        # صلاحيات التكاملات
        'can_view_integrations': request.user.is_super_admin,
        'can_manage_integrations': request.user.is_super_admin,
        
        # صلاحيات إدارة المستخدمين
        'can_view_users': request.user.can_manage_employees,
        'can_add_users': request.user.can_manage_employees,
        'can_edit_users': request.user.can_manage_employees,
        'can_delete_users': request.user.can_manage_employees,
    }
    
    return {'user_perms': perms}