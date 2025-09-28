from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.utils import timezone
from .models import LeaveRequest, LeaveBalance
from .forms import LeaveRequestForm


@login_required
def leave_list_view(request):
    """قائمة طلبات الإجازات"""
    # إحصائيات
    stats = {
        'pending': LeaveRequest.objects.filter(status='pending').count(),
        'approved': LeaveRequest.objects.filter(status='approved').count(),
        'rejected': LeaveRequest.objects.filter(status='rejected').count(),
        'total': LeaveRequest.objects.count(),
    }
    
    # فلترة وبحث
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    leave_type_filter = request.GET.get('leave_type', '')
    
    # بناء الاستعلام
    leaves = LeaveRequest.objects.select_related('employee', 'approved_by').all()
    
    if search:
        leaves = leaves.filter(
            Q(employee__first_name__icontains=search) |
            Q(employee__last_name__icontains=search) |
            Q(reason__icontains=search)
        )
    
    if status_filter:
        leaves = leaves.filter(status=status_filter)
    
    if leave_type_filter:
        leaves = leaves.filter(leave_type=leave_type_filter)
    
    # ترقيم الصفحات
    paginator = Paginator(leaves, 20)
    page_number = request.GET.get('page')
    leaves = paginator.get_page(page_number)
    
    context = {
        'leaves': leaves,
        'stats': stats,
        'search': search,
        'status_filter': status_filter,
        'leave_type_filter': leave_type_filter,
        'leave_types': LeaveRequest.TYPE_CHOICES,
        'status_choices': LeaveRequest.STATUS_CHOICES,
    }
    
    return render(request, 'leaves/list.html', context)


@login_required
def leave_create_view(request):
    """إنشاء طلب إجازة جديد"""
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST, request.FILES)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.employee = request.user
            
            # معالجة المرفقات
            attachments = []
            if 'attachments' in request.FILES:
                import os
                from django.conf import settings
                
                # إنشاء مجلد المرفقات إذا لم يكن موجوداً
                attachments_dir = os.path.join(settings.MEDIA_ROOT, 'leave_attachments', str(leave.id) if leave.id else 'temp')
                os.makedirs(attachments_dir, exist_ok=True)
                
                for file in request.FILES.getlist('attachments'):
                    # إنشاء اسم فريد للملف
                    import uuid
                    file_extension = os.path.splitext(file.name)[1]
                    unique_filename = f"{uuid.uuid4()}{file_extension}"
                    
                    # حفظ الملف
                    file_path = os.path.join(attachments_dir, unique_filename)
                    with open(file_path, 'wb') as destination:
                        for chunk in file.chunks():
                            destination.write(chunk)
                    
                    # إضافة مسار الملف إلى القائمة
                    relative_path = f"leave_attachments/{leave.id if leave.id else 'temp'}/{unique_filename}"
                    attachments.append({
                        'original_name': file.name,
                        'file_path': relative_path,
                        'file_size': file.size,
                        'uploaded_at': timezone.now().isoformat()
                    })
            
            leave.attachments = attachments
            
            # التحقق من التداخل بعد تعيين employee
            if leave.start_date and leave.end_date:
                overlapping_leaves = LeaveRequest.objects.filter(
                    employee=leave.employee,
                    status__in=['pending', 'approved'],
                    start_date__lte=leave.end_date,
                    end_date__gte=leave.start_date
                )
                
                if overlapping_leaves.exists():
                    form.add_error('start_date', 'يوجد إجازة متداخلة مع هذه الفترة')
                    messages.error(request, 'يوجد إجازة متداخلة مع هذه الفترة')
                else:
                    leave.save()
                    messages.success(request, 'تم إنشاء طلب الإجازة بنجاح')
                    return redirect('leaves:detail', leave_id=leave.id)
            else:
                leave.save()
                messages.success(request, 'تم إنشاء طلب الإجازة بنجاح')
                return redirect('leaves:detail', leave_id=leave.id)
        else:
            messages.error(request, 'حدث خطأ في إنشاء طلب الإجازة')
            # طباعة الأخطاء للتشخيص
            for field, errors in form.errors.items():
                for error in errors:
                    print(f"Field {field}: {error}")
    else:
        form = LeaveRequestForm()
    
    context = {
        'form': form,
        'leave_types': LeaveRequest.TYPE_CHOICES,
    }
    
    return render(request, 'leaves/create.html', context)


@login_required
def leave_detail_view(request, leave_id):
    """تفاصيل طلب الإجازة"""
    leave = get_object_or_404(LeaveRequest, id=leave_id)
    
    # التحقق من الصلاحيات
    if not request.user.is_superuser and not request.user.is_staff and leave.employee != request.user:
        messages.error(request, 'ليس لديك صلاحية لعرض هذا الطلب')
        return redirect('leaves:list')
    
    context = {
        'leave': leave,
    }
    
    return render(request, 'leaves/detail.html', context)


@login_required
def leave_edit_view(request, leave_id):
    """تعديل طلب الإجازة"""
    leave = get_object_or_404(LeaveRequest, id=leave_id)
    
    # التحقق من الصلاحيات
    if not request.user.is_superuser and not request.user.is_staff and leave.employee != request.user:
        messages.error(request, 'ليس لديك صلاحية لتعديل هذا الطلب')
        return redirect('leaves:list')
    
    # لا يمكن تعديل الطلبات المعتمدة أو المرفوضة
    if leave.status in ['approved', 'rejected']:
        messages.error(request, 'لا يمكن تعديل الطلبات المعتمدة أو المرفوضة')
        return redirect('leaves:detail', leave_id=leave.id)
    
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST, request.FILES, instance=leave)
        if form.is_valid():
            updated_leave = form.save(commit=False)
            
            # معالجة المرفقات
            if 'attachments' in request.FILES:
                import os
                from django.conf import settings
                
                # الحصول على المرفقات الموجودة أو إنشاء قائمة جديدة
                existing_attachments = updated_leave.attachments if updated_leave.attachments else []
                
                # إنشاء مجلد المرفقات
                attachments_dir = os.path.join(settings.MEDIA_ROOT, 'leave_attachments', str(leave.id))
                os.makedirs(attachments_dir, exist_ok=True)
                
                for file in request.FILES.getlist('attachments'):
                    # إنشاء اسم فريد للملف
                    import uuid
                    file_extension = os.path.splitext(file.name)[1]
                    unique_filename = f"{uuid.uuid4()}{file_extension}"
                    
                    # حفظ الملف
                    file_path = os.path.join(attachments_dir, unique_filename)
                    with open(file_path, 'wb') as destination:
                        for chunk in file.chunks():
                            destination.write(chunk)
                    
                    # إضافة مسار الملف إلى القائمة
                    relative_path = f"leave_attachments/{leave.id}/{unique_filename}"
                    existing_attachments.append({
                        'original_name': file.name,
                        'file_path': relative_path,
                        'file_size': file.size,
                        'uploaded_at': timezone.now().isoformat()
                    })
                
                updated_leave.attachments = existing_attachments
            
            # التحقق من التداخل (استبعاد الطلب الحالي)
            if updated_leave.start_date and updated_leave.end_date:
                overlapping_leaves = LeaveRequest.objects.filter(
                    employee=updated_leave.employee,
                    status__in=['pending', 'approved'],
                    start_date__lte=updated_leave.end_date,
                    end_date__gte=updated_leave.start_date
                ).exclude(pk=leave.id)
                
                if overlapping_leaves.exists():
                    form.add_error('start_date', 'يوجد إجازة متداخلة مع هذه الفترة')
                    messages.error(request, 'يوجد إجازة متداخلة مع هذه الفترة')
                else:
                    form.save()
                    messages.success(request, 'تم تحديث طلب الإجازة بنجاح')
                    return redirect('leaves:detail', leave_id=leave.id)
            else:
                form.save()
                messages.success(request, 'تم تحديث طلب الإجازة بنجاح')
                return redirect('leaves:detail', leave_id=leave.id)
        else:
            messages.error(request, 'حدث خطأ في تحديث طلب الإجازة')
    else:
        form = LeaveRequestForm(instance=leave)
    
    context = {
        'form': form,
        'leave': leave,
        'leave_types': LeaveRequest.TYPE_CHOICES,
    }
    
    return render(request, 'leaves/form.html', context)


@login_required
def leave_approve_view(request, leave_id):
    """موافقة على طلب الإجازة"""
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, 'ليس لديك صلاحية للموافقة على الطلبات')
        return redirect('leaves:list')
    
    leave = get_object_or_404(LeaveRequest, id=leave_id)
    
    if leave.status != 'pending':
        messages.error(request, 'يمكن الموافقة على الطلبات المعلقة فقط')
        return redirect('leaves:detail', leave_id=leave.id)
    
    leave.approve(request.user)
    messages.success(request, 'تم الموافقة على طلب الإجازة')
    
    return redirect('leaves:detail', leave_id=leave.id)


@login_required
def leave_reject_view(request, leave_id):
    """رفض طلب الإجازة"""
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, 'ليس لديك صلاحية لرفض الطلبات')
        return redirect('leaves:list')
    
    leave = get_object_or_404(LeaveRequest, id=leave_id)
    
    if leave.status != 'pending':
        messages.error(request, 'يمكن رفض الطلبات المعلقة فقط')
        return redirect('leaves:detail', leave_id=leave.id)
    
    manager_notes = request.POST.get('manager_notes', '')
    leave.reject(request.user, manager_notes)
    messages.success(request, 'تم رفض طلب الإجازة')
    
    return redirect('leaves:detail', leave_id=leave.id)


@login_required
def leave_cancel_view(request, leave_id):
    """إلغاء طلب الإجازة"""
    leave = get_object_or_404(LeaveRequest, id=leave_id)
    
    # التحقق من الصلاحيات
    if not request.user.is_superuser and not request.user.is_staff and leave.employee != request.user:
        messages.error(request, 'ليس لديك صلاحية لإلغاء هذا الطلب')
        return redirect('leaves:list')
    
    if leave.status not in ['pending']:
        messages.error(request, 'يمكن إلغاء الطلبات المعلقة فقط')
        return redirect('leaves:detail', leave_id=leave.id)
    
    leave.cancel()
    messages.success(request, 'تم إلغاء طلب الإجازة')
    
    return redirect('leaves:detail', leave_id=leave.id)


@login_required
def leave_balance_view(request):
    """عرض رصيد الإجازات للموظف"""
    balances = LeaveBalance.objects.filter(employee=request.user)
    
    context = {
        'balances': balances,
    }
    
    return render(request, 'leaves/balance.html', context)