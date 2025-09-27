from django.shortcuts import render
from django.http import HttpResponse

def ScheduleListView(request):
    # Mock data for schedules
    schedules = [
        {
            'id': 1,
            'name': 'جدول الصباح - فرع الرياض',
            'description': 'جدول العمل الصباحي لفرع الرياض',
            'status': 'active',
            'type': 'يومي',
            'start_date': '2024-01-15',
            'end_date': '2024-01-21',
            'created_by': 'أحمد محمد',
            'created_at': '2024-01-10 09:00:00',
            'branch': 'فرع الرياض',
            'employee_count': 15,
            'total_hours': 8
        },
        {
            'id': 2,
            'name': 'جدول المساء - فرع جدة',
            'description': 'جدول العمل المسائي لفرع جدة',
            'status': 'draft',
            'type': 'أسبوعي',
            'start_date': '2024-01-22',
            'end_date': '2024-01-28',
            'created_by': 'سارة أحمد',
            'created_at': '2024-01-12 14:30:00',
            'branch': 'فرع جدة',
            'employee_count': 12,
            'total_hours': 6
        },
        {
            'id': 3,
            'name': 'جدول نوبات - فرع الدمام',
            'description': 'جدول النوبات الليلية لفرع الدمام',
            'status': 'pending',
            'type': 'نوبات',
            'start_date': '2024-01-29',
            'end_date': '2024-02-04',
            'created_by': 'محمد علي',
            'created_at': '2024-01-14 11:15:00',
            'branch': 'فرع الدمام',
            'employee_count': 8,
            'total_hours': 12
        }
    ]
    
    context = {
        'schedules': schedules,
        'total_schedules': len(schedules),
        'active_schedules': len([s for s in schedules if s['status'] == 'active']),
        'draft_schedules': len([s for s in schedules if s['status'] == 'draft']),
        'pending_schedules': len([s for s in schedules if s['status'] == 'pending'])
    }
    return render(request, 'schedules/list.html', context)

def ScheduleCreateView(request):
    # Mock data for the create form
    context = {
        'branches': [
            {'id': 1, 'name': 'فرع الرياض - المعرض الرئيسي'},
            {'id': 2, 'name': 'فرع جدة - معرض جدة'},
            {'id': 3, 'name': 'فرع الدمام - معرض الدمام'},
        ],
        'employees': [
            {'id': 1, 'name': 'أحمد محمد', 'role': 'مدير فرع', 'hours': 8, 'work_days': 6},
            {'id': 2, 'name': 'فاطمة علي', 'role': 'منسق', 'hours': 9, 'work_days': 5},
            {'id': 3, 'name': 'خالد سعد', 'role': 'موظف', 'hours': 8, 'work_days': 6},
            {'id': 4, 'name': 'سارة أحمد', 'role': 'موظف', 'hours': 8, 'work_days': 6},
            {'id': 5, 'name': 'محمد حسن', 'role': 'موظف', 'hours': 9, 'work_days': 5},
        ],
        'schedule_types': [
            {'value': 'weekly', 'name': 'أسبوعي (7 أيام)'},
            {'value': 'monthly', 'name': 'شهري (30 يوم)'},
            {'value': 'quarterly', 'name': 'ربع سنوي (90 يوم)'},
            {'value': 'yearly', 'name': 'سنوي (365 يوم)'},
        ]
    }
    return render(request, 'schedules/create.html', context)

def ScheduleDetailView(request, pk):
    # Mock schedule data
    schedule = {
        'id': pk,
        'name': f'جدول العمل {pk}',
        'description': f'وصف مفصل لجدول العمل رقم {pk}',
        'status': 'active',
        'type': 'يومي',
        'start_date': '2024-01-15',
        'end_date': '2024-01-21',
        'created_by': 'أحمد محمد',
        'created_at': '2024-01-10 09:00:00',
        'branch': 'فرع الرياض',
        'employee_count': 15,
        'total_hours': 8,
        'shifts': [
            {
                'id': 1,
                'name': 'نوبة الصباح',
                'start_time': '08:00',
                'end_time': '16:00',
                'employee_count': 8,
                'employees': ['أحمد محمد', 'سارة أحمد', 'محمد علي', 'فاطمة حسن', 'علي أحمد', 'نور الدين', 'مريم سعد', 'خالد يوسف']
            },
            {
                'id': 2,
                'name': 'نوبة المساء',
                'start_time': '16:00',
                'end_time': '00:00',
                'employee_count': 7,
                'employees': ['عبدالله محمد', 'هند أحمد', 'يوسف علي', 'ريم حسن', 'سعد أحمد', 'نور الدين', 'مريم سعد']
            }
        ]
    }
    return render(request, 'schedules/detail.html', {'schedule': schedule})

def ScheduleEditView(request, pk):
    # Mock schedule data for editing
    schedule = {
        'id': pk,
        'name': f'جدول العمل {pk}',
        'description': f'وصف مفصل لجدول العمل رقم {pk}',
        'status': 'active',
        'type': 'يومي',
        'start_date': '2024-01-15',
        'end_date': '2024-01-21',
        'branch': 'فرع الرياض',
        'employee_count': 15,
        'total_hours': 8
    }
    return render(request, 'schedules/create.html', {'schedule': schedule})

def ScheduleDeleteView(request, pk):
    return HttpResponse(f"Schedule Delete: {pk}")

def ScheduleApproveView(request, pk):
    return HttpResponse(f"Schedule Approve: {pk}")

def ScheduleRejectView(request, pk):
    return HttpResponse(f"Schedule Reject: {pk}")

def ScheduleCopyView(request, pk):
    return HttpResponse(f"Schedule Copy: {pk}")