from django.shortcuts import render
from django.http import HttpResponse

def ViolationListView(request):
    # Mock data for violations
    violations = [
        {
            'id': 1,
            'employee_name': 'أحمد محمد',
            'employee_position': 'مطور برمجيات',
            'employee_department': 'تقنية المعلومات',
            'type': 'attendance',
            'type_display': 'تأخير',
            'type_color': 'warning',
            'date': '2024-01-15',
            'time': '09:30',
            'description': 'تأخير عن العمل لمدة 30 دقيقة بدون عذر مبرر',
            'severity': 'medium',
            'severity_display': 'متوسطة',
            'severity_color': 'warning',
            'status': 'pending',
            'status_display': 'معلقة',
            'status_color': 'warning',
            'action_taken': 'تم إرسال تنبيه للموظف',
            'notes': 'المخالفة الأولى هذا الشهر'
        },
        {
            'id': 2,
            'employee_name': 'فاطمة علي',
            'employee_position': 'مديرة الموارد البشرية',
            'employee_department': 'الموارد البشرية',
            'type': 'absence',
            'type_display': 'غياب',
            'type_color': 'danger',
            'date': '2024-01-14',
            'time': '08:00',
            'description': 'غياب عن العمل بدون إشعار مسبق أو عذر مبرر',
            'severity': 'high',
            'severity_display': 'عالية',
            'severity_color': 'danger',
            'status': 'resolved',
            'status_display': 'محلولة',
            'status_color': 'success',
            'action_taken': 'تم خصم يوم من الراتب',
            'notes': 'تم التواصل مع الموظف وحل المشكلة'
        },
        {
            'id': 3,
            'employee_name': 'محمد حسن',
            'employee_position': 'محاسب',
            'employee_department': 'المحاسبة',
            'type': 'behavior',
            'type_display': 'سلوك',
            'type_color': 'info',
            'date': '2024-01-13',
            'time': '14:00',
            'description': 'سلوك غير لائق مع زميل في العمل',
            'severity': 'medium',
            'severity_display': 'متوسطة',
            'severity_color': 'warning',
            'status': 'escalated',
            'status_display': 'مرفوعة',
            'status_color': 'danger',
            'action_taken': 'تم رفع الأمر للإدارة العليا',
            'notes': 'يحتاج إلى متابعة من الإدارة'
        },
        {
            'id': 4,
            'employee_name': 'سارة أحمد',
            'employee_position': 'مستشارة مبيعات',
            'employee_department': 'المبيعات',
            'type': 'performance',
            'type_display': 'أداء',
            'type_color': 'secondary',
            'date': '2024-01-12',
            'time': '16:00',
            'description': 'عدم تحقيق الأهداف المطلوبة للشهر',
            'severity': 'low',
            'severity_display': 'منخفضة',
            'severity_color': 'success',
            'status': 'pending',
            'status_display': 'معلقة',
            'status_color': 'warning',
            'action_taken': 'تم تحديد خطة تحسين الأداء',
            'notes': 'المتابعة مستمرة'
        }
    ]
    
    context = {
        'violations': violations,
        'total_violations': len(violations),
        'pending_violations': len([v for v in violations if v['status'] == 'pending']),
        'resolved_violations': len([v for v in violations if v['status'] == 'resolved']),
        'escalated_violations': len([v for v in violations if v['status'] == 'escalated'])
    }
    return render(request, 'violations/list.html', context)

def ViolationCreateView(request):
    return render(request, 'violations/form.html')

def ViolationDetailView(request, pk):
    # Mock violation data
    violation = {
        'id': pk,
        'employee_name': 'أحمد محمد',
        'employee_position': 'مطور برمجيات',
        'employee_department': 'تقنية المعلومات',
        'type': 'attendance',
        'type_display': 'تأخير',
        'type_color': 'warning',
        'date': '2024-01-15',
        'time': '09:30',
        'description': 'تأخير عن العمل لمدة 30 دقيقة بدون عذر مبرر. الموظف لم يخبر الإدارة مسبقاً عن التأخير ولم يقدم عذراً مقبولاً',
        'severity': 'medium',
        'severity_display': 'متوسطة',
        'severity_color': 'warning',
        'status': 'pending',
        'status_display': 'معلقة',
        'status_color': 'warning',
        'action_taken': 'تم إرسال تنبيه للموظف وتذكيره بأهمية الالتزام بالمواعيد',
        'notes': 'هذه المخالفة الأولى للموظف هذا الشهر. يرجى المتابعة معه',
        'history': [
            {
                'title': 'تم إنشاء المخالفة',
                'description': 'تم تسجيل المخالفة في النظام',
                'date': '2024-01-15 09:45',
                'color': 'primary'
            },
            {
                'title': 'تم إرسال التنبيه',
                'description': 'تم إرسال تنبيه للموظف',
                'date': '2024-01-15 10:00',
                'color': 'warning'
            }
        ],
        'employee_violations_count': 3,
        'this_month_count': 1
    }
    return render(request, 'violations/detail.html', {'violation': violation})

def ViolationEditView(request, pk):
    # Mock violation data for editing
    violation = {
        'id': pk,
        'employee': '1',
        'type': 'attendance',
        'date': '2024-01-15',
        'time': '09:30',
        'description': 'تأخير عن العمل لمدة 30 دقيقة بدون عذر مبرر',
        'severity': 'medium',
        'status': 'pending',
        'action_taken': 'تم إرسال تنبيه للموظف',
        'notes': 'المخالفة الأولى هذا الشهر'
    }
    return render(request, 'violations/form.html', {'violation': violation})

def ViolationDeleteView(request, pk):
    return HttpResponse(f"Violation Delete: {pk}")