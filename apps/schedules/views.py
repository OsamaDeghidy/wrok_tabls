from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Schedule, ScheduleEntry
from .forms import ScheduleForm, ScheduleEntryForm
from apps.branches.models import Branch, BranchShift
from apps.leaves.models import LeaveRequest
from .api_views import (
    branch_info_api, 
    employees_api, 
    branch_shifts_api, 
    leave_conflicts_api, 
    create_schedule_api,
    save_schedule_entries_api
)


@login_required
def schedule_list_view(request):
    """قائمة الجداول التشغيلية"""
    
    # الفلاتر
    branch_filter = request.GET.get('branch')
    status_filter = request.GET.get('status')
    schedule_type_filter = request.GET.get('schedule_type')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # بناء الاستعلام
    schedules = Schedule.objects.select_related('branch', 'created_by').prefetch_related('entries')
    
    if branch_filter:
        schedules = schedules.filter(branch_id=branch_filter)
    
    if status_filter:
        schedules = schedules.filter(status=status_filter)
    
    if schedule_type_filter:
        schedules = schedules.filter(schedule_type=schedule_type_filter)
    
    if date_from:
        schedules = schedules.filter(start_date__gte=date_from)
    
    if date_to:
        schedules = schedules.filter(end_date__lte=date_to)
    
    # التحقق من الصلاحيات
    if not request.user.is_superuser and hasattr(request.user, 'profile'):
        user_role = request.user.profile.role
        if user_role == 'branch_manager':
            # مدير الفرع يرى جداول فرعه فقط
            if hasattr(request.user.profile, 'branch') and request.user.profile.branch:
                schedules = schedules.filter(branch=request.user.profile.branch)
            else:
                schedules = schedules.none()
        elif user_role == 'employee':
            # الموظف يرى جداول فرعه فقط
            if hasattr(request.user.profile, 'branch') and request.user.profile.branch:
                schedules = schedules.filter(branch=request.user.profile.branch)
            else:
                schedules = schedules.none()
        elif user_role == 'region_manager':
            # مدير المنطقة يرى جداول الفروع التابعة لمنطقته فقط
            if hasattr(request.user.profile, 'region') and request.user.profile.region:
                schedules = schedules.filter(branch__region=request.user.profile.region)
            else:
                schedules = schedules.none()
    
    # ترتيب النتائج
    schedules = schedules.order_by('-created_at')
    
    # التصفح
    paginator = Paginator(schedules, 20)
    page_number = request.GET.get('page')
    schedules_page = paginator.get_page(page_number)
    
    # الإحصائيات
    stats = {
        'total': Schedule.objects.count(),
        'draft': Schedule.objects.filter(status='draft').count(),
        'pending': Schedule.objects.filter(status__startswith='pending').count(),
        'approved': Schedule.objects.filter(status='approved').count(),
        'active': Schedule.objects.filter(status='active').count(),
    }
    
    # البيانات للفلاتر
    branches = Branch.objects.all()
    
    context = {
        'schedules': schedules_page,
        'stats': stats,
        'branches': branches,
        'schedule_types': Schedule.TYPE_CHOICES,
        'status_choices': Schedule.STATUS_CHOICES,
        'current_filters': {
            'branch': branch_filter,
            'status': status_filter,
            'schedule_type': schedule_type_filter,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    
    return render(request, 'schedules/list.html', context)


@login_required
def schedule_create_view(request):
    """إنشاء جدول تشغيلي جديد"""
    
    # التحقق من الصلاحيات
    if not request.user.is_superuser and hasattr(request.user, 'profile'):
        user_role = request.user.profile.role
        if user_role not in ['branch_manager', 'coordinator', 'region_manager', 'operations_manager', 'admin_manager', 'super_admin']:
            messages.error(request, 'ليس لديك صلاحية لإنشاء جداول تشغيلية')
            return redirect('schedules:list')
    
    if request.method == 'POST':
        form = ScheduleForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                schedule = form.save(commit=False)
                schedule.created_by = request.user
                
                # التحقق من الصلاحيات للفرع
                if not request.user.is_superuser and hasattr(request.user, 'profile'):
                    user_role = request.user.profile.role
                    if user_role == 'branch_manager':
                        if hasattr(request.user.profile, 'branch') and request.user.profile.branch != schedule.branch:
                            messages.error(request, 'يمكنك إنشاء جداول لفرعك فقط')
                            return redirect('schedules:list')
                
                # التحقق من وجود جدول مشابه (اختياري - للتحذير فقط)
                existing_schedules = Schedule.objects.filter(
                    branch=schedule.branch,
                    start_date=schedule.start_date,
                    end_date=schedule.end_date
                ).exclude(status='draft')
                
                if existing_schedules.exists():
                    messages.warning(request, f'يوجد بالفعل {existing_schedules.count()} جدول نشط لنفس الفترة والفرع')
                
                schedule.save()
                messages.success(request, 'تم إنشاء الجدول التشغيلي بنجاح')
                return redirect('schedules:detail', schedule_id=schedule.id)
                
            except Exception as e:
                messages.error(request, f'حدث خطأ في إنشاء الجدول التشغيلي: {str(e)}')
                return render(request, 'schedules/create.html', {
                    'form': form,
                    'branches': Branch.objects.all(),
                    'schedule_types': Schedule.TYPE_CHOICES,
                })
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء في النموذج')
    else:
        form = ScheduleForm(user=request.user)
    
    # تحديد ما إذا كان مدير معرض (لقفل حقل الفرع في الـ template)
    is_branch_manager = (
        not request.user.is_superuser and
        hasattr(request.user, 'profile') and
        request.user.profile.role == 'branch_manager'
    )
    user_branch = None
    if is_branch_manager and hasattr(request.user, 'profile'):
        user_branch = request.user.profile.branch

    context = {
        'form': form,
        'branches': Branch.objects.all() if not is_branch_manager else (Branch.objects.filter(id=user_branch.id) if user_branch else Branch.objects.none()),
        'schedule_types': Schedule.TYPE_CHOICES,
        'is_branch_manager': is_branch_manager,
        'user_branch': user_branch,
    }
    
    return render(request, 'schedules/create_single.html', context)


@login_required
def schedule_detail_view(request, schedule_id):
    """تفاصيل الجدول التشغيلي"""
    
    schedule = get_object_or_404(Schedule, id=schedule_id)
    
    # التحقق من الصلاحيات
    if not request.user.is_superuser and hasattr(request.user, 'profile'):
        user_role = request.user.profile.role
        if user_role == 'branch_manager':
            if hasattr(request.user.profile, 'branch') and request.user.profile.branch != schedule.branch:
                messages.error(request, 'ليس لديك صلاحية لعرض هذا الجدول')
                return redirect('schedules:list')
        elif user_role == 'employee':
            if hasattr(request.user.profile, 'branch') and request.user.profile.branch != schedule.branch:
                messages.error(request, 'ليس لديك صلاحية لعرض هذا الجدول')
                return redirect('schedules:list')
    
    # إحصائيات الجدول
    entries = schedule.entries.select_related('employee', 'shift').order_by('date', 'start_time')
    
    # تجميع الإدخالات حسب التاريخ (البدء بجميع أيام الجدول)
    entries_by_date = {}
    from datetime import timedelta, datetime
    current_date = schedule.start_date
    while current_date <= schedule.end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        entries_by_date[date_str] = []
        current_date += timedelta(days=1)
        
    for entry in entries:
        date_str = entry.date.strftime('%Y-%m-%d')
        if date_str in entries_by_date:
            entries_by_date[date_str].append(entry)
    
    # إحصائيات الموظفين
    employee_stats = {}
    for entry in entries:
        employee = entry.employee
        if employee.id not in employee_stats:
            profile = getattr(employee, 'profile', None)
            is_laborer = getattr(profile, 'is_laborer', False) if profile else False
            work_hours = getattr(profile, 'work_hours', 8) if profile else 8
            
            if is_laborer:
                required_hours = 0
            else:
                required_hours = 0
                current_date = schedule.start_date
                from datetime import timedelta
                while current_date <= schedule.end_date:
                    weekday = current_date.weekday()
                    if work_hours == 9:
                        if weekday not in [4, 5]:
                            required_hours += 9
                    elif work_hours == 85:
                        if weekday == 4:
                            required_hours += 5
                        elif weekday != 2:
                            required_hours += 8
                    else:
                        if weekday != 4:
                            required_hours += 8
                    current_date += timedelta(days=1)
            
            employee_stats[employee.id] = {
                'employee': employee,
                'total_hours': 0,
                'required_hours': required_hours,
                'hours_per_day': work_hours,
                'is_laborer': is_laborer,
                'days_count': 0,
                'entries': []
            }
        employee_stats[employee.id]['total_hours'] += float(entry.hours)
        employee_stats[employee.id]['days_count'] += 1
        employee_stats[employee.id]['entries'].append(entry)
    
    # حساب الإحصائيات العامة (باستثناء ساعات العمالة من متطلبات التغطية والعجز)
    total_hours = sum(stats['total_hours'] for stats in employee_stats.values())
    regular_total_hours = sum(stats['total_hours'] for stats in employee_stats.values() if not stats.get('is_laborer'))
    required_hours = schedule.calculate_required_hours()
    
    if required_hours == 0 or total_hours == 0:
        coverage_percentage = schedule.get_coverage_percentage_alternative()
    else:
        # نسبة التغطية تعتمد على ساعات الموظفين الأساسيين مقارنة بالمطلوب
        coverage_percentage = min(100.0, (regular_total_hours / required_hours) * 100) if required_hours > 0 else 100.0
    
    deficit = max(0.0, float(required_hours) - float(regular_total_hours))
    surplus = max(0.0, float(regular_total_hours) - float(required_hours))
    
    stats = {
        'total_entries': entries.count(),
        'unique_employees': len(employee_stats),
        'total_hours': total_hours,
        'regular_total_hours': regular_total_hours,
        'coverage_percentage': coverage_percentage,
        'required_hours': required_hours,
        'duration_days': schedule.get_duration_days(),
        'deficit': deficit,
        'surplus': surplus,
    }
    
    # حساب إحصائيات عمل الفرع يومياً
    branch_operating_stats = {}
    for date_str, day_entries in entries_by_date.items():
        if day_entries:
            # أبكر وقت بداية
            opening_time = min(e.start_time for e in day_entries)
            
            # تحديد آخر وقت نهاية
            # نتحقق من وجود نوبات مسائية (تنتهي في اليوم التالي)
            overnight_entries = [e for e in day_entries if e.end_time <= e.start_time]
            if overnight_entries:
                closing_time = max(e.end_time for e in overnight_entries)
                is_overnight = True
            else:
                closing_time = max(e.end_time for e in day_entries)
                is_overnight = False
            
            # حساب إجمالي الساعات من أول فتح لآخر إغلاق
            d1 = datetime.combine(datetime.today(), opening_time)
            d2 = datetime.combine(datetime.today(), closing_time)
            if is_overnight:
                d2 += timedelta(days=1)
            
            branch_operating_stats[date_str] = {
                'opening_time': opening_time,
                'closing_time': closing_time,
                'operating_hours': (d2 - d1).total_seconds() / 3600
            }
        else:
            branch_operating_stats[date_str] = None

    from apps.leaves.models import LeaveRequest
    branch_leaves = LeaveRequest.objects.filter(
        employee__profile__branch=schedule.branch,
        status='approved',
        start_date__lte=schedule.end_date,
        end_date__gte=schedule.start_date
    ).select_related('employee')

    context = {
        'schedule': schedule,
        'entries_by_date': entries_by_date,
        'employee_stats': employee_stats,
        'stats': stats,
        'branch_operating_stats': branch_operating_stats,
        'branch_leaves': branch_leaves,
    }
    
    return render(request, 'schedules/detail.html', context)


@login_required
def schedule_edit_view(request, schedule_id):
    """تعديل الجدول التشغيلي"""
    
    schedule = get_object_or_404(Schedule, id=schedule_id)
    
    # التحقق من الصلاحيات
    if not request.user.is_superuser and hasattr(request.user, 'profile'):
        user_role = request.user.profile.role
        if user_role == 'branch_manager':
            if hasattr(request.user.profile, 'branch') and request.user.profile.branch != schedule.branch:
                messages.error(request, 'ليس لديك صلاحية لتعديل هذا الجدول')
                return redirect('schedules:list')
        elif user_role not in ['coordinator', 'region_manager', 'operations_manager', 'admin_manager', 'super_admin']:
            messages.error(request, 'ليس لديك صلاحية لتعديل الجداول التشغيلية')
            return redirect('schedules:list')
    
    # لا يمكن تعديل الجداول المعتمدة أو المرفوضة
    if schedule.status in ['approved', 'rejected', 'active']:
        messages.error(request, 'لا يمكن تعديل الجداول المعتمدة أو المرفوضة')
        return redirect('schedules:detail', schedule_id=schedule.id)
    
    # استخدام النماذج الجديدة
    from .forms import ScheduleEditForm, ScheduleEntryEditForm
    
    if request.method == 'POST':
        form = ScheduleEditForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث الجدول التشغيلي بنجاح')
            return redirect('schedules:detail', schedule_id=schedule.id)
        else:
            messages.error(request, 'حدث خطأ في تحديث الجدول التشغيلي')
    else:
        form = ScheduleEditForm(instance=schedule)
    
    # جلب بيانات التوزيعات الموجودة
    entries = schedule.entries.select_related('employee', 'shift').all()
    
    # تجميع التوزيعات حسب التاريخ
    entries_by_date = {}
    for entry in entries:
        date_str = entry.date.strftime('%Y-%m-%d')
        if date_str not in entries_by_date:
            entries_by_date[date_str] = []
        entries_by_date[date_str].append(entry)
    
    # إحصائيات الموظفين
    employee_stats = {}
    for entry in entries:
        employee = entry.employee
        if employee.id not in employee_stats:
            required_hours_per_day = getattr(employee.profile, 'hours_per_day', 8)
            total_days = schedule.get_duration_days()
            required_hours = required_hours_per_day * total_days
            
            employee_stats[employee.id] = {
                'employee': employee,
                'total_hours': 0,
                'required_hours': required_hours,
                'hours_per_day': required_hours_per_day,
                'days_count': 0,
                'entries': []
            }
        employee_stats[employee.id]['total_hours'] += float(entry.hours)
        employee_stats[employee.id]['days_count'] += 1
        employee_stats[employee.id]['entries'].append(entry)
    
    # حساب الإحصائيات العامة
    total_hours = sum(stats['total_hours'] for stats in employee_stats.values())
    required_hours = schedule.calculate_required_hours()
    
    if required_hours == 0 or total_hours == 0:
        coverage_percentage = schedule.get_coverage_percentage_alternative()
    else:
        coverage_percentage = schedule.get_coverage_percentage()
    
    stats = {
        'total_entries': entries.count(),
        'unique_employees': len(employee_stats),
        'total_hours': total_hours,
        'coverage_percentage': coverage_percentage,
        'required_hours': required_hours,
        'duration_days': schedule.get_duration_days(),
        'deficit': max(0, required_hours - total_hours),
        'surplus': max(0, total_hours - required_hours),
    }
    
    # إنشاء نماذج التوزيعات
    entry_forms = []
    for entry in entries:
        entry_form = ScheduleEntryEditForm(instance=entry, schedule=schedule)
        entry_forms.append(entry_form)
    
    # نموذج فارغ لإضافة توزيعات جديدة
    new_entry_form = ScheduleEntryEditForm(schedule=schedule)
    
    # جلب بيانات الفرع
    branch = schedule.branch
    shifts = BranchShift.objects.filter(branch=branch, is_active=True)
    employees = User.objects.filter(profile__branch=branch).select_related('profile')
    
    # تحويل الشفتات لبيانات JSON للاستخدام في JS
    shifts_data = []
    for shift in shifts:
        shifts_data.append({
            'id': shift.id,
            'name': shift.name,
            'start_time': shift.start_time.strftime('%H:%M'),
            'end_time': shift.end_time.strftime('%H:%M'),
            'duration': str(shift.get_duration()),
        })

    # تحويل التوزيعات الموجودة لبيانات JSON للاستخدام في JS
    existing_entries_data = {}
    for date_str, date_entries in entries_by_date.items():
        existing_entries_data[date_str] = {
            'shifts': {},
            'employees': list(set(e.employee.id for e in date_entries)),
            'coverage': 0 # سيتم حسابه في JS
        }
        for entry in date_entries:
            shift_id = str(entry.shift.id)
            if shift_id not in existing_entries_data[date_str]['shifts']:
                existing_entries_data[date_str]['shifts'][shift_id] = []
            existing_entries_data[date_str]['shifts'][shift_id].append(entry.employee.id)

    context = {
        'form': form,
        'schedule': schedule,
        'entries': entries,
        'entries_by_date': entries_by_date,
        'employee_stats': employee_stats,
        'stats': stats,
        'branches': Branch.objects.all(),
        'schedule_types': Schedule.TYPE_CHOICES,
        'entry_forms': entry_forms,
        'new_entry_form': new_entry_form,
        'branch_shifts': shifts_data,
        'branch_employees': employees,
        'existing_entries_json': existing_entries_data,
        'selected_employee_ids': list(schedule.entries.values_list('employee_id', flat=True).distinct()),
    }
    
    return render(request, 'schedules/edit.html', context)


@login_required
def schedule_approve_view(request, schedule_id):
    """اعتماد الجدول التشغيلي"""
    
    schedule = get_object_or_404(Schedule, id=schedule_id)
    
    # التحقق من الصلاحيات
    if not request.user.is_superuser and hasattr(request.user, 'profile'):
        user_role = request.user.profile.role
        if user_role not in ['coordinator', 'region_manager', 'operations_manager', 'admin_manager', 'super_admin']:
            messages.error(request, 'ليس لديك صلاحية لاعتماد الجداول')
            return redirect('schedules:detail', schedule_id=schedule.id)
    
    # التحقق من الحالة الحالية
    current_status = schedule.status
    next_status = None
    
    if user_role == 'region_manager' and current_status == 'pending_region_manager':
        next_status = 'pending_coordinator'
    elif user_role == 'coordinator' and current_status == 'pending_coordinator':
        next_status = 'pending_operations_manager'
    elif user_role == 'operations_manager' and current_status == 'pending_operations_manager':
        next_status = 'pending_admin_manager'
    elif user_role in ['admin_manager', 'super_admin'] and current_status == 'pending_admin_manager':
        next_status = 'approved'
    
    if next_status:
        schedule.status = next_status
        schedule.save()
        if next_status == 'approved':
            from apps.schedules.utils import send_schedule_approval_emails
            send_schedule_approval_emails(schedule)
        messages.success(request, f'تم اعتماد الجدول التشغيلي بنجاح')
    else:
        messages.error(request, 'لا يمكنك اعتماد هذا الجدول في الوقت الحالي')
    
    return redirect('schedules:detail', schedule_id=schedule.id)


@login_required
def schedule_reject_view(request, schedule_id):
    """رفض الجدول التشغيلي"""
    
    schedule = get_object_or_404(Schedule, id=schedule_id)
    
    # التحقق من الصلاحيات
    if not request.user.is_superuser and hasattr(request.user, 'profile'):
        user_role = request.user.profile.role
        if user_role not in ['coordinator', 'region_manager', 'operations_manager', 'admin_manager', 'super_admin']:
            messages.error(request, 'ليس لديك صلاحية لرفض الجداول')
            return redirect('schedules:detail', schedule_id=schedule.id)
    
    # التحقق من أن الجدول في حالة انتظار موافقة
    if not schedule.status.startswith('pending'):
        messages.error(request, 'لا يمكن رفض هذا الجدول في الوقت الحالي')
        return redirect('schedules:detail', schedule_id=schedule.id)
    
    schedule.status = 'rejected'
    schedule.save()
    messages.success(request, 'تم رفض الجدول التشغيلي')
    
    return redirect('schedules:detail', schedule_id=schedule.id)


@login_required
def schedule_activate_view(request, schedule_id):
    """تفعيل الجدول التشغيلي"""
    
    schedule = get_object_or_404(Schedule, id=schedule_id)
    
    # التحقق من الصلاحيات
    if not request.user.is_superuser and hasattr(request.user, 'profile'):
        user_role = request.user.profile.role
        if user_role not in ['coordinator', 'region_manager', 'operations_manager', 'admin_manager', 'super_admin']:
            messages.error(request, 'ليس لديك صلاحية لتفعيل الجداول')
            return redirect('schedules:detail', schedule_id=schedule.id)
    
    # التحقق من أن الجدول معتمد
    if schedule.status != 'approved':
        messages.error(request, 'يمكن تفعيل الجداول المعتمدة فقط')
        return redirect('schedules:detail', schedule_id=schedule.id)
    
    # إلغاء تفعيل الجداول النشطة الأخرى لنفس الفرع في نفس الفترة
    active_schedules = Schedule.objects.filter(
        branch=schedule.branch,
        status='active',
        start_date__lte=schedule.end_date,
        end_date__gte=schedule.start_date
    ).exclude(id=schedule.id)
    
    for active_schedule in active_schedules:
        active_schedule.status = 'completed'
        active_schedule.save()
    
    schedule.status = 'active'
    schedule.save()
    messages.success(request, 'تم تفعيل الجدول التشغيلي بنجاح')
    
    return redirect('schedules:detail', schedule_id=schedule.id)


@login_required
def schedule_complete_view(request, schedule_id):
    """إكمال الجدول التشغيلي"""
    schedule = get_object_or_404(Schedule, id=schedule_id)
    # التحقق من الصلاحيات
    if not request.user.is_superuser and hasattr(request.user, 'profile'):
        user_role = request.user.profile.role
        if user_role not in ['coordinator', 'region_manager', 'operations_manager', 'admin_manager', 'super_admin']:
            messages.error(request, 'ليس لديك صلاحية لإكمال الجداول')
            return redirect('schedules:detail', schedule_id=schedule.id)
    # يجب أن يكون الجدول في حالة نشطة ليتم إكماله
    if schedule.status != 'active':
        messages.error(request, 'يمكن إكمال الجداول النشطة فقط')
        return redirect('schedules:detail', schedule_id=schedule.id)
    schedule.status = 'completed'
    schedule.save()
    messages.success(request, 'تم إكمال الجدول التشغيلي بنجاح')
    return redirect('schedules:detail', schedule_id=schedule.id)

@login_required
def schedule_delete_view(request, schedule_id):
    """حذف مسودة الجدول التشغيلي"""
    from django.http import JsonResponse
    schedule = get_object_or_404(Schedule, id=schedule_id)
    
    # التحقق من الصلاحيات
    if not request.user.is_superuser and hasattr(request.user, 'profile'):
        user_role = request.user.profile.role
        if user_role == 'branch_manager':
            if hasattr(request.user.profile, 'branch') and request.user.profile.branch != schedule.branch:
                return JsonResponse({'error': 'ليس لديك صلاحية لحذف هذا الجدول'}, status=403)
        elif user_role not in ['coordinator', 'region_manager', 'operations_manager', 'admin_manager', 'super_admin']:
            return JsonResponse({'error': 'ليس لديك صلاحية لحذف الجداول'}, status=403)
            
    # التحقق من أن الجدول في حالة مسودة
    if schedule.status != 'draft':
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'يمكن حذف الجداول التي في حالة مسودة فقط'}, status=400)
        messages.error(request, 'يمكن حذف الجداول التي في حالة مسودة فقط')
        return redirect('schedules:list')
        
    if request.method == 'POST':
        schedule.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'success': True, 'message': 'تم حذف الجدول بنجاح'})
        messages.success(request, 'تم حذف المسودة بنجاح')
        return redirect('schedules:list')
        
    return JsonResponse({'error': 'طريقة الطلب غير مسموحة'}, status=405)

@login_required
def schedule_entries_view(request, schedule_id):
    """إدارة إدخالات الجدول التشغيلي"""
    
    schedule = get_object_or_404(Schedule, id=schedule_id)
    
    # التحقق من الصلاحيات
    if not request.user.is_superuser and hasattr(request.user, 'profile'):
        user_role = request.user.profile.role
        if user_role == 'branch_manager':
            if hasattr(request.user.profile, 'branch') and request.user.profile.branch != schedule.branch:
                messages.error(request, 'ليس لديك صلاحية لإدارة هذا الجدول')
                return redirect('schedules:list')
        elif user_role not in ['coordinator', 'region_manager', 'operations_manager', 'admin_manager', 'super_admin']:
            messages.error(request, 'ليس لديك صلاحية لإدارة الجداول التشغيلية')
            return redirect('schedules:list')
    
    # لا يمكن تعديل إدخالات الجداول المعتمدة أو المرفوضة
    if schedule.status in ['approved', 'rejected', 'active']:
        messages.error(request, 'لا يمكن تعديل إدخالات الجداول المعتمدة أو المرفوضة')
        return redirect('schedules:detail', schedule_id=schedule.id)
    
    if request.method == 'POST':
        # معالجة إضافة/تعديل/حذف الإدخالات
        action = request.POST.get('action')
        
        if action == 'add_entry':
            form = ScheduleEntryForm(request.POST, schedule=schedule)
            if form.is_valid():
                entry = form.save(commit=False)
                entry.schedule = schedule
                entry.save()
                messages.success(request, 'تم إضافة الإدخال بنجاح')
            else:
                messages.error(request, 'حدث خطأ في إضافة الإدخال')
        
        elif action == 'update_entry':
            entry_id = request.POST.get('entry_id')
            entry = get_object_or_404(ScheduleEntry, id=entry_id, schedule=schedule)
            form = ScheduleEntryForm(request.POST, instance=entry, schedule=schedule)
            if form.is_valid():
                form.save()
                messages.success(request, 'تم تحديث الإدخال بنجاح')
            else:
                messages.error(request, 'حدث خطأ في تحديث الإدخال')
        
        elif action == 'delete_entry':
            entry_id = request.POST.get('entry_id')
            entry = get_object_or_404(ScheduleEntry, id=entry_id, schedule=schedule)
            entry.delete()
            messages.success(request, 'تم حذف الإدخال بنجاح')
        
        return redirect('schedules:entries', schedule_id=schedule.id)
    
    # الحصول على الإدخالات
    entries = schedule.entries.select_related('employee', 'shift').order_by('date', 'start_time')
    
    # الحصول على الموظفين المتاحين
    employees = User.objects.filter(profile__branch=schedule.branch).select_related('profile')
    
    # الحصول على الشفتات المتاحة
    shifts = BranchShift.objects.filter(branch=schedule.branch, is_active=True)
    
    context = {
        'schedule': schedule,
        'entries': entries,
        'employees': employees,
        'shifts': shifts,
        'entry_form': ScheduleEntryForm(schedule=schedule),
    }
    
    return render(request, 'schedules/entries.html', context)


@login_required
def schedule_analytics_view(request, schedule_id):
    """تحليلات الجدول التشغيلي"""
    
    schedule = get_object_or_404(Schedule, id=schedule_id)
    
    # التحقق من الصلاحيات
    if not request.user.is_superuser and hasattr(request.user, 'profile'):
        user_role = request.user.profile.role
        if user_role == 'branch_manager':
            if hasattr(request.user.profile, 'branch') and request.user.profile.branch != schedule.branch:
                messages.error(request, 'ليس لديك صلاحية لعرض تحليلات هذا الجدول')
                return redirect('schedules:list')
        elif user_role not in ['coordinator', 'region_manager', 'operations_manager', 'admin_manager', 'super_admin']:
            messages.error(request, 'ليس لديك صلاحية لعرض تحليلات الجداول')
            return redirect('schedules:list')
    
    # حساب التحليلات
    entries = schedule.entries.select_related('employee', 'shift')
    
    # تحليلات الموظفين
    employee_analytics = {}
    for entry in entries:
        employee = entry.employee
        if employee.id not in employee_analytics:
            employee_analytics[employee.id] = {
                'employee': employee,
                'total_hours': 0,
                'days_count': 0,
                'shifts_count': 0,
                'entries': []
            }
        employee_analytics[employee.id]['total_hours'] += float(entry.hours)
        employee_analytics[employee.id]['days_count'] += 1
        employee_analytics[employee.id]['shifts_count'] += 1
        employee_analytics[employee.id]['entries'].append(entry)
    
    # تحليلات الشفتات
    shift_analytics = {}
    for entry in entries:
        shift = entry.shift
        if shift.id not in shift_analytics:
            shift_analytics[shift.id] = {
                'shift': shift,
                'total_hours': 0,
                'entries_count': 0,
                'employees_count': 0,
                'employees': set()
            }
        shift_analytics[shift.id]['total_hours'] += float(entry.hours)
        shift_analytics[shift.id]['entries_count'] += 1
        shift_analytics[shift.id]['employees'].add(entry.employee.id)
    
    # تحديث عدد الموظفين الفريدين لكل شفت
    for shift_data in shift_analytics.values():
        shift_data['employees_count'] = len(shift_data['employees'])
        del shift_data['employees']  # إزالة set من البيانات المرسلة
    
    # تحليلات التغطية اليومية
    coverage_analytics = {}
    current_date = schedule.start_date
    while current_date <= schedule.end_date:
        date_entries = entries.filter(date=current_date)
        if date_entries.exists():
            total_hours = sum(float(entry.hours) for entry in date_entries)
            unique_employees = date_entries.values('employee').distinct().count()
            coverage_analytics[current_date.strftime('%Y-%m-%d')] = {
                'date': current_date,
                'total_hours': total_hours,
                'unique_employees': unique_employees,
                'entries_count': date_entries.count()
            }
        current_date += timedelta(days=1)
    
    context = {
        'schedule': schedule,
        'employee_analytics': employee_analytics,
        'shift_analytics': shift_analytics,
        'coverage_analytics': coverage_analytics,
    }
    
    return render(request, 'schedules/analytics.html', context)


@login_required
def schedule_export_view(request, schedule_id):
    """تصدير الجدول التشغيلي إلى Excel (عادي أو ساب SAP)"""
    import pandas as pd
    from django.http import HttpResponse
    from collections import Counter
    
    schedule = get_object_or_404(Schedule, id=schedule_id)
    
    # التحقق من الصلاحيات
    if not request.user.is_superuser and hasattr(request.user, 'profile'):
        user_role = request.user.profile.role
        if user_role == 'branch_manager' and hasattr(request.user.profile, 'branch') and request.user.profile.branch != schedule.branch:
            messages.error(request, 'ليس لديك صلاحية لتصدير هذا الجدول')
            return redirect('schedules:list')
        elif user_role == 'employee' and hasattr(request.user.profile, 'branch') and request.user.profile.branch != schedule.branch:
            messages.error(request, 'ليس لديك صلاحية لتصدير هذا الجدول')
            return redirect('schedules:list')
            
    export_type = request.GET.get('type', 'standard')
    entries = schedule.entries.select_related('employee__profile', 'shift').order_by('employee__first_name', 'date')
    
    # تصدير ساب SAP (سواء شامل أو موظفين فقط أو عمالة فقط)
    if export_type.startswith('sap'):
        # تحديد الفئة المستهدفة
        if export_type == 'sap_staff':
            # استبعاد العمالة
            target_entries = [e for e in entries if not (getattr(e.employee.profile, 'is_laborer', False) or e.employee.username.startswith('98979'))]
            filename_prefix = f"SAP_Staff_Schedule_{schedule.branch.name}_{schedule.start_date}"
        elif export_type == 'sap_labor':
            # العمالة فقط
            target_entries = [e for e in entries if getattr(e.employee.profile, 'is_laborer', False) or e.employee.username.startswith('98979')]
            filename_prefix = f"SAP_Labor_Schedule_{schedule.branch.name}_{schedule.start_date}"
        else:
            target_entries = list(entries)
            filename_prefix = f"SAP_Full_Schedule_{schedule.branch.name}_{schedule.start_date}"

        # الحصول على جميع الموظفين المرتبطين بالجدول
        all_emp_ids = list(schedule.entries.values_list('employee_id', flat=True).distinct())
        if not all_emp_ids:
            # في حال عدم وجود إدخالات بعد، جلب موظفي الفرع
            from apps.branches.models import Branch
            all_emp_ids = list(User.objects.filter(profile__branch=schedule.branch).values_list('id', flat=True))

        all_employees = User.objects.filter(id__in=all_emp_ids).select_related('profile').order_by('first_name', 'username')

        # تصفية حسب الفئة
        if export_type == 'sap_staff':
            target_employees = [emp for emp in all_employees if not (getattr(emp.profile, 'is_laborer', False) or emp.username.startswith('98979'))]
            filename_prefix = f"SAP_Staff_Schedule_{schedule.branch.name}_{schedule.start_date}"
        elif export_type == 'sap_labor':
            target_employees = [emp for emp in all_employees if getattr(emp.profile, 'is_laborer', False) or emp.username.startswith('98979')]
            filename_prefix = f"SAP_Labor_Schedule_{schedule.branch.name}_{schedule.start_date}"
        else:
            target_employees = list(all_employees)
            filename_prefix = f"SAP_Full_Schedule_{schedule.branch.name}_{schedule.start_date}"

        day_abbr_map = {0: 'MON', 1: 'TUE', 2: 'WED', 3: 'THU', 4: 'FRI', 5: 'SAT', 6: 'SUN'}
        sap_rows = []

        # تصدير تفصيلي يومي كامل لجميع أيام الفترة لكل موظف
        for employee in target_employees:
            profile = getattr(employee, 'profile', None)
            emp_no = profile.job_id if (profile and profile.job_id) else employee.username
            emp_entries = [e for e in entries if e.employee_id == employee.id]

            current_date = schedule.start_date
            while current_date <= schedule.end_date:
                date_str = current_date.strftime('%d.%m.%Y')
                weekday = current_date.weekday()
                day_code = day_abbr_map.get(weekday, 'MON')

                day_entries = [e for e in emp_entries if e.date == current_date]

                if day_entries:
                    if len(day_entries) == 1:
                        e = day_entries[0]
                        in_time_1 = f"{e.start_time.hour}:{e.start_time.minute:02d}" if e.start_time else ""
                        out_time_1 = f"{e.end_time.hour}:{e.end_time.minute:02d}" if e.end_time else ""
                        in_time_2 = ""
                        out_time_2 = ""
                        end_nxt_dy = "X" if (e.start_time and e.end_time and e.end_time < e.start_time) else ""
                    else:
                        # شفت منقسم (أكثر من وردية في نفس اليوم)
                        sorted_e = sorted(day_entries, key=lambda x: x.start_time or datetime.min.time())
                        e1, e2 = sorted_e[0], sorted_e[1]
                        in_time_1 = f"{e1.start_time.hour}:{e1.start_time.minute:02d}" if e1.start_time else ""
                        out_time_1 = f"{e1.end_time.hour}:{e1.end_time.minute:02d}" if e1.end_time else ""
                        in_time_2 = f"{e2.start_time.hour}:{e2.start_time.minute:02d}" if e2.start_time else ""
                        out_time_2 = f"{e2.end_time.hour}:{e2.end_time.minute:02d}" if e2.end_time else ""
                        end_nxt_dy = "X" if (e2.start_time and e2.end_time and e2.end_time < e2.start_time) else ""

                    rst_day = ""
                    rst_day_2 = ""
                else:
                    # يوم راحة للموظف (Rest Day)
                    in_time_1 = ""
                    out_time_1 = ""
                    in_time_2 = ""
                    out_time_2 = ""
                    end_nxt_dy = ""
                    rst_day = day_code
                    rst_day_2 = ""

                sap_rows.append({
                    'Emp No': emp_no,
                    'Start Dt': date_str,
                    'End Dt': date_str,
                    'In Time 1': in_time_1,
                    'Out Time1': out_time_1,
                    'In Time 2': in_time_2,
                    'Out Time2': out_time_2,
                    'Rst Day': rst_day,
                    'End Nxt Dy': end_nxt_dy,
                    'Rst Day 2': rst_day_2,
                    'REST DAY3': "",
                })

                current_date += timedelta(days=1)

        df = pd.DataFrame(sap_rows, columns=[
            'Emp No', 'Start Dt', 'End Dt', 'In Time 1', 'Out Time1',
            'In Time 2', 'Out Time2', 'Rst Day', 'End Nxt Dy', 'Rst Day 2', 'REST DAY3'
        ])

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{filename_prefix}.xlsx"'
        
        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='SAP_Schedule')
            
        return response

    # التصدير العادي التفصيلي
    data = []
    for entry in entries:
        employee_name = entry.employee.get_full_name() or entry.employee.username
        job_id = entry.employee.profile.job_id if hasattr(entry.employee, 'profile') else ''
        is_laborer = getattr(entry.employee.profile, 'is_laborer', False) if hasattr(entry.employee, 'profile') else False
        
        data.append({
            'الموظف': employee_name,
            'الرقم الوظيفي': job_id,
            'الفئة': 'عمالة' if is_laborer else 'موظف',
            'التاريخ': entry.date.strftime('%Y-%m-%d'),
            'اليوم': entry.date.strftime('%A'),
            'الشفت': entry.shift.name if entry.shift else '-',
            'وقت الحضور': entry.start_time.strftime('%H:%M') if entry.start_time else '-',
            'وقت الانصراف': entry.end_time.strftime('%H:%M') if entry.end_time else '-',
            'عدد الساعات': entry.hours,
            'ملاحظات': entry.notes or ''
        })
        
    df = pd.DataFrame(data)
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="schedule_{schedule.id}_{schedule.branch.name}.xlsx"'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='الجدول التشغيلي')
        
    return response
