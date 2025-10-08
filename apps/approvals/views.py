from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from .models import ApprovalFlow, ApprovalStep
from apps.schedules.models import Schedule
from apps.leaves.models import LeaveRequest
from apps.users.models import UserProfile
import json


@login_required
def approvals_list_view(request):
    """قائمة الموافقات"""
    
    # التحقق من الصلاحيات
    if not request.user.is_authenticated:
        return redirect('login')
    
    # جلب الموافقات حسب دور المستخدم
    user_profile = getattr(request.user, 'profile', None)
    if not user_profile:
        messages.error(request, 'لم يتم العثور على ملف المستخدم')
        return redirect('dashboard')
    
    # تحديد الموافقات المطلوب عرضها حسب الدور
    if user_profile.role == 'super_admin':
        # المدير العام يرى جميع الموافقات
        approval_flows = ApprovalFlow.objects.all()
    elif user_profile.role in ['coordinator', 'region_manager', 'operations_manager', 'admin_manager']:
        # المدراء يرون الموافقات المطلوب منهم موافقة عليها
        approval_flows = ApprovalFlow.objects.filter(
            Q(status='in_progress') | Q(status='pending'),
            current_step__lte=4  # خطوات الموافقة العادية
        )
    else:
        # الموظفين العاديين يرون موافقاتهم فقط
        approval_flows = ApprovalFlow.objects.filter(created_by=request.user)
    
    # إحصائيات
    stats = {
        'pending': approval_flows.filter(status='pending').count(),
        'in_progress': approval_flows.filter(status='in_progress').count(),
        'approved': approval_flows.filter(status='approved').count(),
        'rejected': approval_flows.filter(status='rejected').count(),
        'total': approval_flows.count()
    }
    
    # فلترة حسب الحالة
    status_filter = request.GET.get('status', '')
    if status_filter:
        approval_flows = approval_flows.filter(status=status_filter)
    
    # ترتيب حسب التاريخ
    approval_flows = approval_flows.order_by('-created_at')
    
    # تقسيم الصفحات
    paginator = Paginator(approval_flows, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'approval_flows': page_obj,
        'stats': stats,
        'status_filter': status_filter,
        'user_role': user_profile.role,
    }
    
    return render(request, 'approvals/list.html', context)


@login_required
def approval_detail_view(request, approval_id):
    """تفاصيل الموافقة"""
    
    approval_flow = get_object_or_404(ApprovalFlow, id=approval_id)
    
    # التحقق من الصلاحيات
    user_profile = getattr(request.user, 'profile', None)
    if not user_profile:
        messages.error(request, 'لم يتم العثور على ملف المستخدم')
        return redirect('approvals:list')
    
    # التحقق من إمكانية الوصول للموافقة
    can_view = (
        request.user.is_superuser or
        approval_flow.created_by == request.user or
        (user_profile.role in ['coordinator', 'region_manager', 'operations_manager', 'admin_manager'] and 
         approval_flow.status in ['pending', 'in_progress'])
    )
    
    if not can_view:
        messages.error(request, 'ليس لديك صلاحية لعرض هذه الموافقة')
        return redirect('approvals:list')
    
    # جلب خطوات الموافقة
    approval_steps = approval_flow.steps.all().order_by('step_order')
    
    # التحقق من إمكانية الموافقة/الرفض
    can_approve = False
    if approval_flow.status in ['pending', 'in_progress']:
        current_role = approval_flow.get_current_step_info()
        if current_role == user_profile.role:
            can_approve = True
    
    context = {
        'approval_flow': approval_flow,
        'approval_steps': approval_steps,
        'can_approve': can_approve,
        'user_role': user_profile.role,
    }
    
    return render(request, 'approvals/detail.html', context)


@login_required
@require_http_methods(["POST"])
def approve_request_view(request, approval_id):
    """الموافقة على الطلب"""
    
    approval_flow = get_object_or_404(ApprovalFlow, id=approval_id)
    
    # التحقق من الصلاحيات
    user_profile = getattr(request.user, 'profile', None)
    if not user_profile:
        return JsonResponse({'success': False, 'error': 'لم يتم العثور على ملف المستخدم'})
    
    # التحقق من إمكانية الموافقة
    current_role = approval_flow.get_current_step_info()
    if current_role != user_profile.role:
        return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية للموافقة على هذه الخطوة'})
    
    if approval_flow.status not in ['pending', 'in_progress']:
        return JsonResponse({'success': False, 'error': 'هذه الموافقة لا يمكن الموافقة عليها'})
    
    # جلب التعليق
    comment = request.POST.get('comment', '')
    
    try:
        # الموافقة على الخطوة الحالية
        approval_flow.approve_current_step(request.user, comment)
        
        # إذا تمت الموافقة النهائية، تحديث حالة الكائن المرتبط
        if approval_flow.status == 'approved':
            related_object = approval_flow.related_object
            if hasattr(related_object, 'status'):
                related_object.status = 'approved'
                related_object.save()
        
        return JsonResponse({
            'success': True, 
            'message': 'تمت الموافقة بنجاح',
            'new_status': approval_flow.status
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'حدث خطأ: {str(e)}'})


@login_required
@require_http_methods(["POST"])
def reject_request_view(request, approval_id):
    """رفض الطلب"""
    
    approval_flow = get_object_or_404(ApprovalFlow, id=approval_id)
    
    # التحقق من الصلاحيات
    user_profile = getattr(request.user, 'profile', None)
    if not user_profile:
        return JsonResponse({'success': False, 'error': 'لم يتم العثور على ملف المستخدم'})
    
    # التحقق من إمكانية الرفض
    current_role = approval_flow.get_current_step_info()
    if current_role != user_profile.role:
        return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية لرفض هذه الخطوة'})
    
    if approval_flow.status not in ['pending', 'in_progress']:
        return JsonResponse({'success': False, 'error': 'هذه الموافقة لا يمكن رفضها'})
    
    # جلب سبب الرفض
    reason = request.POST.get('reason', '')
    if not reason:
        return JsonResponse({'success': False, 'error': 'يرجى إدخال سبب الرفض'})
    
    try:
        # رفض الموافقة
        approval_flow.reject(request.user, reason)
        
        # تحديث حالة الكائن المرتبط
        related_object = approval_flow.related_object
        if hasattr(related_object, 'status'):
            related_object.status = 'rejected'
            related_object.save()
        
        return JsonResponse({
            'success': True, 
            'message': 'تم رفض الطلب بنجاح',
            'new_status': approval_flow.status
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'حدث خطأ: {str(e)}'})


@login_required
def create_approval_for_schedule(request, schedule_id):
    """إنشاء موافقة للجدول التشغيلي"""
    
    schedule = get_object_or_404(Schedule, id=schedule_id)
    
    # التحقق من الصلاحيات
    if not request.user.is_authenticated:
        return redirect('login')
    
    # التحقق من أن الجدول يحتاج موافقة
    if schedule.status in ['approved', 'rejected']:
        messages.error(request, 'هذا الجدول تم التعامل معه مسبقاً')
        return redirect('schedules:detail', schedule_id=schedule.id)
    
    # إنشاء مسار الموافقة
    from django.contrib.contenttypes.models import ContentType
    
    content_type = ContentType.objects.get_for_model(Schedule)
    
    approval_flow = ApprovalFlow.objects.create(
        content_type=content_type,
        object_id=schedule.id,
        created_by=request.user,
        total_steps=4  # منسق -> مدير المنطقة -> مدير العمليات -> مدير الإدارة
    )
    
    # إنشاء خطوات الموافقة
    ApprovalStep.create_default_steps(approval_flow, request.user)
    
    # تحديث حالة الجدول
    schedule.status = 'pending_approval'
    schedule.save()
    
    messages.success(request, 'تم إنشاء طلب الموافقة بنجاح')
    return redirect('approvals:detail', approval_id=approval_flow.id)


@login_required
def my_approvals_view(request):
    """موافقاتي"""
    
    if not request.user.is_authenticated:
        return redirect('login')
    
    # جلب موافقات المستخدم
    my_approvals = ApprovalFlow.objects.filter(created_by=request.user)
    
    # إحصائيات
    stats = {
        'pending': my_approvals.filter(status='pending').count(),
        'in_progress': my_approvals.filter(status='in_progress').count(),
        'approved': my_approvals.filter(status='approved').count(),
        'rejected': my_approvals.filter(status='rejected').count(),
        'total': my_approvals.count()
    }
    
    # ترتيب حسب التاريخ
    my_approvals = my_approvals.order_by('-created_at')
    
    # تقسيم الصفحات
    paginator = Paginator(my_approvals, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'my_approvals': page_obj,
        'stats': stats,
    }
    
    return render(request, 'approvals/my_approvals.html', context)


@login_required
def approvals_guide_view(request):
    """دليل شرح نظام الموافقات"""
    return render(request, 'approvals/guide.html')