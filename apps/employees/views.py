from django.shortcuts import render
from django.http import HttpResponse

def EmployeeListView(request):
    return render(request, 'employees/list.html')

def EmployeeCreateView(request):
    return render(request, 'employees/form.html')

def EmployeeDetailView(request, pk):
    # Mock employee data for demonstration
    employee = {
        'id': pk,
        'first_name': 'أحمد',
        'last_name': 'محمد',
        'email': 'ahmed.mohamed@example.com',
        'phone': '+966501234567',
        'position': 'مطور برمجيات',
        'department': 'تقنية المعلومات',
        'hire_date': '2023-01-15',
        'salary': 15000,
        'status': 'نشط',
        'branch': 'الفرع الرئيسي',
        'avatar': None
    }
    return render(request, 'employees/detail.html', {'employee': employee})

def EmployeeEditView(request, pk):
    return render(request, 'employees/form.html')

def EmployeeDeleteView(request, pk):
    return HttpResponse(f"Employee Delete: {pk}")

def EmployeeImportView(request):
    return HttpResponse("Employee Import")

def EmployeeExportView(request):
    return HttpResponse("Employee Export")