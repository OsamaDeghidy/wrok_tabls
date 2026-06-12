from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import PermissionDenied

from .models import Employee, EmployeeDocument, EmployeeEmergencyContact
from .forms import EmployeeForm, EmployeeDocumentForm, EmployeeEmergencyContactForm, EmployeeImportForm, EmployeeSearchForm
from apps.users.models import UserProfile


def check_employee_permission(user, action='view'):
    """التحقق من صلاحيات المستخدم للتعامل مع الموظفين"""
    if not user.is_authenticated:
        return False
    
    if hasattr(user, 'profile'):
        role = user.profile.role
        
        # المدير العام يمكنه فعل كل شيء
        if role == 'super_admin':
            return True
        
        # مدير العمليات ومدير الإدارة يمكنهم فعل كل شيء
        if role in ['operations_manager', 'admin_manager']:
            return True
        
        # مدير المنطقة يمكنه رؤية الموظفين في منطقته
        if role == 'region_manager':
            return True
        
        # مدير الفرع يمكنه رؤية موظفي فرعه فقط
        if role == 'branch_manager':
            return True
        
        # المنسق يمكنه رؤية الموظفين
        if role == 'coordinator':
            return action in ['view', 'create', 'edit']
    
    return False


@login_required
def employee_list_view(request):
    """عرض قائمة الموظفين"""
    if not check_employee_permission(request.user, 'view'):
        raise PermissionDenied("ليس لديك صلاحية لعرض الموظفين")
    
    # الحصول على معاملات البحث والفلترة
    search_form = EmployeeSearchForm(request.GET)
    
    # بناء الاستعلام
    queryset = Employee.objects.select_related('user', 'user__profile', 'user__profile__branch').all()
    
    # تطبيق الفلاتر
    if search_form.is_valid():
        search = search_form.cleaned_data.get('search')
        branch = search_form.cleaned_data.get('branch')
        status = search_form.cleaned_data.get('status')
        employment_type = search_form.cleaned_data.get('employment_type')
        role = search_form.cleaned_data.get('role')
        
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(employee_number__icontains=search) |
                Q(job_title__icontains=search)
            )
        
        if branch:
            queryset = queryset.filter(user__profile__branch=branch)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if employment_type:
            queryset = queryset.filter(employment_type=employment_type)
        
        if role:
            queryset = queryset.filter(user__profile__role=role)
    
    # تطبيق قيود الصلاحيات
    if hasattr(request.user, 'profile'):
        role = request.user.profile.role
        if role == 'branch_manager' and hasattr(request.user.profile, 'branch'):
            # مدير الفرع يرى موظفي فرعه فقط
            queryset = queryset.filter(user__profile__branch=request.user.profile.branch)
    
    # الترقيم
    paginator = Paginator(queryset, 20)
    page_number = request.GET.get('page')
    employees = paginator.get_page(page_number)
    
    context = {
        'employees': employees,
        'search_form': search_form,
        'total_count': queryset.count(),
    }
    
    return render(request, 'employees/list.html', context)


@login_required
def employee_detail_view(request, employee_id):
    """عرض تفاصيل الموظف"""
    from datetime import datetime
    from django.db.models import Sum, Count
    from apps.schedules.models import ScheduleEntry
    from apps.leaves.models import LeaveRequest
    from apps.violations.models import Violation
    
    employee = get_object_or_404(Employee, pk=employee_id)
    
    # التحقق من الصلاحيات
    if not check_employee_permission(request.user, 'view'):
        raise PermissionDenied("ليس لديك صلاحية لعرض تفاصيل الموظف")
    
    # مدير الفرع يرى موظفي فرعه فقط
    if (hasattr(request.user, 'profile') and 
        request.user.profile.role == 'branch_manager' and 
        hasattr(request.user.profile, 'branch')):
        if employee.get_branch() != request.user.profile.branch:
            raise PermissionDenied("ليس لديك صلاحية لعرض هذا الموظف")
    
    # الحصول على الوثائق وجهات الاتصال
    documents = employee.documents.all()
    emergency_contacts = employee.emergency_contacts.all()
    
    # حساب الإحصائيات الشهرية
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # ساعات العمل والنوبات هذا الشهر
    monthly_entries = ScheduleEntry.objects.filter(
        employee=employee.user,
        schedule__start_date__month=current_month,
        schedule__start_date__year=current_year
    )
    
    monthly_hours = sum([entry.get_duration() for entry in monthly_entries]) if monthly_entries.exists() else 0
    monthly_shifts = monthly_entries.count()
    
    # الإجازات هذا الشهر
    monthly_leaves_count = LeaveRequest.objects.filter(
        employee=employee.user,
        start_date__month=current_month,
        start_date__year=current_year,
        status='approved'
    ).count()
    
    # المخالفات هذا الشهر
    monthly_violations_count = Violation.objects.filter(
        employee=employee.user,
        date__month=current_month,
        date__year=current_year
    ).count()
    
    # معدل الحضور (نسبة الحضور من النوبات المجدولة)
    total_scheduled = monthly_shifts
    attended = monthly_shifts  # يمكن تطويره لاحقاً لحساب الحضور الفعلي
    attendance_rate = (attended / total_scheduled * 100) if total_scheduled > 0 else 0
    
    # الحصول على جميع النوبات والإجازات والمخالفات
    all_shifts = ScheduleEntry.objects.filter(employee=employee.user).order_by('-schedule__start_date')[:20]
    all_leaves = LeaveRequest.objects.filter(employee=employee.user).order_by('-start_date')[:20]
    all_violations = Violation.objects.filter(employee=employee.user).order_by('-date')[:20]
    
    context = {
        'employee': employee,
        'documents': documents,
        'emergency_contacts': emergency_contacts,
        'monthly_hours': int(monthly_hours),
        'monthly_shifts': monthly_shifts,
        'monthly_leaves': monthly_leaves_count,
        'monthly_violations': monthly_violations_count,
        'attendance_rate': round(attendance_rate, 1),
        'all_shifts': all_shifts,
        'all_leaves': all_leaves,
        'all_violations': all_violations,
    }
    
    return render(request, 'employees/detail.html', context)


@login_required
def employee_create_view(request):
    """إنشاء موظف جديد"""
    if not check_employee_permission(request.user, 'create'):
        raise PermissionDenied("ليس لديك صلاحية لإضافة موظف جديد")
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            try:
                employee = form.save()
                messages.success(request, f'تم إنشاء الموظف {employee.user.get_full_name()} بنجاح')
                return redirect('employees:detail', employee.id)
            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء إنشاء الموظف: {str(e)}')
                import traceback
                print(traceback.format_exc())
        else:
            # عرض أخطاء الفورم
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = EmployeeForm()
    
    context = {
        'form': form,
        'title': 'إضافة موظف جديد'
    }
    
    return render(request, 'employees/form.html', context)


@login_required
def employee_edit_view(request, employee_id):
    """تعديل بيانات الموظف"""
    employee = get_object_or_404(Employee, pk=employee_id)
    
    if not check_employee_permission(request.user, 'edit'):
        raise PermissionDenied("ليس لديك صلاحية لتعديل بيانات الموظف")
    
    # مدير الفرع يعدل موظفي فرعه فقط
    if (hasattr(request.user, 'profile') and 
        request.user.profile.role == 'branch_manager' and 
        hasattr(request.user.profile, 'branch')):
        if employee.get_branch() != request.user.profile.branch:
            raise PermissionDenied("ليس لديك صلاحية لتعديل هذا الموظف")
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            try:
                employee = form.save()
                messages.success(request, f'تم تحديث بيانات الموظف {employee.user.get_full_name()} بنجاح')
                return redirect('employees:detail', employee.id)
            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء تحديث بيانات الموظف: {str(e)}')
    else:
        form = EmployeeForm(instance=employee)
    
    context = {
        'form': form,
        'employee': employee,
        'title': 'تعديل بيانات الموظف'
    }
    
    return render(request, 'employees/form.html', context)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def employee_delete_view(request, employee_id):
    """حذف الموظف"""
    employee = get_object_or_404(Employee, pk=employee_id)
    
    if not check_employee_permission(request.user, 'delete'):
        return JsonResponse({'success': False, 'message': 'ليس لديك صلاحية لحذف الموظف'}, status=403)
    
    # مدير الفرع يحذف موظفي فرعه فقط
    if (hasattr(request.user, 'profile') and 
        request.user.profile.role == 'branch_manager' and 
        hasattr(request.user.profile, 'branch')):
        if employee.get_branch() != request.user.profile.branch:
            return JsonResponse({'success': False, 'message': 'ليس لديك صلاحية لحذف هذا الموظف'}, status=403)
    
    try:
        employee_name = employee.user.get_full_name()
        # حذف المستخدم المرتبط أيضاً
        user_to_delete = employee.user
        employee.delete()
        user_to_delete.delete()
        return JsonResponse({'success': True, 'message': f'تم حذف الموظف {employee_name} بنجاح'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'حدث خطأ أثناء حذف الموظف: {str(e)}'})




@login_required
def employee_import_view(request):
    """استيراد الموظفين من Excel"""
    import pandas as pd
    from datetime import datetime
    
    if not check_employee_permission(request.user, 'create'):
        raise PermissionDenied("ليس لديك صلاحية لاستيراد الموظفين")
    
    if request.method == 'POST':
        form = EmployeeImportForm(request.POST, request.FILES)
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
                    return redirect('employees:import')
                
                created_count = 0
                updated_count = 0
                errors = []
                
                # تحسين الكشف عن الأعمدة - تحويل العناوين لنصوص منظفة وموحدة
                actual_columns = {str(col).strip().lower(): col for col in df.columns}
                
                # دالة داخلية للحصول على القيمة من أسماء محتملة متعددة
                def get_val(row_data, *names):
                    for name in names:
                        name_lower = name.lower()
                        if name_lower in actual_columns:
                            val = row_data[actual_columns[name_lower]]
                            if pd.notna(val):
                                return str(val).strip()
                    return ''
                
                # معالجة كل صف
                for index, row in df.iterrows():
                    try:
                        # دعم التسميات المتعددة بالعربية والإنجليزية
                        employee_number = get_val(row, 'employee_number', 'الرقم الوظيفي', 'الرقم', 'رقم الموظف', 'id')
                        username = get_val(row, 'username', 'اسم المستخدم', 'user')
                        email = get_val(row, 'email', 'البريد الإلكتروني', 'البريد', 'email address')
                        full_name = get_val(row, 'full_name', 'الاسم الكامل', 'الاسم', 'name', 'employee name')
                        
                        if not employee_number or employee_number.lower() == 'nan':
                            errors.append(f'الصف {index + 2}: الرقم الوظيفي مفقود')
                            continue
                        
                        # تعيين قيم افتراضية إذا كانت مفقودة
                        if not username or username.lower() == 'nan':
                            username = f"user_{employee_number}"
                        if not email or email.lower() == 'nan':
                            email = f"{username}@company.com"
                        
                        # تقسيم الاسم الكامل إلى اسم أول وأخير لـ Django User
                        if full_name and ' ' in full_name:
                            name_parts = full_name.split(' ', 1)
                            first_name = name_parts[0]
                            last_name = name_parts[1]
                        else:
                            first_name = full_name
                            last_name = ''
                        
                        # التحقق من وجود المستخدم عبر الرقم الوظيفي
                        employee_obj = Employee.objects.filter(employee_number=employee_number).first()
                        user = employee_obj.user if employee_obj else None
                        
                        if not user:
                            user = User.objects.filter(username=username).first()
                        
                        if user and update_existing:
                            # --- تحضير قيم التحديث ---
                            role_val = get_val(row, 'role', 'الدور', 'الصلاحية')
                            job_title_val = get_val(row, 'job_title', 'المسمى الوظيفي', 'الوظيفة')
                            
                            # ربط الفرع
                            branch_id = None
                            branch_name = get_val(row, 'branch', 'الفرع', 'المعرض')
                            if branch_name:
                                from apps.branches.models import Branch
                                branch_obj = Branch.objects.filter(
                                    Q(name=branch_name) | Q(name__icontains=branch_name)
                                ).first()
                                if branch_obj:
                                    branch_id = branch_obj.id
                                else:
                                    errors.append(f'تحذير الصف {index + 2}: الفرع "{branch_name}" غير موجود في النظام')
                            
                            # المنطقة
                            region_final = ''
                            region_val = get_val(row, 'region', 'المنطقة', 'منطقة')
                            if region_val:
                                REGION_MAP = {
                                    'north': 'north', 'المنطقة الشمالية': 'north', 'شمال': 'north', 'شمالية': 'north',
                                    'south': 'south', 'المنطقة الجنوبية': 'south', 'جنوب': 'south', 'جنوبية': 'south',
                                    'east': 'east', 'المنطقة الشرقية': 'east', 'شرق': 'east', 'شرقية': 'east',
                                    'center': 'center', 'المنطقة الوسطى': 'center', 'وسط': 'center', 'وسطى': 'center',
                                    'west': 'west', 'المنطقة الغربية': 'west', 'غرب': 'west', 'غربية': 'west',
                                }
                                for key, code in REGION_MAP.items():
                                    if key.lower() == region_val.strip().lower():
                                        region_final = code
                                        break
                            
                            # تحديث UserProfile مباشرة في DB - يتجاوز الـ signals
                            update_kwargs = {}
                            if role_val:
                                update_kwargs['role'] = role_val
                            if job_title_val:
                                update_kwargs['position'] = job_title_val
                            if branch_name:  # فقط حدّث لو تم تحديد فرع في الملف
                                update_kwargs['branch_id'] = branch_id  # None لو مش موجود
                            if region_val:
                                update_kwargs['region'] = region_final
                            
                            if update_kwargs:
                                UserProfile.objects.filter(user=user).update(**update_kwargs)
                            
                            # حفظ User (بعد update profile لتجنب تأثير الـ signal على profile)
                            user.first_name = first_name
                            user.last_name = last_name
                            user.email = email
                            user.save()
                            
                            # تحديث Employee إذا كان موجوداً
                            try:
                                employee_inst = Employee.objects.get(user=user)
                                if job_title_val:
                                    employee_inst.job_title = job_title_val
                                
                                hire_date_raw = get_val(row, 'hire_date', 'تاريخ التعيين', 'التاريخ')
                                if hire_date_raw and hire_date_raw.lower() != 'nan':
                                    try:
                                        from django.utils.dateparse import parse_date
                                        hire_date = parse_date(hire_date_raw)
                                        if not hire_date:
                                            hire_date = datetime.strptime(hire_date_raw, '%Y-%m-%d').date()
                                        employee_inst.hire_date = hire_date
                                    except Exception:
                                        pass
                                
                                employee_inst.save()
                            except Employee.DoesNotExist:
                                pass
                            
                            updated_count += 1

                        elif not user:

                            # الحصول على كلمة المرور من الملف أو استخدام الافتراضية
                            password = get_val(row, 'password', 'كلمة المرور', 'الباسورد')
                            if not password:
                                password = 'password123'
                            
                            # إنشاء مستخدم جديد
                            user = User.objects.create_user(
                                username=username,
                                email=email,
                                first_name=first_name,
                                last_name=last_name,
                                password=password
                            )
                            
                            # --- تحضير قيم الـ profile ---
                            role_val = get_val(row, 'role', 'الدور', 'الصلاحية')
                            role_final = role_val if role_val else 'employee'
                            
                            job_title = get_val(row, 'job_title', 'المسمى الوظيفي', 'الوظيفة') or 'موظف'
                            
                            # ربط الفرع - نحفظ الـ ID مباشرة
                            branch_id = None
                            branch_name = get_val(row, 'branch', 'الفرع', 'المعرض')
                            if branch_name:
                                from apps.branches.models import Branch
                                branch_obj = Branch.objects.filter(
                                    Q(name=branch_name) | Q(name__icontains=branch_name)
                                ).first()
                                if branch_obj:
                                    branch_id = branch_obj.id
                                else:
                                    errors.append(f'تحذير الصف {index + 2}: الفرع "{branch_name}" غير موجود في النظام')
                            
                            # المنطقة
                            region_final = ''
                            region_val = get_val(row, 'region', 'المنطقة', 'منطقة')
                            if region_val:
                                REGION_MAP = {
                                    'north': 'north', 'المنطقة الشمالية': 'north', 'شمال': 'north', 'شمالية': 'north',
                                    'south': 'south', 'المنطقة الجنوبية': 'south', 'جنوب': 'south', 'جنوبية': 'south',
                                    'east': 'east', 'المنطقة الشرقية': 'east', 'شرق': 'east', 'شرقية': 'east',
                                    'center': 'center', 'المنطقة الوسطى': 'center', 'وسط': 'center', 'وسطى': 'center',
                                    'west': 'west', 'المنطقة الغربية': 'west', 'غرب': 'west', 'غربية': 'west',
                                }
                                for key, code in REGION_MAP.items():
                                    if key.lower() == region_val.strip().lower():
                                        region_final = code
                                        break
                                if not region_final:
                                    errors.append(f'تحذير الصف {index + 2}: قيمة المنطقة "{region_val}" غير معروفة')
                            
                            # حفظ الـ profile بـ update() مع branch_id صراحة - يتجاوز الـ Django signals
                            UserProfile.objects.filter(user=user).update(
                                role=role_final,
                                position=job_title,
                                branch_id=branch_id,
                                region=region_final,
                            )
                            
                            # تاريخ التعيين
                            hire_date_raw = get_val(row, 'hire_date', 'تاريخ التعيين', 'التاريخ')
                            hire_date = None
                            
                            if hire_date_raw and hire_date_raw.lower() != 'nan':
                                try:
                                    from django.utils.dateparse import parse_date
                                    hire_date = parse_date(hire_date_raw)
                                    if not hire_date:
                                        hire_date = datetime.strptime(hire_date_raw, '%Y-%m-%d').date()
                                except Exception:
                                    hire_date = datetime.now().date()
                            else:
                                hire_date = datetime.now().date()
                            
                            # إنشاء Employee
                            employee = Employee.objects.create(
                                user=user,
                                employee_number=employee_number,
                                job_title=job_title,
                                employment_type='full_time',
                                status='active',
                                hire_date=hire_date
                            )
                            
                            created_count += 1
                        else:
                            if not update_existing:
                                errors.append(f'الصف {index + 2}: الموظف صاحب الرقم {employee_number} موجود بالفعل (فعّل خيار "تحديث الموظفين الموجودين" لتحديثه)')
                            else:
                                errors.append(f'الصف {index + 2}: الموظف صاحب الرقم المرجعي {employee_number} موجود ولكن لم يتم تحديثه')
                    
                    except Exception as e:
                        errors.append(f'الصف {index + 2}: {str(e)}')
                
                # رسائل النتائج
                if created_count > 0:
                    messages.success(request, f'تم إنشاء {created_count} موظف جديد')
                if updated_count > 0:
                    messages.success(request, f'تم تحديث {updated_count} موظف')
                if errors:
                    for error in errors[:5]:  # عرض أول 5 أخطاء فقط
                        messages.warning(request, error)
                    if len(errors) > 5:
                        messages.warning(request, f'و {len(errors) - 5} أخطاء أخرى...')
                
                return redirect('employees:list')
                
            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء استيراد الملف: {str(e)}')
    else:
        form = EmployeeImportForm()
    
    context = {
        'form': form,
        'title': 'استيراد الموظفين'
    }
    
    return render(request, 'employees/import.html', context)


@login_required
def employee_export_view(request):
    """تصدير الموظفين إلى Excel"""
    import pandas as pd
    from django.http import HttpResponse
    from datetime import datetime
    
    if not check_employee_permission(request.user, 'view'):
        raise PermissionDenied("ليس لديك صلاحية لتصدير الموظفين")
    
    # الحصول على جميع الموظفين
    employees = Employee.objects.select_related('user', 'user__profile', 'user__profile__branch').all()
    
    # تطبيق قيود الصلاحيات
    if hasattr(request.user, 'profile'):
        role = request.user.profile.role
        if role == 'branch_manager' and hasattr(request.user.profile, 'branch'):
            employees = employees.filter(user__profile__branch=request.user.profile.branch)
    
    # إعداد البيانات
    data = []
    for employee in employees:
        profile = employee.user.profile if hasattr(employee.user, 'profile') else None
        data.append({
            'الرقم الوظيفي': employee.employee_number,
            'الاسم الكامل': employee.user.get_full_name(),
            'اسم المستخدم': employee.user.username,
            'البريد الإلكتروني': employee.user.email,
            'المسمى الوظيفي': employee.job_title,
            'الدور': profile.get_role_display() if profile else '',
            'الفرع': profile.branch.name if profile and profile.branch else '',
            'نوع التوظيف': employee.get_employment_type_display(),
            'ساعات العمل': profile.work_hours if profile else 8,
            'الحالة': employee.get_status_display(),
            'تاريخ التعيين': employee.hire_date.strftime('%Y-%m-%d') if employee.hire_date else '',
            'مكان العمل': employee.work_location,
        })
    
    # إنشاء DataFrame
    df = pd.DataFrame(data)
    
    # إنشاء ملف Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="employees_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
    
    # كتابة DataFrame إلى Excel
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='الموظفين')
    
    return response


@login_required
def download_sample_file(request):
    """تحميل ملف Excel نموذجي للاستيراد"""
    import pandas as pd
    from django.http import HttpResponse
    
    # محاولة الحصول على فروع من قاعدة البيانات ليكون الملف واقعياً
    try:
        from apps.branches.models import Branch
        db_branches = list(Branch.objects.filter(status='active')[:3])
        branch1 = db_branches[0].name if len(db_branches) > 0 else 'فرع الرياض'
        branch2 = db_branches[1].name if len(db_branches) > 1 else 'فرع جدة'
        branch3 = db_branches[2].name if len(db_branches) > 2 else 'فرع الدمام'
    except Exception:
        branch1, branch2, branch3 = 'فرع الرياض', 'فرع جدة', 'فرع الدمام'
        
    # إنشاء بيانات نموذجية
    sample_data = {
        'الرقم الوظيفي': ['EMP-1001', 'EMP-1002', 'EMP-1003'],
        'الاسم الكامل': ['أحمد محمد', 'فاطمة علي', 'محمد خالد'],
        'username': ['ahmed.mohamed', 'fatima.ali', 'mohamed.khaled'],
        'email': ['ahmed@company.com', 'fatima@company.com', 'mohamed@company.com'],
        'password': ['password123', 'password123', 'password123'],
        'job_title': ['مطور', 'مدير معرض', 'محلل'],
        'role': ['employee', 'branch_manager', 'employee'],
        'branch': [branch1, branch2, branch3],
        'region': ['المنطقة الوسطى', 'المنطقة الغربية', 'المنطقة الشرقية'],
        'hire_date': ['2024-01-10', '2024-01-15', '2024-02-01']
    }
    
    # إنشاء DataFrame
    df = pd.DataFrame(sample_data)
    
    # إنشاء ملف Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="sample_employees.xlsx"'
    
    # كتابة DataFrame إلى Excel
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='الموظفين')
        
        # الحصول على الـ worksheet لتنسيق العناوين
        worksheet = writer.sheets['الموظفين']
        
        # تعيين عرض الأعمدة
        for column in worksheet.columns:
            max_length = 0
            column = [cell for cell in column]
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
    
    return response


# API Views
@login_required
def api_employee_list(request):
    """API لعرض قائمة الموظفين"""
    if not check_employee_permission(request.user, 'view'):
        return JsonResponse({'error': 'ليس لديك صلاحية لعرض الموظفين'}, status=403)
    
    employees = Employee.objects.select_related('user', 'user__profile', 'user__profile__branch').all()
    
    # تطبيق قيود الصلاحيات
    if hasattr(request.user, 'profile'):
        role = request.user.profile.role
        if role == 'branch_manager' and hasattr(request.user.profile, 'branch'):
            employees = employees.filter(user__profile__branch=request.user.profile.branch)
    
    data = []
    for employee in employees:
        data.append({
            'id': employee.id,
            'employee_number': employee.employee_number,
            'name': employee.user.get_full_name(),
            'job_title': employee.job_title,
            'status': employee.get_status_display(),
            'branch': employee.get_branch().name if employee.get_branch() else 'غير محدد',
            'role': employee.get_role(),
            'email': employee.user.email,
            'phone': employee.user.profile.phone if hasattr(employee.user, 'profile') else '',
        })
    
    return JsonResponse({'employees': data})


@login_required
def api_employee_detail(request, employee_id):
    """API لعرض تفاصيل الموظف"""
    employee = get_object_or_404(Employee, pk=employee_id)
    
    if not check_employee_permission(request.user, 'view'):
        return JsonResponse({'error': 'ليس لديك صلاحية لعرض تفاصيل الموظف'}, status=403)
    
    # مدير الفرع يرى موظفي فرعه فقط
    if (hasattr(request.user, 'profile') and 
        request.user.profile.role == 'branch_manager' and 
        hasattr(request.user.profile, 'branch')):
        if employee.get_branch() != request.user.profile.branch:
            return JsonResponse({'error': 'ليس لديك صلاحية لعرض هذا الموظف'}, status=403)
    
    data = {
        'id': employee.id,
        'employee_number': employee.employee_number,
        'name': employee.user.get_full_name(),
        'job_title': employee.job_title,
        'employment_type': employee.get_employment_type_display(),
        'status': employee.get_status_display(),
        'hire_date': employee.hire_date.strftime('%Y-%m-%d') if employee.hire_date else None,
        'termination_date': employee.termination_date.strftime('%Y-%m-%d') if employee.termination_date else None,
        'work_location': employee.work_location,
        'branch': employee.get_branch().name if employee.get_branch() else 'غير محدد',
        'role': employee.get_role(),
        'email': employee.user.email,
        'phone': employee.user.profile.phone if hasattr(employee.user, 'profile') else '',
        'notes': employee.notes,
        'created_at': employee.created_at.strftime('%Y-%m-%d %H:%M'),
        'updated_at': employee.updated_at.strftime('%Y-%m-%d %H:%M'),
    }
    
    return JsonResponse(data)


@login_required
def api_branch_managers(request, branch_id):
    """API للحصول على مديري الفرع"""
    try:
        from apps.branches.models import Branch
        branch = Branch.objects.get(id=branch_id)
        
        # الحصول على مديري الفرع (branch_manager role مع نفس الفرع)
        managers = User.objects.filter(
            profile__role='branch_manager',
            profile__branch=branch,
            is_active=True
        ).select_related('profile')
        
        data = []
        for manager in managers:
            data.append({
                'id': manager.id,
                'name': manager.get_full_name(),
                'username': manager.username,
                'email': manager.email,
            })
        
        return JsonResponse({'managers': data})
    except Branch.DoesNotExist:
        return JsonResponse({'error': 'الفرع غير موجود'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)