from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from apps.branches.models import Branch, BranchShift
from apps.leaves.models import LeaveRequest
from apps.users.models import UserProfile
from .models import Schedule, ScheduleEntry
import json
from datetime import datetime


@csrf_exempt
@require_http_methods(["GET"])
def branch_info_api(request, branch_id):
    """معلومات الفرع"""
    try:
        branch = get_object_or_404(Branch, id=branch_id)
        
        # حساب عدد الموظفين
        employees_count = User.objects.filter(profile__branch=branch).count()
        
        # حساب عدد الشفتات
        shifts_count = BranchShift.objects.filter(branch=branch, is_active=True).count()
        
        # حساب إجمالي ساعات العمل
        total_hours = 0
        for shift in BranchShift.objects.filter(branch=branch, is_active=True):
            total_hours += shift.get_duration()
        
        data = {
            'id': branch.id,
            'name': branch.name,
            'address': branch.address,
            'working_days': branch.working_days,
            'employees_count': employees_count,
            'shifts_count': shifts_count,
            'total_hours': total_hours,
        }
        
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def employees_api(request):
    """قائمة الموظفين للفرع"""
    try:
        branch_id = request.GET.get('branch')
        if not branch_id:
            return JsonResponse({'error': 'Branch ID required'}, status=400)
        
        branch = get_object_or_404(Branch, id=branch_id)
        employees = User.objects.filter(profile__branch=branch).select_related('profile')
        
        employees_data = []
        for employee in employees:
            try:
                profile = employee.profile
                employees_data.append({
                    'id': employee.id,
                    'full_name': employee.get_full_name() or employee.username,
                    'username': employee.username,
                    'role': profile.role,
                    'role_display': profile.get_role_display(),
                    'position': getattr(profile, 'position', 'موظف'),
                    'hours_per_day': getattr(profile, 'work_hours', 8),
                    'work_days': getattr(profile, 'work_days', 6 if getattr(profile, 'work_hours', 8) == 8 else 5),
                    'phone': getattr(profile, 'phone', ''),
                    'email': employee.email,
                })
            except Exception as e:
                print(f"Error processing employee {employee.id}: {e}")
                continue
        
        return JsonResponse({
            'success': True,
            'employees': employees_data,
            'count': len(employees_data)
        })
    except Exception as e:
        print(f"Error in employees_api: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def branch_shifts_api(request, branch_id):
    """شفتات الفرع"""
    try:
        branch = get_object_or_404(Branch, id=branch_id)
        shifts = BranchShift.objects.filter(branch=branch, is_active=True)
        
        shifts_data = []
        for shift in shifts:
            shifts_data.append({
                'id': shift.id,
                'name': shift.name,
                'start_time': shift.start_time.strftime('%H:%M'),
                'end_time': shift.end_time.strftime('%H:%M'),
                'break_start': shift.break_start.strftime('%H:%M') if shift.break_start else None,
                'break_end': shift.break_end.strftime('%H:%M') if shift.break_end else None,
                'duration': shift.get_duration(),
            })
        
        return JsonResponse({
            'success': True,
            'shifts': shifts_data,
            'count': len(shifts_data)
        })
    except Exception as e:
        print(f"Error in branch_shifts_api: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def delete_day_entries_api(request, schedule_id):
    """حذف توزيعات يوم معين"""
    try:
        schedule = get_object_or_404(Schedule, id=schedule_id)
        
        # التحقق من الصلاحيات
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'يجب تسجيل الدخول'}, status=401)
        
        # التحقق من الصلاحيات
        if not request.user.is_superuser and hasattr(request.user, 'profile'):
            user_role = request.user.profile.role
            if user_role == 'branch_manager':
                if hasattr(request.user.profile, 'branch') and request.user.profile.branch != schedule.branch:
                    return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية لحذف توزيعات هذا الجدول'}, status=403)
            elif user_role not in ['coordinator', 'region_manager', 'operations_manager', 'admin_manager', 'super_admin']:
                return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية لحذف التوزيعات'}, status=403)
        
        # لا يمكن حذف توزيعات الجداول المعتمدة
        if schedule.status in ['approved', 'active']:
            return JsonResponse({'success': False, 'error': 'لا يمكن حذف توزيعات الجداول المعتمدة'}, status=400)
        
        # الحصول على التاريخ من البيانات المرسلة
        data = json.loads(request.body)
        date_str = data.get('date')
        
        if not date_str:
            return JsonResponse({'success': False, 'error': 'تاريخ مطلوب'}, status=400)
        
        # تحويل التاريخ
        from datetime import datetime
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'success': False, 'error': 'تنسيق تاريخ غير صحيح'}, status=400)
        
        # حذف التوزيعات لهذا اليوم
        deleted_count = schedule.entries.filter(date=target_date).delete()[0]
        
        print(f"Deleted {deleted_count} entries for date {target_date}")
        
        return JsonResponse({
            'success': True,
            'message': f'تم حذف {deleted_count} توزيعة بنجاح',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        print(f"Error in delete_day_entries_api: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_day_entries_api(request, schedule_id):
    """جلب توزيعات يوم معين"""
    try:
        schedule = get_object_or_404(Schedule, id=schedule_id)
        
        # التحقق من الصلاحيات
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'يجب تسجيل الدخول'}, status=401)
        
        # الحصول على التاريخ من المعاملات
        date_str = request.GET.get('date')
        
        if not date_str:
            return JsonResponse({'success': False, 'error': 'تاريخ مطلوب'}, status=400)
        
        # تحويل التاريخ
        from datetime import datetime
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'success': False, 'error': 'تنسيق تاريخ غير صحيح'}, status=400)
        
        # جلب التوزيعات لهذا اليوم
        entries = schedule.entries.filter(date=target_date).select_related('employee', 'shift')
        
        entries_data = []
        for entry in entries:
            entries_data.append({
                'id': entry.id,
                'employee_id': entry.employee.id,
                'employee_name': entry.employee.get_full_name() or entry.employee.username,
                'shift_id': entry.shift.id,
                'shift_name': entry.shift.name,
                'start_time': entry.start_time.strftime('%H:%M'),
                'end_time': entry.end_time.strftime('%H:%M'),
                'hours': float(entry.hours),
                'is_cover': entry.is_cover,
                'notes': entry.notes or ''
            })
        
        print(f"Found {len(entries_data)} entries for date {target_date}")
        
        return JsonResponse({
            'success': True,
            'entries': entries_data,
            'count': len(entries_data),
            'date': date_str
        })
        
    except Exception as e:
        print(f"Error in get_day_entries_api: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def leave_conflicts_api(request):
    """تعارضات الإجازات"""
    try:
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        employees = request.GET.get('employees', '').split(',')
        
        if not start_date or not end_date:
            return JsonResponse({'error': 'Start date and end date required'}, status=400)
        
        # فلترة الموظفين الفارغة
        employees = [emp for emp in employees if emp.strip()]
        
        if not employees:
            return JsonResponse({'conflicts': []})
        
        # البحث عن الإجازات المتداخلة
        conflicts = []
        for employee_id in employees:
            employee = get_object_or_404(User, id=employee_id)
            overlapping_leaves = LeaveRequest.objects.filter(
                employee=employee,
                start_date__lte=end_date,
                end_date__gte=start_date,
                status='approved'
            )
            
            for leave in overlapping_leaves:
                conflicts.append({
                    'employee_id': employee.id,
                    'employee_name': employee.get_full_name() or employee.username,
                    'start_date': leave.start_date.strftime('%Y-%m-%d'),
                    'end_date': leave.end_date.strftime('%Y-%m-%d'),
                    'type': leave.get_leave_type_display(),
                    'reason': leave.reason,
                })
        
        return JsonResponse({'conflicts': conflicts})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def create_schedule_api(request):
    """إنشاء جدول تشغيلي جديد"""
    try:
        data = json.loads(request.body)
        print("=== API: Received data ===")
        print("Basic data:", {k: v for k, v in data.items() if k != 'entries'})
        print("Entries count:", len(data.get('entries', [])))
        print("Entries data:", data.get('entries', []))
        
        # التحقق من البيانات المطلوبة
        required_fields = ['branch', 'schedule_type', 'start_date', 'end_date']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'error': f'Missing required field: {field}'}, status=400)
        
        # إنشاء الجدول
        from apps.schedules.models import Schedule, ScheduleEntry
        
        branch = get_object_or_404(Branch, id=data['branch'])
        
        # تحويل التواريخ من نصوص إلى كائنات date
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        
        schedule = Schedule.objects.create(
            branch=branch,
            schedule_type=data['schedule_type'],
            start_date=start_date,
            end_date=end_date,
            notes=data.get('notes', ''),
            created_by=request.user,
            status='draft'
        )
        
        print(f"=== API: Created schedule {schedule.id} ===")
        
        # إضافة الإدخالات إذا كانت متوفرة
        entries_created = 0
        entry_errors = []
        if 'entries' in data and data['entries']:
            print(f"=== API: Processing {len(data['entries'])} entries ===")
            for i, entry_data in enumerate(data['entries']):
                try:
                    print(f"Creating entry {i+1}: {entry_data}")
                    entry = ScheduleEntry(
                        schedule=schedule,
                        employee_id=entry_data['employee_id'],
                        date=datetime.strptime(entry_data['date'], '%Y-%m-%d').date(),
                        shift_id=entry_data['shift_id'],
                        start_time=datetime.strptime(entry_data['start_time'], '%H:%M').time(),
                        end_time=datetime.strptime(entry_data['end_time'], '%H:%M').time(),
                        hours=entry_data.get('hours', 8),
                        is_cover=entry_data.get('is_cover', False),
                        notes=entry_data.get('notes', '')
                    )
                    entry.full_clean()
                    entry.save()
                    entries_created += 1
                    print(f"Successfully created entry {entries_created}: {entry}")
                except Exception as e:
                    error_msg = str(e)
                    print(f"Error creating entry {i+1}: {error_msg}")
                    entry_errors.append({
                        'index': i,
                        'data': entry_data,
                        'error': error_msg
                    })
                    continue
        else:
            print("=== API: No entries to process ===")
        
        print(f"=== API: Total entries created: {entries_created}, Errors: {len(entry_errors)} ===")
        
        if entry_errors:
            # إذا فشل أي إدخال، يفضل حذف الجدول أو تنبيه المستخدم
            # في هذه الحالة سنعيد نجاح مع قائمة بالأخطاء ليعرضها الـ Frontend
            return JsonResponse({
                'success': entries_created > 0,
                'schedule_id': schedule.id,
                'entries_created': entries_created,
                'errors': entry_errors,
                'message': f'تم إنشاء الجدول مع {entries_created} إدخال ووجد {len(entry_errors)} أخطاء'
            })

        return JsonResponse({
            'success': True,
            'schedule_id': schedule.id,
            'entries_created': entries_created,
            'message': f'تم إنشاء الجدول التشغيلي بنجاح مع {entries_created} إدخال'
        })
        
    except Exception as e:
        print(f"=== API: Error occurred: {e} ===")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def save_schedule_entries_api(request, schedule_id):
    """حفظ إدخالات الجدول التشغيلي"""
    try:
        data = json.loads(request.body)
        schedule = get_object_or_404(Schedule, id=schedule_id)
        
        print(f"=== API: Updating schedule {schedule_id} ===")
        print("Received data:", {k: v for k, v in data.items() if k != 'entries'})
        print("Entries count:", len(data.get('entries', [])))
        
        # التحقق من الصلاحيات
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'يجب تسجيل الدخول'}, status=401)
        
        if not request.user.is_superuser and hasattr(request.user, 'profile'):
            user_role = request.user.profile.role
            if user_role == 'branch_manager':
                if hasattr(request.user.profile, 'branch') and request.user.profile.branch != schedule.branch:
                    return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية لتعديل هذا الجدول'}, status=403)
        
        # تحديث البيانات الأساسية للجدول
        if 'branch_id' in data:
            schedule.branch_id = data['branch_id']
        if 'schedule_type' in data:
            schedule.schedule_type = data['schedule_type']
        if 'status' in data:
            schedule.status = data['status']
        if 'version' in data:
            schedule.version = data['version']
        if 'start_date' in data:
            schedule.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        if 'end_date' in data:
            schedule.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        if 'notes' in data:
            schedule.notes = data['notes']
        
        schedule.save()
        print(f"Updated basic schedule data")
        
        # حذف الإدخالات الموجودة فقط إذا لم يكن هناك خيار للاحتفاظ بها
        if not data.get('keep_existing', False):
            old_entries_count = schedule.entries.count()
            schedule.entries.all().delete()
            print(f"Deleted {old_entries_count} old entries")
        else:
            print("Keeping existing entries, adding new ones only")
        
        # إنشاء الإدخالات الجديدة
        entries_created = 0
        entry_errors = []
        if 'entries' in data and data['entries']:
            print(f"Creating {len(data['entries'])} new entries")
            for i, entry_data in enumerate(data['entries']):
                try:
                    print(f"Creating entry {i+1}: {entry_data}")
                    entry = ScheduleEntry(
                        schedule=schedule,
                        employee_id=entry_data['employee_id'],
                        date=datetime.strptime(entry_data['date'], '%Y-%m-%d').date(),
                        shift_id=entry_data['shift_id'],
                        start_time=datetime.strptime(entry_data['start_time'], '%H:%M').time(),
                        end_time=datetime.strptime(entry_data['end_time'], '%H:%M').time(),
                        hours=entry_data.get('hours', 8),
                        is_cover=entry_data.get('is_cover', False),
                        notes=entry_data.get('notes', '')
                    )
                    entry.full_clean()
                    entry.save()
                    entries_created += 1
                    print(f"Successfully created entry {entries_created}: {entry}")
                except Exception as e:
                    error_msg = str(e)
                    print(f"Error creating entry {i+1}: {error_msg}")
                    entry_errors.append({
                        'index': i,
                        'data': entry_data,
                        'error': error_msg
                    })
                    continue
        else:
            print("No entries to process")
        
        print(f"Total entries created: {entries_created}, Errors: {len(entry_errors)}")
        
        if entry_errors:
            return JsonResponse({
                'success': entries_created > 0,
                'entries_created': entries_created,
                'errors': entry_errors,
                'message': f'تم حفظ {entries_created} إدخال ووجد {len(entry_errors)} أخطاء'
            })

        return JsonResponse({
            'success': True,
            'entries_created': entries_created,
            'entries_updated': entries_created,
            'message': f'تم حفظ {entries_created} إدخال بنجاح'
        })
        
    except Exception as e:
        print(f"=== API: Error occurred: {e} ===")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
