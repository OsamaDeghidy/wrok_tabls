from django.shortcuts import render
from django.http import HttpResponse

def LeaveListView(request):
    # Mock data for leaves
    leaves = [
        {
            'id': 1,
            'employee_name': 'أحمد محمد',
            'employee_position': 'مطور برمجيات',
            'leave_type': 'annual',
            'leave_type_display': 'إجازة سنوية',
            'start_date': '2024-01-20',
            'end_date': '2024-01-25',
            'days_count': 6,
            'status': 'pending',
            'created_at': '2024-01-15 09:00:00',
            'reason': 'إجازة سنوية للراحة والاستجمام',
            'emergency_contact': '+966501234567',
            'manager_name': 'سارة أحمد'
        },
        {
            'id': 2,
            'employee_name': 'فاطمة علي',
            'employee_position': 'مديرة الموارد البشرية',
            'leave_type': 'sick',
            'leave_type_display': 'إجازة مرضية',
            'start_date': '2024-01-18',
            'end_date': '2024-01-20',
            'days_count': 3,
            'status': 'approved',
            'created_at': '2024-01-17 14:30:00',
            'reason': 'إجازة مرضية بسبب نزلة برد',
            'emergency_contact': '+966502345678',
            'manager_name': 'محمد حسن',
            'reviewed_at': '2024-01-17 16:00:00'
        },
        {
            'id': 3,
            'employee_name': 'محمد حسن',
            'employee_position': 'محاسب',
            'leave_type': 'emergency',
            'leave_type_display': 'إجازة طارئة',
            'start_date': '2024-01-22',
            'end_date': '2024-01-22',
            'days_count': 1,
            'status': 'rejected',
            'created_at': '2024-01-21 08:00:00',
            'reason': 'حالة طارئة عائلية',
            'emergency_contact': '+966503456789',
            'manager_name': 'أحمد محمد',
            'reviewed_at': '2024-01-21 10:00:00',
            'review_notes': 'تم رفض الطلب بسبب عدم توفر بديل مناسب'
        }
    ]
    
    context = {
        'leaves': leaves,
        'total_leaves': len(leaves),
        'pending_leaves': len([l for l in leaves if l['status'] == 'pending']),
        'approved_leaves': len([l for l in leaves if l['status'] == 'approved']),
        'rejected_leaves': len([l for l in leaves if l['status'] == 'rejected'])
    }
    return render(request, 'leaves/list.html', context)

def LeaveCreateView(request):
    return render(request, 'leaves/form.html')

def LeaveDetailView(request, pk):
    # Mock leave data
    leave = {
        'id': pk,
        'employee_name': 'أحمد محمد',
        'employee_position': 'مطور برمجيات',
        'employee_department': 'تقنية المعلومات',
        'employee_phone': '+966501234567',
        'employee_email': 'ahmed.mohamed@example.com',
        'leave_type': 'annual',
        'leave_type_display': 'إجازة سنوية',
        'start_date': '2024-01-20',
        'end_date': '2024-01-25',
        'days_count': 6,
        'status': 'pending',
        'created_at': '2024-01-15 09:00:00',
        'reason': 'إجازة سنوية للراحة والاستجمام مع العائلة',
        'notes': 'سأكون متاحاً للطوارئ على رقم الهاتف المرفق',
        'emergency_contact': '+966501234567',
        'manager_name': 'سارة أحمد',
        'reviewed_at': None,
        'review_notes': None,
        'attachments': [
            {
                'name': 'تقرير_طبي.pdf',
                'url': '/media/attachments/medical_report.pdf'
            }
        ]
    }
    return render(request, 'leaves/detail.html', {'leave': leave})

def LeaveEditView(request, pk):
    # Mock leave data for editing
    leave = {
        'id': pk,
        'employee': '1',
        'leave_type': 'annual',
        'start_date': '2024-01-20',
        'end_date': '2024-01-25',
        'days_count': 6,
        'status': 'pending',
        'reason': 'إجازة سنوية للراحة والاستجمام',
        'notes': 'سأكون متاحاً للطوارئ',
        'emergency_contact': '+966501234567',
        'manager_notes': '',
        'attachments': [
            {
                'name': 'تقرير_طبي.pdf',
                'url': '/media/attachments/medical_report.pdf'
            }
        ]
    }
    return render(request, 'leaves/form.html', {'leave': leave})

def LeaveDeleteView(request, pk):
    return HttpResponse(f"Leave Delete: {pk}")

def LeaveApproveView(request, pk):
    return HttpResponse(f"Leave Approve: {pk}")

def LeaveRejectView(request, pk):
    return HttpResponse(f"Leave Reject: {pk}")