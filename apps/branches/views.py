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
from .forms import BranchForm, BranchShiftForm, BranchImportForm
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
        elif request.user.profile.role == 'branch_manager' and request.user.profile.branch:
            # مدير المعرض يرى فرعه فقط
            branches = Branch.objects.filter(id=request.user.profile.branch.id)
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
    
    # التحقق من الصلاحيات للعرض في القالب
    can_manage = False
    if request.user.is_superuser:
        can_manage = True
    elif hasattr(request.user, 'profile'):
        can_manage = request.user.profile.can_manage_branches
    
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
        'can_manage': can_manage,
    }
    
    return render(request, 'branches/list.html', context)


@login_required
def branch_detail_view(request, branch_id):
    """تفاصيل الفرع"""
    branch = get_object_or_404(Branch, id=branch_id)
    
    # التحقق من الصلاحيات
    can_view = False
    if request.user.is_superuser:
        can_view = True
    elif hasattr(request.user, 'profile'):
        if request.user.profile.can_manage_branches:
            can_view = True
        elif request.user.profile.role == 'branch_manager' and request.user.profile.branch == branch:
            # مدير المعرض يرى فرعه فقط
            can_view = True
    
    if not can_view:
        messages.error(request, 'ليس لديك صلاحية لعرض هذا الفرع')
        return redirect('branches:list')
    
    # الحصول على الشفتات
    shifts = branch.shifts.all()
    
    # الحصول على الموظفين
    employees = User.objects.filter(profile__branch=branch, is_active=True).select_related('profile')
    
    # التحقق من صلاحيات التعديل
    can_edit = False
    if request.user.is_superuser:
        can_edit = True
    elif hasattr(request.user, 'profile'):
        if request.user.profile.can_manage_branches:
            can_edit = True
        elif request.user.profile.role == 'branch_manager' and request.user.profile.branch == branch:
            # مدير المعرض يمكنه تعديل شفتات فرعه
            can_edit = True
    
    context = {
        'branch': branch,
        'shifts': shifts,
        'employees': employees,
        'can_edit': can_edit,
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
        profile__role__in=['branch_manager', 'coordinator', 'region_manager', 'operations_manager', 'admin_manager', 'super_admin'],
        is_active=True
    ).select_related('profile')
    
    if request.method == 'POST':
        form = BranchForm(request.POST)
        if form.is_valid():
            try:
                branch = form.save(commit=False)
                branch.save()
                
                # إنشاء الشفتات
                shift_names = request.POST.getlist('shift_name[]')
                shift_starts = request.POST.getlist('shift_start[]')
                shift_ends = request.POST.getlist('shift_end[]')
                
                for i in range(len(shift_names)):
                    if shift_names[i] and shift_starts[i] and shift_ends[i]:
                        BranchShift.objects.create(
                            branch=branch,
                            name=shift_names[i],
                            start_time=parse_time(shift_starts[i]),
                            end_time=parse_time(shift_ends[i]),
                            is_active=True
                        )
                
                messages.success(request, f'تم إنشاء الفرع {branch.name} بنجاح')
                return redirect('branches:detail', branch_id=branch.id)
                
            except Exception as e:
                messages.error(request, f'حدث خطأ في إنشاء الفرع: {str(e)}')
                print(f"Error in branch_create_view: {e}")
        else:
            # عرض أخطاء الفورم
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = BranchForm()
    
    # فلترة المديرين حسب الفرع المحدد (إذا كان تعديل)
    # في حالة التعديل، نعرض مديري الفروع الأخرى أيضاً
    context = {
        'title': 'إنشاء فرع جديد',
        'form': form,
        'managers': managers,
        'branch': None  # للتمييز بين إنشاء وتعديل
    }
    return render(request, 'branches/form.html', context)


@login_required
def branch_edit_view(request, branch_id):
    """تعديل الفرع"""
    branch = get_object_or_404(Branch, id=branch_id)
    
    # التحقق من الصلاحيات
    can_edit = False
    if request.user.is_superuser:
        can_edit = True
    elif hasattr(request.user, 'profile'):
        if request.user.profile.can_manage_branches:
            can_edit = True
        elif request.user.profile.role == 'branch_manager' and request.user.profile.branch == branch:
            # مدير المعرض يمكنه تعديل فرعه فقط
            can_edit = True
    
    if not can_edit:
        messages.error(request, 'ليس لديك صلاحية لتعديل هذا الفرع')
        return redirect('branches:list')
    
    # الحصول على المديرين المؤهلين
    managers = User.objects.filter(
        profile__role__in=['branch_manager', 'coordinator', 'region_manager', 'operations_manager', 'admin_manager', 'super_admin'],
        is_active=True
    ).select_related('profile')
    
    if request.method == 'POST':
        form = BranchForm(request.POST, instance=branch)
        if form.is_valid():
            try:
                branch = form.save()
                
                # تحديث الشفتات لمن يملك الصلاحية (مدير النظام، مدير الفروع، أو مدير المعرض على فرعه)
                is_branch_manager_of_this_branch = (
                    hasattr(request.user, 'profile') and
                    request.user.profile.role == 'branch_manager' and
                    request.user.profile.branch == branch
                )
                if request.user.is_superuser or request.user.profile.can_manage_branches or is_branch_manager_of_this_branch:
                    branch.shifts.all().delete()
                    
                    shift_names = request.POST.getlist('shift_name[]')
                    shift_starts = request.POST.getlist('shift_start[]')
                    shift_ends = request.POST.getlist('shift_end[]')
                    
                    for i in range(len(shift_names)):
                        if shift_names[i] and shift_starts[i] and shift_ends[i]:
                            BranchShift.objects.create(
                                branch=branch,
                                name=shift_names[i],
                                start_time=parse_time(shift_starts[i]),
                                end_time=parse_time(shift_ends[i]),
                                is_active=True
                            )
                
                
                messages.success(request, f'تم تحديث الفرع {branch.name} بنجاح')
                return redirect('branches:detail', branch_id=branch.id)
                
            except Exception as e:
                messages.error(request, f'حدث خطأ في تحديث الفرع: {str(e)}')
                print(f"Error in branch_edit_view: {e}")
        else:
            # عرض أخطاء الفورم
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = BranchForm(instance=branch)
    
    # فلترة المديرين حسب الفرع المحدد
    # إذا كان هناك فرع محدد، نعرض مديري الفروع الأخرى أيضاً
    context = {
        'title': 'تعديل الفرع', 
        'form': form,
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
    # يُسمح لـ: المدير العام، من يملك can_manage_branches، ومدير المعرض على فرعه
    is_branch_manager_of_this_branch = (
        hasattr(request.user, 'profile') and
        request.user.profile.role == 'branch_manager' and
        request.user.profile.branch == branch
    )
    if not request.user.is_superuser and not (hasattr(request.user, 'profile') and request.user.profile.can_manage_branches) and not is_branch_manager_of_this_branch:
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
    # يُسمح لـ: المدير العام، من يملك can_manage_branches، ومدير المعرض على فرعه
    is_branch_manager_of_this_branch = (
        hasattr(request.user, 'profile') and
        request.user.profile.role == 'branch_manager' and
        request.user.profile.branch == branch
    )
    if not request.user.is_superuser and not (hasattr(request.user, 'profile') and request.user.profile.can_manage_branches) and not is_branch_manager_of_this_branch:
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


@login_required
def branch_import_view(request):
    """استيراد المعارض من Excel"""
    import pandas as pd
    from datetime import datetime
    
    if not request.user.is_superuser and not (hasattr(request.user, 'profile') and request.user.profile.can_manage_branches):
        messages.error(request, 'ليس لديك صلاحية لاستيراد المعارض')
        return redirect('branches:list')
    
    if request.method == 'POST':
        form = BranchImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                file = request.FILES['file']
                update_existing = form.cleaned_data.get('update_existing', False)
                
                # قراءة الملف
                if file.name.endswith('.xlsx') or file.name.endswith('.xls'):
                    df = pd.read_excel(file)
                elif file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                else:
                    messages.error(request, 'نوع الملف غير مدعوم. يرجى رفع ملف Excel أو CSV')
                    return redirect('branches:import')
                
                created_count = 0
                updated_count = 0
                errors = []
                
                # تحويل أسماء الأعمدة إلى lowercase للتوافق
                df.columns = df.columns.str.strip().str.lower()
                
                # معالجة كل صف
                for index, row in df.iterrows():
                    try:
                        # دعم الأسماء بالإنجليزية والعربية
                        name = str(row.get('name', row.get('اسم الفرع', ''))).strip()
                        code = str(row.get('code', row.get('كود الفرع', ''))).strip()
                        
                        if not name or not code:
                            errors.append(f'الصف {index + 2}: اسم الفرع أو كود الفرع مفقود')
                            continue
                        
                        # التحقق من أن الكود 4 خانات
                        if not (code.isdigit() and len(code) == 4):
                            errors.append(f'الصف {index + 2}: كود الفرع "{code}" يجب أن يكون 4 أرقام')
                            continue
                        
                        # التحقق من وجود الفرع
                        branch = Branch.objects.filter(code=code).first()
                        
                        if branch and update_existing:
                            # تحديث الفرع الموجود
                            branch.name = name
                            branch.type = str(row.get('type', row.get('نوع الفرع', 'branch'))).strip() or 'branch'
                            branch.category = str(row.get('category', row.get('فئة الفرع', 'B'))).strip() or 'B'
                            branch.status = str(row.get('status', row.get('الحالة', 'active'))).strip() or 'active'
                            branch.address = str(row.get('address', row.get('العنوان', ''))).strip()
                            branch.city = str(row.get('city', row.get('المدينة', ''))).strip()
                            branch.region = str(row.get('region', row.get('المنطقة', ''))).strip()
                            
                            # إزالة الحقول القديمة كما طلب العميل
                            # branch.postal_code = str(row.get('postal_code', row.get('الرمز البريدي', ''))).strip()
                            # branch.phone = str(row.get('phone', row.get('رقم الهاتف', ''))).strip()
                            # branch.email = str(row.get('email', row.get('البريد الإلكتروني', ''))).strip()
                            
                            capacity = row.get('capacity', row.get('السعة الاستيعابية', 0))
                            if pd.notna(capacity):
                                try:
                                    branch.capacity = int(capacity)
                                except:
                                    branch.capacity = 0
                            
                            # branch.opening_date = ...
                            
                            # أيام العمل
                            working_days_str = str(row.get('working_days', row.get('أيام العمل', ''))).strip()
                            if working_days_str and working_days_str != 'nan':
                                # تحويل أيام العمل من نص إلى قائمة
                                days_map = {
                                    'السبت': 'saturday', 'saturday': 'saturday',
                                    'الأحد': 'sunday', 'sunday': 'sunday',
                                    'الاثنين': 'monday', 'monday': 'monday',
                                    'الثلاثاء': 'tuesday', 'tuesday': 'tuesday',
                                    'الأربعاء': 'wednesday', 'wednesday': 'wednesday',
                                    'الخميس': 'thursday', 'thursday': 'thursday',
                                    'الجمعة': 'friday', 'friday': 'friday',
                                }
                                working_days = []
                                for day in working_days_str.split(','):
                                    day = day.strip()
                                    if day in days_map:
                                        working_days.append(days_map[day])
                                branch.working_days = working_days
                            
                            branch.description = str(row.get('description', row.get('الوصف', ''))).strip()
                            branch.notes = str(row.get('notes', row.get('ملاحظات', ''))).strip()
                            branch.save()
                            
                            # تحديث الشفتات (دعم 4 شفتات)
                            branch.shifts.all().delete()
                            
                            # الأيام ما عدا الجمعة
                            week_days = [d for d in branch.working_days if d != 'friday']
                            
                            for i in range(1, 5):
                                s_start = str(row.get(f'shift{i}_start', row.get(f'وقت بداية الشفت {i}', ''))).strip()
                                s_end = str(row.get(f'shift{i}_end', row.get(f'وقت نهاية الشفت {i}', ''))).strip()
                                
                                if s_start and s_end and s_start != 'nan' and s_start != 'None':
                                    try:
                                        start_time = parse_time(s_start)
                                        end_time = parse_time(s_end)
                                        if week_days:
                                            BranchShift.objects.create(
                                                branch=branch,
                                                name=f'شفت {i}',
                                                start_time=start_time,
                                                end_time=end_time,
                                                days=week_days,
                                                is_active=True
                                            )
                                    except Exception as e:
                                        print(f"Error creating shift {i}: {e}")

                            # شفت الجمعة
                            friday_start = str(row.get('friday_start', row.get('وقت بداية دوام الجمعة', ''))).strip()
                            friday_end = str(row.get('friday_end', row.get('وقت نهاية دوام الجمعة', ''))).strip()
                            
                            if friday_start and friday_end and friday_start != 'nan':
                                try:
                                    start_time = parse_time(friday_start)
                                    end_time = parse_time(friday_end)
                                    
                                    if 'friday' in branch.working_days:
                                        BranchShift.objects.create(
                                            branch=branch,
                                            name='شفت الجمعة',
                                            start_time=start_time,
                                            end_time=end_time,
                                            days=['friday'],
                                            is_active=True
                                        )
                                except Exception as e:
                                    print(f"Error creating friday shift: {e}")
                                    pass
                            
                            # دعم التنسيق القديم (اختياري، لكن يفضل الاعتماد على الجديد)
                            shift_name = str(row.get('shift_name', row.get('اسم الشفت', ''))).strip()
                            shift_start = str(row.get('shift_start', row.get('وقت بداية الشفت', ''))).strip()
                            shift_end = str(row.get('shift_end', row.get('وقت نهاية الشفت', ''))).strip()
                            
                            if shift_name and shift_start and shift_end and shift_name != 'nan':
                                try:
                                    start_time = parse_time(shift_start)
                                    end_time = parse_time(shift_end)
                                    BranchShift.objects.create(
                                        branch=branch,
                                        name=shift_name,
                                        start_time=start_time,
                                        end_time=end_time,
                                        is_active=True
                                    )
                                except:
                                    pass
                            
                            updated_count += 1
                        elif not branch:
                            # إنشاء فرع جديد
                            branch = Branch.objects.create(
                                name=name,
                                code=code,
                                type=str(row.get('type', row.get('نوع الفرع', 'branch'))).strip() or 'branch',
                                category=str(row.get('category', row.get('فئة الفرع', 'B'))).strip() or 'B',
                                status=str(row.get('status', row.get('الحالة', 'active'))).strip() or 'active',
                                address=str(row.get('address', row.get('العنوان', ''))).strip(),
                                city=str(row.get('city', row.get('المدينة', ''))).strip(),
                                region=str(row.get('region', row.get('المنطقة', ''))).strip(),
                                postal_code=str(row.get('postal_code', row.get('الرمز البريدي', ''))).strip(),
                                phone=str(row.get('phone', row.get('رقم الهاتف', ''))).strip(),
                                email=str(row.get('email', row.get('البريد الإلكتروني', ''))).strip(),
                            )
                            
                            capacity = row.get('capacity', row.get('السعة الاستيعابية', 0))
                            if pd.notna(capacity):
                                try:
                                    branch.capacity = int(capacity)
                                except:
                                    branch.capacity = 0
                            
                            opening_date_value = row.get('opening_date', row.get('تاريخ الافتتاح', None))
                            if pd.notna(opening_date_value) and opening_date_value != '':
                                try:
                                    if isinstance(opening_date_value, str):
                                        branch.opening_date = parse_date(opening_date_value)
                                    else:
                                        branch.opening_date = opening_date_value
                                except:
                                    branch.opening_date = None
                            
                            # أيام العمل
                            working_days_str = str(row.get('working_days', row.get('أيام العمل', ''))).strip()
                            if working_days_str and working_days_str != 'nan':
                                days_map = {
                                    'السبت': 'saturday', 'saturday': 'saturday',
                                    'الأحد': 'sunday', 'sunday': 'sunday',
                                    'الاثنين': 'monday', 'monday': 'monday',
                                    'الثلاثاء': 'tuesday', 'tuesday': 'tuesday',
                                    'الأربعاء': 'wednesday', 'wednesday': 'wednesday',
                                    'الخميس': 'thursday', 'thursday': 'thursday',
                                    'الجمعة': 'friday', 'friday': 'friday',
                                }
                                working_days = []
                                for day in working_days_str.split(','):
                                    day = day.strip()
                                    if day in days_map:
                                        working_days.append(days_map[day])
                                branch.working_days = working_days
                            
                            branch.description = str(row.get('description', row.get('الوصف', ''))).strip()
                            branch.notes = str(row.get('notes', row.get('ملاحظات', ''))).strip()
                            branch.save()
                            
                            # إنشاء الشفتات
                            branch.shifts.all().delete()
                            
                            # إنشاء 4 شفتات للأسبوع كحد أقصى (حسب طلب العميل)
                            week_days = [d for d in branch.working_days if d != 'friday']
                            
                            for i in range(1, 5):
                                shift_start = str(row.get(f'shift{i}_start', row.get(f'وقت بداية الشفت {i}', ''))).strip()
                                shift_end = str(row.get(f'shift{i}_end', row.get(f'وقت نهاية الشفت {i}', ''))).strip()
                                
                                if shift_start and shift_end and shift_start != 'nan' and shift_end != 'nan':
                                    try:
                                        start_time = parse_time(shift_start)
                                        end_time = parse_time(shift_end)
                                        if week_days:
                                            BranchShift.objects.create(
                                                branch=branch,
                                                name=f'الشفت {i}',
                                                start_time=start_time,
                                                end_time=end_time,
                                                days=week_days,
                                                is_active=True
                                            )
                                    except Exception as e:
                                        print(f"Error creating shift {i}: {e}")
                                        pass

                            # شفت الجمعة
                            friday_start = str(row.get('friday_start', row.get('وقت بداية دوام الجمعة', ''))).strip()
                            friday_end = str(row.get('friday_end', row.get('وقت نهاية دوام الجمعة', ''))).strip()
                            
                            if friday_start and friday_end and friday_start != 'nan' and friday_end != 'nan':
                                try:
                                    start_time = parse_time(friday_start)
                                    end_time = parse_time(friday_end)
                                    
                                    if 'friday' in branch.working_days:
                                        BranchShift.objects.create(
                                            branch=branch,
                                            name='شفت الجمعة',
                                            start_time=start_time,
                                            end_time=end_time,
                                            days=['friday'],
                                            is_active=True
                                        )
                                except Exception as e:
                                    print(f"Error creating friday shift: {e}")
                                    pass
                            
                            created_count += 1
                        else:
                            if not update_existing:
                                errors.append(f'الصف {index + 2}: الفرع {code} موجود بالفعل (فعّل خيار "تحديث المعارض الموجودة" لتحديثه)')
                            else:
                                errors.append(f'الصف {index + 2}: الفرع {code} موجود ولكن لم يتم تحديثه')
                    
                    except Exception as e:
                        errors.append(f'الصف {index + 2}: {str(e)}')
                
                # رسائل النتائج
                if created_count > 0:
                    messages.success(request, f'تم إنشاء {created_count} فرع جديد')
                if updated_count > 0:
                    messages.success(request, f'تم تحديث {updated_count} فرع')
                if errors:
                    for error in errors[:5]:  # عرض أول 5 أخطاء فقط
                        messages.warning(request, error)
                    if len(errors) > 5:
                        messages.warning(request, f'و {len(errors) - 5} أخطاء أخرى...')
                
                return redirect('branches:list')
                
            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء استيراد الملف: {str(e)}')
                print(f"Error in branch_import_view: {e}")
    else:
        form = BranchImportForm()
    
    context = {
        'form': form,
        'title': 'استيراد المعارض'
    }
    
    return render(request, 'branches/import.html', context)


@login_required
def download_branch_sample_file(request):
    """تحميل ملف Excel نموذجي لاستيراد المعارض"""
    import pandas as pd
    from django.http import HttpResponse
    
    # إنشاء بيانات نموذجية
    sample_data = {
        'اسم الفرع': ['فرع الرياض', 'فرع جدة', 'فرع الدمام'],
        'كود الفرع': ['1001', '2001', '3001'],
        'نوع الفرع': ['branch', 'branch', 'branch'],
        'فئة الفرع': ['A', 'B', 'C'],
        'الحالة': ['active', 'active', 'active'],
        'العنوان': ['شارع الملك فهد، الرياض', 'شارع التحلية، جدة', 'شارع الكورنيش، الدمام'],
        'المدينة': ['الرياض', 'جدة', 'الدمام'],
        'المنطقة': ['center', 'west', 'east'],
        'السعة الاستيعابية': [50, 40, 30],
        'أيام العمل': ['السبت, الأحد, الاثنين, الثلاثاء, الأربعاء, الخميس, الجمعة', 'السبت, الأحد, الاثنين, الثلاثاء, الأربعاء, الخميس, الجمعة', 'السبت, الأحد, الاثنين, الثلاثاء, الأربعاء, الخميس'],
        'وقت بداية الشفت 1': ['08:00', '09:00', '08:00'],
        'وقت نهاية الشفت 1': ['12:00', '13:00', '16:00'],
        'وقت بداية الشفت 2': ['16:00', '17:00', ''],
        'وقت نهاية الشفت 2': ['21:00', '21:00', ''],
        'وقت بداية الشفت 3': ['', '', ''],
        'وقت نهاية الشفت 3': ['', '', ''],
        'وقت بداية الشفت 4': ['', '', ''],
        'وقت نهاية الشفت 4': ['', '', ''],
        'وقت بداية دوام الجمعة': ['16:00', '16:00', ''],
        'وقت نهاية دوام الجمعة': ['21:00', '21:00', ''],
    }
    
    # إنشاء DataFrame
    df = pd.DataFrame(sample_data)
    
    # إنشاء ملف Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="sample_branches.xlsx"'
    
    # كتابة DataFrame إلى Excel
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='المعارض')
    
    return response