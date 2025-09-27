from django.shortcuts import render
from django.http import HttpResponse

def ApprovalListView(request):
    # Mock data for approvals
    approvals = [
        {
            'id': 1,
            'title': 'طلب إجازة سنوية',
            'type': 'leave',
            'type_display': 'طلب إجازة',
            'requester_name': 'أحمد محمد',
            'requester_position': 'مطور برمجيات',
            'department': 'تقنية المعلومات',
            'priority': 'medium',
            'priority_display': 'متوسطة',
            'status': 'pending',
            'created_at': '2024-01-15 09:00:00',
            'deadline': '2024-01-20',
            'manager_name': 'سارة أحمد',
            'description': 'طلب إجازة سنوية لمدة 5 أيام للراحة والاستجمام',
            'justification': 'حاجة للراحة بعد فترة عمل مكثفة'
        },
        {
            'id': 2,
            'title': 'طلب شراء معدات',
            'type': 'equipment',
            'type_display': 'طلب معدات',
            'requester_name': 'فاطمة علي',
            'requester_position': 'مديرة الموارد البشرية',
            'department': 'الموارد البشرية',
            'priority': 'high',
            'priority_display': 'عالية',
            'status': 'approved',
            'created_at': '2024-01-14 14:30:00',
            'deadline': '2024-01-18',
            'manager_name': 'محمد حسن',
            'reviewed_at': '2024-01-15 10:00:00',
            'description': 'طلب شراء أجهزة حاسوب جديدة للموظفين',
            'justification': 'تحسين كفاءة العمل وتحديث الأجهزة القديمة'
        },
        {
            'id': 3,
            'title': 'طلب تدريب تقني',
            'type': 'training',
            'type_display': 'طلب تدريب',
            'requester_name': 'محمد حسن',
            'requester_position': 'محاسب',
            'department': 'المحاسبة',
            'priority': 'urgent',
            'priority_display': 'عاجلة',
            'status': 'rejected',
            'created_at': '2024-01-13 11:00:00',
            'deadline': '2024-01-16',
            'manager_name': 'أحمد محمد',
            'reviewed_at': '2024-01-14 15:00:00',
            'review_notes': 'تم رفض الطلب بسبب عدم توفر الميزانية',
            'description': 'طلب حضور دورة تدريبية في المحاسبة المتقدمة',
            'justification': 'تطوير المهارات المحاسبية والاستفادة من أحدث التقنيات'
        }
    ]
    
    context = {
        'approvals': approvals,
        'total_approvals': len(approvals),
        'pending_approvals': len([a for a in approvals if a['status'] == 'pending']),
        'approved_approvals': len([a for a in approvals if a['status'] == 'approved']),
        'rejected_approvals': len([a for a in approvals if a['status'] == 'rejected'])
    }
    return render(request, 'approvals/list.html', context)

def ApprovalCreateView(request):
    return render(request, 'approvals/form.html')

def ApprovalDetailView(request, pk):
    # Mock approval data
    approval = {
        'id': pk,
        'title': 'طلب إجازة سنوية',
        'type': 'leave',
        'type_display': 'طلب إجازة',
        'requester_name': 'أحمد محمد',
        'requester_position': 'مطور برمجيات',
        'requester_department': 'تقنية المعلومات',
        'requester_phone': '+966501234567',
        'requester_email': 'ahmed.mohamed@example.com',
        'department': 'تقنية المعلومات',
        'priority': 'medium',
        'priority_display': 'متوسطة',
        'status': 'pending',
        'created_at': '2024-01-15 09:00:00',
        'deadline': '2024-01-20',
        'manager_name': 'سارة أحمد',
        'reviewed_at': None,
        'review_notes': None,
        'description': 'طلب إجازة سنوية لمدة 5 أيام للراحة والاستجمام مع العائلة',
        'justification': 'حاجة للراحة بعد فترة عمل مكثفة وتجديد النشاط',
        'attachments': [
            {
                'name': 'طلب_إجازة.pdf',
                'url': '/media/attachments/leave_request.pdf'
            }
        ],
        'comments': [
            {
                'author': 'سارة أحمد',
                'text': 'تم استلام الطلب وسيتم مراجعته قريباً',
                'created_at': '2024-01-15 09:30:00'
            }
        ]
    }
    return render(request, 'approvals/detail.html', {'approval': approval})

def ApprovalEditView(request, pk):
    # Mock approval data for editing
    approval = {
        'id': pk,
        'title': 'طلب إجازة سنوية',
        'type': 'leave',
        'manager': '1',
        'department': 'تقنية المعلومات',
        'priority': 'medium',
        'status': 'pending',
        'deadline': '2024-01-20',
        'description': 'طلب إجازة سنوية لمدة 5 أيام للراحة والاستجمام',
        'justification': 'حاجة للراحة بعد فترة عمل مكثفة',
        'review_notes': '',
        'attachments': [
            {
                'name': 'طلب_إجازة.pdf',
                'url': '/media/attachments/leave_request.pdf'
            }
        ]
    }
    return render(request, 'approvals/form.html', {'approval': approval})

def ApprovalApproveView(request, pk):
    return HttpResponse(f"Approval Approve: {pk}")

def ApprovalRejectView(request, pk):
    return HttpResponse(f"Approval Reject: {pk}")