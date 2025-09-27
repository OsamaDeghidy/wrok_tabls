from django.shortcuts import render
from django.http import HttpResponse

def BranchListView(request):
    # Mock data for branches
    branches = [
        {
            'id': 1,
            'name': 'فرع الرياض الرئيسي',
            'code': 'RYD-001',
            'category': 'A',
            'category_display': 'فئة أ',
            'region': 'الرياض',
            'city': 'الرياض',
            'address': 'شارع الملك فهد، حي النخيل',
            'phone': '+966112345678',
            'email': 'riyadh@company.com',
            'manager_name': 'أحمد محمد',
            'manager_phone': '+966501234567',
            'status': 'active',
            'status_display': 'نشط',
            'opening_date': '2020-01-15',
            'employee_count': 25,
            'area': 500.5,
            'description': 'الفرع الرئيسي في الرياض'
        },
        {
            'id': 2,
            'name': 'فرع جدة التجاري',
            'code': 'JED-002',
            'category': 'B',
            'category_display': 'فئة ب',
            'region': 'مكة المكرمة',
            'city': 'جدة',
            'address': 'شارع التحلية، حي الزهراء',
            'phone': '+966126543210',
            'email': 'jeddah@company.com',
            'manager_name': 'فاطمة علي',
            'manager_phone': '+966502345678',
            'status': 'active',
            'status_display': 'نشط',
            'opening_date': '2021-03-20',
            'employee_count': 18,
            'area': 350.0,
            'description': 'فرع تجاري في جدة'
        },
        {
            'id': 3,
            'name': 'فرع الدمام الصناعي',
            'code': 'DAM-003',
            'category': 'C',
            'category_display': 'فئة ج',
            'region': 'الشرقية',
            'city': 'الدمام',
            'address': 'المنطقة الصناعية الثانية',
            'phone': '+966133987654',
            'email': 'dammam@company.com',
            'manager_name': 'محمد حسن',
            'manager_phone': '+966503456789',
            'status': 'inactive',
            'status_display': 'غير نشط',
            'opening_date': '2022-06-10',
            'employee_count': 12,
            'area': 200.0,
            'description': 'فرع صناعي في الدمام'
        }
    ]
    
    context = {
        'branches': branches,
        'total_branches': len(branches),
        'active_branches': len([b for b in branches if b['status'] == 'active']),
        'inactive_branches': len([b for b in branches if b['status'] == 'inactive']),
        'total_employees': sum([b['employee_count'] for b in branches])
    }
    return render(request, 'branches/list.html', context)

def BranchCreateView(request):
    return render(request, 'branches/form.html')

def BranchDetailView(request, pk):
    # Mock branch data
    branch = {
        'id': pk,
        'name': 'فرع الرياض الرئيسي',
        'code': 'RYD-001',
        'category': 'A',
        'category_display': 'فئة أ',
        'region': 'الرياض',
        'city': 'الرياض',
        'address': 'شارع الملك فهد، حي النخيل، الرياض 12345',
        'phone': '+966112345678',
        'email': 'riyadh@company.com',
        'website': 'https://riyadh.company.com',
        'manager_name': 'أحمد محمد',
        'manager_phone': '+966501234567',
        'manager_email': 'ahmed.mohamed@company.com',
        'status': 'active',
        'status_display': 'نشط',
        'opening_date': '2020-01-15',
        'employee_count': 25,
        'area': 500.5,
        'description': 'الفرع الرئيسي في الرياض والمقر الرئيسي للشركة',
        'services': [
            'خدمات العملاء',
            'المبيعات',
            'الدعم الفني',
            'الاستشارات'
        ],
        'working_hours': {
            'sunday': '8:00 AM - 6:00 PM',
            'monday': '8:00 AM - 6:00 PM',
            'tuesday': '8:00 AM - 6:00 PM',
            'wednesday': '8:00 AM - 6:00 PM',
            'thursday': '8:00 AM - 6:00 PM',
            'friday': 'مغلق',
            'saturday': '9:00 AM - 2:00 PM'
        },
        'facilities': [
            'موقف سيارات',
            'مصلى',
            'كافيتريا',
            'قاعة اجتماعات',
            'مكتبة'
        ]
    }
    return render(request, 'branches/detail.html', {'branch': branch})

def BranchEditView(request, pk):
    # Mock branch data for editing
    branch = {
        'id': pk,
        'name': 'فرع الرياض الرئيسي',
        'code': 'RYD-001',
        'category': 'A',
        'region': 'الرياض',
        'city': 'الرياض',
        'address': 'شارع الملك فهد، حي النخيل',
        'phone': '+966112345678',
        'email': 'riyadh@company.com',
        'website': 'https://riyadh.company.com',
        'manager_name': 'أحمد محمد',
        'manager_phone': '+966501234567',
        'manager_email': 'ahmed.mohamed@company.com',
        'status': 'active',
        'opening_date': '2020-01-15',
        'employee_count': 25,
        'area': 500.5,
        'description': 'الفرع الرئيسي في الرياض'
    }
    return render(request, 'branches/form.html', {'branch': branch})

def BranchDeleteView(request, pk):
    return HttpResponse(f"Branch Delete: {pk}")