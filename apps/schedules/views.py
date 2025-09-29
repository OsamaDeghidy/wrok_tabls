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
        form = ScheduleForm(request.POST)
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
        form = ScheduleForm()
        
        # تحديد الفرع الافتراضي للمديرين
        if hasattr(request.user, 'profile') and request.user.profile.role == 'branch_manager':
            if hasattr(request.user.profile, 'branch') and request.user.profile.branch:
                form.fields['branch'].initial = request.user.profile.branch
    
    context = {
        'form': form,
        'branches': Branch.objects.all(),
        'schedule_types': Schedule.TYPE_CHOICES,
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
    
    # تجميع الإدخالات حسب التاريخ
    entries_by_date = {}
    for entry in entries:
        date_str = entry.date.strftime('%Y-%m-%d')
        if date_str not in entries_by_date:
            entries_by_date[date_str] = []
        entries_by_date[date_str].append(entry)
    
    # إنشاء أيام فارغة إذا لم تكن هناك إدخالات
    if not entries.exists():
        from datetime import timedelta
        current_date = schedule.start_date
        while current_date <= schedule.end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            entries_by_date[date_str] = []
            current_date += timedelta(days=1)
    
    # إحصائيات الموظفين
    employee_stats = {}
    for entry in entries:
        employee = entry.employee
        if employee.id not in employee_stats:
            # حساب الساعات المطلوبة للموظف
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
    
    # استخدام الحساب البديل إذا كان الحساب الأساسي لا يعطي نتائج منطقية
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
    }
    
    context = {
        'schedule': schedule,
        'entries_by_date': entries_by_date,
        'employee_stats': employee_stats,
        'stats': stats,
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
    }
    
    # إنشاء نماذج التوزيعات
    entry_forms = []
    for entry in entries:
        entry_form = ScheduleEntryEditForm(instance=entry, schedule=schedule)
        entry_forms.append(entry_form)
    
    # نموذج فارغ لإضافة توزيعات جديدة
    new_entry_form = ScheduleEntryEditForm(schedule=schedule)
    
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
    }
    
    return render(request, 'schedules/edit_simple.html', context)


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
    
    if user_role == 'coordinator' and current_status == 'pending_coordinator':
        next_status = 'pending_region_manager'
    elif user_role == 'region_manager' and current_status == 'pending_region_manager':
        next_status = 'pending_operations_manager'
    elif user_role == 'operations_manager' and current_status == 'pending_operations_manager':
        next_status = 'pending_admin_manager'
    elif user_role in ['admin_manager', 'super_admin'] and current_status == 'pending_admin_manager':
        next_status = 'approved'
    
    if next_status:
        schedule.status = next_status
        schedule.save()
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

