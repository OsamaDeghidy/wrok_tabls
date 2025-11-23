from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from .models import Branch, BranchShift
from .forms import BranchForm, BranchShiftForm
from django.utils.dateparse import parse_date, parse_time
import json


@login_required
def branch_list_view(request):
    """قائمة الفروع"""
    search_query = request.GET.get('search', '')
    type_filter = request.GET.get('type', '')
    category_filter = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')
    region_filter = request.GET.get('region', '')
    
    # الحصول على الفروع حسب الصلاحيات
    if request.user.is_superuser:
        branches = Branch.objects.all()
    elif hasattr(request.user, 'profile'):
        if request.user.profile.can_manage_branches:
            branches = Branch.objects.all()
        else:
            branches = Branch.objects.none()
    else:
        branches = Branch.objects.none()
    
    # تطبيق الفلاتر
    if search_query:
        branches = branches.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(address__icontains=search_query)
        )
    
    if type_filter:
        branches = branches.filter(type=type_filter)
    
    if category_filter:
        branches = branches.filter(category=category_filter)
    
    if status_filter:
        branches = branches.filter(status=status_filter)
    
    if region_filter:
        branches = branches.filter(region=region_filter)
    
    # الترقيم
    paginator = Paginator(branches, 20)
    page_number = request.GET.get('page')
    branches = paginator.get_page(page_number)
    
    context = {
        'branches': branches,
        'search_query': search_query,
        'type_filter': type_filter,
        'category_filter': category_filter,
        'status_filter': status_filter,
        'region_filter': region_filter,
        'type_choices': Branch.TYPE_CHOICES,
        'category_choices': Branch.CATEGORY_CHOICES,
        'status_choices': Branch.STATUS_CHOICES,
        'region_choices': Branch.REGION_CHOICES,
    }
    
    return render(request, 'branches/list.html', context)


@login_required
def branch_detail_view(request, branch_id):
    """تفاصيل الفرع"""
    branch = get_object_or_404(Branch, id=branch_id)
    
    # التحقق من الصلاحيات
    if not request.user.is_superuser and not (hasattr(request.user, 'profile') and request.user.profile.can_manage_branches):
        messages.error(request, 'ليس لديك صلاحية لعرض هذا الفرع')
        return redirect('branches:list')
    
    # الحصول على الشفتات
    shifts = branch.shifts.all()
    
    # الحصول على الموظفين
    employees = User.objects.filter(profile__branch=branch).select_related('profile')
    
    context = {
        'branch': branch,
        'shifts': shifts,
        'employees': employees,
    }
    
    return render(request, 'branches/detail.html', context)


@login_required
def branch_create_view(request):
    """إنشاء فرع جديد"""
    if not request.user.is_superuser and not (hasattr(request.user, 'profile') and request.user.profile.can_manage_branches):
        messages.error(request, 'ليس لديك صلاحية لإنشاء فروع')
        return redirect('branches:list')
    
    # الحصول على المديرين المؤهلين
    managers = User.objects.filter(
        profile__role__in=['branch_manager', 'coordinator', 'region_manager', 'operations_manager', 'admin_manager', 'super_admin']
    )
    
    if request.method == 'POST':
        try:
            # إنشاء الفرع
            branch = Branch.objects.create(
                name=request.POST.get('name', ''),
                code=request.POST.get('code', ''),
                type=request.POST.get('type', 'branch'),
                category=request.POST.get('category', 'B'),
                status=request.POST.get('status', 'active'),
                address=request.POST.get('address', ''),
                city=request.POST.get('city', ''),
                region=request.POST.get('region', ''),
                postal_code=request.POST.get('postal_code', ''),
                phone=request.POST.get('phone', ''),
                email=request.POST.get('email', ''),
                capacity=int(request.POST.get('capacity', 0)) if request.POST.get('capacity') else 0,
                opening_date=parse_date(request.POST.get('opening_date')) if request.POST.get('opening_date') else None,
                working_days=request.POST.getlist('working_days'),
                description=request.POST.get('description', ''),
                notes=request.POST.get('notes', '')
            )
            
            # تعيين المدير
            manager_id = request.POST.get('manager')
            if manager_id:
                try:
                    branch.manager = User.objects.get(id=manager_id)
                    branch.save()
                except User.DoesNotExist:
                    pass
            
            # إنشاء الشفتات
            shift_names = request.POST.getlist('shift_name[]')
            shift_starts = request.POST.getlist('shift_start[]')
            shift_ends = request.POST.getlist('shift_end[]')
            break_starts = request.POST.getlist('break_start[]')
            break_ends = request.POST.getlist('break_end[]')
            
            for i in range(len(shift_names)):
                if shift_names[i] and shift_starts[i] and shift_ends[i]:
                    BranchShift.objects.create(
                        branch=branch,
                        name=shift_names[i],
                        start_time=parse_time(shift_starts[i]),
                        end_time=parse_time(shift_ends[i]),
                        break_start=parse_time(break_starts[i]) if i < len(break_starts) and break_starts[i] else None,
                        break_end=parse_time(break_ends[i]) if i < len(break_ends) and break_ends[i] else None,
                        is_active=True
                    )
            
            messages.success(request, f'تم إنشاء الفرع {branch.name} بنجاح')
            return redirect('branches:detail', branch_id=branch.id)
            
        except Exception as e:
            messages.error(request, f'حدث خطأ في إنشاء الفرع: {str(e)}')
            print(f"Error in branch_create_view: {e}")
    
    context = {
        'title': 'إنشاء فرع جديد',
        'managers': managers,
        'branch': None  # للتمييز بين إنشاء وتعديل
    }
    return render(request, 'branches/form.html', context)


@login_required
def branch_edit_view(request, branch_id):
    """تعديل الفرع"""
    branch = get_object_or_404(Branch, id=branch_id)
    
    # التحقق من الصلاحيات
    if not request.user.is_superuser and not (hasattr(request.user, 'profile') and request.user.profile.can_manage_branches):
        messages.error(request, 'ليس لديك صلاحية لتعديل هذا الفرع')
        return redirect('branches:list')
    
    # الحصول على المديرين المؤهلين
    managers = User.objects.filter(
        profile__role__in=['branch_manager', 'coordinator', 'region_manager', 'operations_manager', 'admin_manager', 'super_admin']
    )
    
    if request.method == 'POST':
        try:
            # تحديث بيانات الفرع
            branch.name = request.POST.get('name', '')
            branch.code = request.POST.get('code', '')
            branch.type = request.POST.get('type', 'branch')
            branch.category = request.POST.get('category', 'B')
            branch.status = request.POST.get('status', 'active')
            branch.address = request.POST.get('address', '')
            branch.city = request.POST.get('city', '')
            branch.region = request.POST.get('region', '')
            branch.postal_code = request.POST.get('postal_code', '')
            branch.phone = request.POST.get('phone', '')
            branch.email = request.POST.get('email', '')
            branch.capacity = int(request.POST.get('capacity', 0)) if request.POST.get('capacity') else 0
            branch.opening_date = parse_date(request.POST.get('opening_date')) if request.POST.get('opening_date') else None
            branch.working_days = request.POST.getlist('working_days')
            branch.description = request.POST.get('description', '')
            branch.notes = request.POST.get('notes', '')
            
            # تحديث المدير
            manager_id = request.POST.get('manager')
            if manager_id:
                try:
                    branch.manager = User.objects.get(id=manager_id)
                except User.DoesNotExist:
                    branch.manager = None
            else:
                branch.manager = None
            
            branch.save()
            
            # تحديث الشفتات (حذف القديمة وإنشاء الجديدة)
            branch.shifts.all().delete()
            
            shift_names = request.POST.getlist('shift_name[]')
            shift_starts = request.POST.getlist('shift_start[]')
            shift_ends = request.POST.getlist('shift_end[]')
            break_starts = request.POST.getlist('break_start[]')
            break_ends = request.POST.getlist('break_end[]')
            
            for i in range(len(shift_names)):
                if shift_names[i] and shift_starts[i] and shift_ends[i]:
                    BranchShift.objects.create(
                        branch=branch,
                        name=shift_names[i],
                        start_time=parse_time(shift_starts[i]),
                        end_time=parse_time(shift_ends[i]),
                        break_start=parse_time(break_starts[i]) if i < len(break_starts) and break_starts[i] else None,
                        break_end=parse_time(break_ends[i]) if i < len(break_ends) and break_ends[i] else None,
                        is_active=True
                    )
            
            messages.success(request, f'تم تحديث الفرع {branch.name} بنجاح')
            return redirect('branches:detail', branch_id=branch.id)
            
        except Exception as e:
            messages.error(request, f'حدث خطأ في تحديث الفرع: {str(e)}')
            print(f"Error in branch_edit_view: {e}")
    
    context = {
        'title': 'تعديل الفرع', 
        'branch': branch,
        'managers': managers
    }
    return render(request, 'branches/form.html', context)


@login_required
@require_http_methods(["DELETE"])
@csrf_exempt
def branch_delete_view(request, branch_id):
    """حذف الفرع"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'ليس لديك صلاحية للحذف'})
    
    branch = get_object_or_404(Branch, id=branch_id)
    branch_name = branch.name
    branch.delete()
    
    return JsonResponse({'success': True, 'message': f'تم حذف الفرع {branch_name} بنجاح'})


@login_required
def shift_create_view(request, branch_id):
    """إنشاء شفت جديد"""
    branch = get_object_or_404(Branch, id=branch_id)
    
    # التحقق من الصلاحيات
    if not request.user.is_superuser and not (hasattr(request.user, 'profile') and request.user.profile.can_manage_branches):
        messages.error(request, 'ليس لديك صلاحية لإنشاء شفتات')
        return redirect('branches:detail', branch_id=branch.id)
    
    if request.method == 'POST':
        form = BranchShiftForm(request.POST)
        if form.is_valid():
            shift = form.save(commit=False)
            shift.branch = branch
            shift.save()
            messages.success(request, f'تم إنشاء الشفت {shift.name} بنجاح')
            return redirect('branches:detail', branch_id=branch.id)
    else:
        form = BranchShiftForm()
    
    context = {
        'form': form,
        'title': f'إنشاء شفت جديد لـ {branch.name}',
        'branch': branch,
    }
    
    return render(request, 'branches/shift_form.html', context)


@login_required
def shift_edit_view(request, branch_id, shift_id):
    """تعديل الشفت"""
    branch = get_object_or_404(Branch, id=branch_id)
    shift = get_object_or_404(BranchShift, id=shift_id, branch=branch)
    
    # التحقق من الصلاحيات
    if not request.user.is_superuser and not (hasattr(request.user, 'profile') and request.user.profile.can_manage_branches):
        messages.error(request, 'ليس لديك صلاحية لتعديل الشفتات')
        return redirect('branches:detail', branch_id=branch.id)
    
    if request.method == 'POST':
        form = BranchShiftForm(request.POST, instance=shift)
        if form.is_valid():
            form.save()
            messages.success(request, f'تم تحديث الشفت {shift.name} بنجاح')
            return redirect('branches:detail', branch_id=branch.id)
    else:
        form = BranchShiftForm(instance=shift)
    
    context = {
        'form': form,
        'title': f'تعديل شفت {shift.name}',
        'branch': branch,
        'shift': shift,
    }
    
    return render(request, 'branches/shift_form.html', context)


@login_required
@require_http_methods(["DELETE"])
@csrf_exempt
def shift_delete_view(request, branch_id, shift_id):
    """حذف الشفت"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'ليس لديك صلاحية للحذف'})
    
    shift = get_object_or_404(BranchShift, id=shift_id)
    shift_name = shift.name
    shift.delete()
    
    return JsonResponse({'success': True, 'message': f'تم حذف الشفت {shift_name} بنجاح'})


# API Views
@login_required
def api_branch_list(request):
    """API للحصول على قائمة الفروع"""
    search = request.GET.get('search', '')
    type_filter = request.GET.get('type', '')
    
    branches = Branch.objects.all()
    
    if search:
        branches = branches.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search) |
            Q(city__icontains=search)
        )
    
    if type_filter:
        branches = branches.filter(type=type_filter)
    
    data = []
    for branch in branches[:50]:  # حد أقصى 50 نتيجة
        data.append({
            'id': branch.id,
            'name': branch.name,
            'code': branch.code,
            'type': branch.get_type_display(),
            'status': branch.get_status_display(),
            'city': branch.city,
            'region': branch.get_region_display() if branch.region else None,
            'manager': branch.manager.get_full_name() if branch.manager else None,
        })
    
    return JsonResponse({'branches': data})


@login_required
def api_branch_detail(request, branch_id):
    """API للحصول على تفاصيل الفرع"""
    try:
        branch = Branch.objects.get(id=branch_id)
        
        data = {
            'id': branch.id,
            'name': branch.name,
            'code': branch.code,
            'type': branch.get_type_display(),
            'status': branch.get_status_display(),
            'address': branch.address,
            'city': branch.city,
            'region': branch.get_region_display() if branch.region else None,
            'postal_code': branch.postal_code,
            'phone': branch.phone,
            'email': branch.email,
            'manager': branch.manager.get_full_name() if branch.manager else None,
            'capacity': branch.capacity,
            'opening_date': branch.opening_date.isoformat() if branch.opening_date else None,
            'working_days': branch.working_days,
            'description': branch.description,
            'notes': branch.notes,
            'shifts_count': branch.shifts.count(),
            'employees_count': branch.employees.count(),
        }
        
        return JsonResponse({'branch': data})
    except Branch.DoesNotExist:
        return JsonResponse({'error': 'الفرع غير موجود'}, status=404)


@login_required
def api_shift_list(request, branch_id):
    """API للحصول على قائمة شفتات الفرع"""
    try:
        branch = Branch.objects.get(id=branch_id)
        shifts = branch.shifts.all()
        
        data = []
        for shift in shifts:
            data.append({
                'id': shift.id,
                'name': shift.name,
                'start_time': shift.start_time.strftime('%H:%M'),
                'end_time': shift.end_time.strftime('%H:%M'),
                'break_start': shift.break_start.strftime('%H:%M') if shift.break_start else None,
                'break_end': shift.break_end.strftime('%H:%M') if shift.break_end else None,
                'is_active': shift.is_active,
                'duration': shift.get_duration(),
            })
        
        return JsonResponse({'shifts': data})
    except Branch.DoesNotExist:
        return JsonResponse({'error': 'الفرع غير موجود'}, status=404)


@require_http_methods(["GET"])
def api_regions(request):
    """API لإرجاع قائمة المناطق المتاحة للاستخدام في التسجيل"""
    regions = [
        {"value": key, "label": label}
        for key, label in Branch.REGION_CHOICES
    ]
    return JsonResponse({"regions": regions})