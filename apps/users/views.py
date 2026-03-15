from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.urls import reverse
from .models import UserProfile
from .forms import UserProfileForm, UserRegistrationForm
import json


def login_view(request):
    """صفحة تسجيل الدخول"""
    if request.user.is_authenticated:
        return redirect('users:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        # دعم تسجيل الدخول بالبريد الإلكتروني أو اسم المستخدم
        user = authenticate(request, username=username, password=password)
        if user is None and '@' in username:
            try:
                from django.contrib.auth.models import User as DjangoUser
                u = DjangoUser.objects.filter(email__iexact=username).first()
                if u:
                    user = authenticate(request, username=u.username, password=password)
            except Exception:
                pass
        if user is not None:
            if not user.is_active:
                messages.error(request, 'الحساب غير نشط. يرجى التواصل مع المسؤول')
                return render(request, 'users/login.html')
            login(request, user)
            if not remember_me:
                request.session.set_expiry(0)  # تنتهي الجلسة عند إغلاق المتصفح
            return redirect('users:dashboard')
        else:
            messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة')
    
    return render(request, 'users/login.html')


def register_view(request):
    """صفحة التسجيل"""
    if request.user.is_authenticated:
        return redirect('users:dashboard')
    
    if request.method == 'POST':
        # استخراج البيانات من الطلب
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        phone = request.POST.get('phone', '')
        role = request.POST.get('role')
        branch = request.POST.get('branch')
        region = request.POST.get('region', '')
        
        # التحقق من صحة البيانات
        errors = []
        
        if not username:
            errors.append('اسم المستخدم مطلوب')
        elif User.objects.filter(username=username).exists():
            errors.append('اسم المستخدم مستخدم بالفعل')
        
        if not first_name:
            errors.append('الاسم الأول مطلوب')
        
        if not last_name:
            errors.append('الاسم الأخير مطلوب')
        
        if not email:
            errors.append('البريد الإلكتروني مطلوب')
        elif User.objects.filter(email=email).exists():
            errors.append('البريد الإلكتروني مستخدم بالفعل')
        
        if not password1:
            errors.append('كلمة المرور مطلوبة')
        elif len(password1) < 8:
            errors.append('كلمة المرور يجب أن تكون 8 أحرف على الأقل')
        
        if password1 != password2:
            errors.append('كلمة المرور وتأكيدها غير متطابقين')
        
        if not role:
            errors.append('الدور مطلوب')
        
        # التحقق من الفرع/المنطقة حسب الدور
        if role in ['employee', 'branch_manager'] and not branch:
            errors.append('الفرع مطلوب لهذا الدور')
        if role == 'region_manager' and not region:
            errors.append('المنطقة مطلوبة لهذا الدور')
        if role == 'region_manager' and region:
            try:
                from apps.branches.models import Branch
                valid_regions = {key for key, _ in Branch.REGION_CHOICES}
                if region not in valid_regions:
                    errors.append('المنطقة المحددة غير صحيحة')
            except Exception:
                pass
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            try:
                # إنشاء المستخدم
                user = User.objects.create_user(
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    password=password1
                )
                
                # إنشاء ملف المستخدم
                branch_obj = None
                if branch:
                    from apps.branches.models import Branch
                    try:
                        branch_obj = Branch.objects.get(pk=branch)
                    except Branch.DoesNotExist:
                        pass
                
                # استخدام ملف المستخدم الذي تم إنشاؤه بواسطة Signal
                profile = user.profile
                profile.role = role
                profile.phone = phone
                profile.branch = branch_obj
                profile.region = region if role == 'region_manager' else ''
                profile.save()
                
                messages.success(request, 'تم إنشاء الحساب بنجاح! يمكنك الآن تسجيل الدخول')
                return redirect('users:login')
            except Exception as e:
                messages.error(request, f'حدث خطأ في إنشاء الحساب: {str(e)}')
    
    # الحصول على الفروع للعرض في النموذج
    from apps.branches.models import Branch
    branches = Branch.objects.all()
    
    context = {
        'branches': branches,
        'roles': UserProfile.ROLE_CHOICES,
    }
    return render(request, 'users/register.html', context)


def logout_view(request):
    """تسجيل الخروج"""
    logout(request)
    return redirect('users:login')


@login_required
@login_required
def dashboard_view(request):
    """لوحة التحكم الرئيسية"""
    from apps.branches.models import Branch
    from apps.schedules.models import Schedule
    from apps.leaves.models import LeaveRequest
    from apps.approvals.models import ApprovalFlow
    from apps.employees.models import Employee
    
    user_profile = getattr(request.user, 'profile', None)
    
    # إحصائيات عامة
    total_users = User.objects.filter(is_active=True).count()
    active_users = UserProfile.objects.filter(status='active', user__is_active=True).count()
    
    # إحصائيات الفروع
    if request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.can_manage_branches):
        total_branches = Branch.objects.count()
    elif hasattr(request.user, 'profile') and request.user.profile.role == 'branch_manager' and request.user.profile.branch:
        total_branches = 1  # مدير المعرض يرى فرعه فقط
    else:
        total_branches = 0
    
    # إحصائيات الجداول
    if request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.can_create_schedules):
        active_schedules = Schedule.objects.filter(status__in=['active', 'approved']).count()
    elif hasattr(request.user, 'profile') and request.user.profile.role == 'branch_manager' and request.user.profile.branch:
        active_schedules = Schedule.objects.filter(
            branch=request.user.profile.branch,
            status__in=['active', 'approved']
        ).count()
    else:
        active_schedules = 0
    
    # إحصائيات الإجازات المعلقة
    if request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.can_approve_leaves):
        pending_leaves = LeaveRequest.objects.filter(status='pending').count()
    elif hasattr(request.user, 'profile') and request.user.profile.role == 'branch_manager' and request.user.profile.branch:
        # مدير المعرض يرى إجازات موظفي فرعه فقط
        pending_leaves = LeaveRequest.objects.filter(
            employee__profile__branch=request.user.profile.branch,
            status='pending'
        ).count()
    else:
        # الموظف يرى إجازاته فقط
        try:
            employee = Employee.objects.get(user=request.user)
            pending_leaves = LeaveRequest.objects.filter(employee=employee, status='pending').count()
        except Employee.DoesNotExist:
            pending_leaves = 0
    
    # إحصائيات الموافقات المعلقة
    if request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.can_approve_schedules):
        pending_approvals = ApprovalFlow.objects.filter(status='pending').count()
    else:
        # الموافقات المخصصة للمستخدم
        pending_approvals = ApprovalFlow.objects.filter(
            steps__assigned_to=request.user,
            steps__status='pending',
            status='in_progress'
        ).distinct().count()
    
    context = {
        'user_profile': user_profile,
        'total_users': total_users,
        'active_users': active_users,
        'total_branches': total_branches,
        'active_schedules': active_schedules,
        'pending_leaves': pending_leaves,
        'pending_approvals': pending_approvals,
    }
    
    return render(request, 'users/dashboard.html', context)


@login_required
def user_list_view(request):
    """قائمة المستخدمين"""
    search = request.GET.get('search', '')
    role = request.GET.get('role', '')
    status = request.GET.get('status', '')
    department = request.GET.get('department', '')
    
    # الحصول على المستخدمين حسب الصلاحيات (عرض UserProfile مع ربط User)
    base_qs = UserProfile.objects.select_related('user')
    if request.user.is_superuser:
        users = base_qs
    elif hasattr(request.user, 'profile'):
        if getattr(request.user.profile, 'can_manage_employees', False):
            users = base_qs
        else:
            users = base_qs.filter(user=request.user)
    else:
        users = base_qs.none()
    
    # تطبيق الفلاتر
    if search:
        users = users.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__username__icontains=search) |
            Q(user__email__icontains=search)
        )
    
    if role:
        users = users.filter(role=role)
    
    if status:
        users = users.filter(status=status)
    
    if department:
        users = users.filter(department__icontains=department)
    
    # الترقيم
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    users = paginator.get_page(page_number)
    
    context = {
        'users': users,
        'search': search,
        'role_filter': role,
        'status_filter': status,
        'department_filter': department,
        'roles': UserProfile.ROLE_CHOICES,
        'statuses': UserProfile.STATUS_CHOICES,
    }
    
    return render(request, 'users/list.html', context)


@login_required
def user_detail_view(request, user_id):
    """تفاصيل المستخدم"""
    user = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(UserProfile, user=user)
    
    # التحقق من الصلاحيات
    if not request.user.is_superuser and not (hasattr(request.user, 'profile') and request.user.profile.can_manage_employees):
        if user != request.user:
            messages.error(request, 'ليس لديك صلاحية لعرض هذا المستخدم')
            return redirect('users:list')
    
    context = {
        'user': user,
        'profile': profile,
    }
    
    return render(request, 'users/detail.html', context)


@login_required
def user_create_view(request):
    """إنشاء مستخدم جديد"""
    if not request.user.is_superuser and not (hasattr(request.user, 'profile') and request.user.profile.can_manage_employees):
        messages.error(request, 'ليس لديك صلاحية لإنشاء مستخدمين')
        return redirect('users:list')
    
    # الحصول على الفروع المتاحة
    from apps.branches.models import Branch
    branches = Branch.objects.all()
    regions_choices = Branch.REGION_CHOICES
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'تم إنشاء المستخدم {user.get_full_name()} بنجاح')
            return redirect('users:detail', user_id=user.id)
    else:
        form = UserRegistrationForm()
    
    context = {
        'form': form, 
        'title': 'إنشاء مستخدم جديد',
        'branches': branches,
        'regions_choices': regions_choices
    }
    return render(request, 'users/form.html', context)


@login_required
def user_edit_view(request, user_id):
    """تعديل المستخدم"""
    user = get_object_or_404(User, id=user_id)
    
    # التحقق من الصلاحيات
    if not request.user.is_superuser and not (hasattr(request.user, 'profile') and request.user.profile.can_manage_employees):
        if user != request.user:
            messages.error(request, 'ليس لديك صلاحية لتعديل هذا المستخدم')
            return redirect('users:list')
    
    # الحصول على الفروع المتاحة
    from apps.branches.models import Branch
    branches = Branch.objects.all()
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'تم تحديث المستخدم {user.get_full_name()} بنجاح')
            return redirect('users:detail', user_id=user.id)
    else:
        form = UserProfileForm(instance=user)
    
    context = {
        'form': form, 
        'title': 'تعديل المستخدم', 
        'user': user,
        'user_detail': user.profile if hasattr(user, 'profile') else None,
        'branches': branches,
        'regions_choices': Branch.REGION_CHOICES
    }
    return render(request, 'users/form.html', context)


@login_required
@require_http_methods(["DELETE"])
@csrf_exempt
def user_delete_view(request, user_id):
    """حذف المستخدم"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'ليس لديك صلاحية للحذف'})
    
    user = get_object_or_404(User, id=user_id)
    user_name = user.get_full_name() or user.username
    user.delete()
    
    return JsonResponse({'success': True, 'message': f'تم حذف المستخدم {user_name} بنجاح'})


@login_required
def profile_view(request):
    """الملف الشخصي للمستخدم الحالي"""
    profile = getattr(request.user, 'profile', None)
    if not profile:
        messages.error(request, 'لم يتم العثور على ملف المستخدم')
        return redirect('users:dashboard')
    
    context = {
        'profile': profile,
        'user': request.user
    }
    return render(request, 'users/profile.html', context)


@login_required
def profile_edit_view(request):
    """تعديل الملف الشخصي"""
    profile = getattr(request.user, 'profile', None)
    if not profile:
        messages.error(request, 'لم يتم العثور على ملف المستخدم')
        return redirect('users:dashboard')
    
    # الحصول على الفروع المتاحة
    from apps.branches.models import Branch
    branches = Branch.objects.all()
    
    if request.method == 'POST':
        try:
            # تحديث بيانات المستخدم
            request.user.first_name = request.POST.get('first_name', '')
            request.user.last_name = request.POST.get('last_name', '')
            request.user.username = request.POST.get('username', '')
            request.user.email = request.POST.get('email', '')
            request.user.save()
            
            # تحديث بيانات الملف الشخصي
            profile.phone = request.POST.get('phone', '')
            profile.position = request.POST.get('position', '')
            profile.department = request.POST.get('department', '')
            
            # التحقق من work_hours
            work_hours = request.POST.get('work_hours')
            if work_hours:
                profile.work_hours = int(work_hours)
            
            # التحقق من hire_date
            hire_date = request.POST.get('hire_date')
            if hire_date:
                profile.hire_date = hire_date
            else:
                profile.hire_date = None
                
            # التحقق من salary
            salary = request.POST.get('salary')
            if salary:
                profile.salary = float(salary)
            else:
                profile.salary = None
                
            profile.address = request.POST.get('address', '')
            profile.emergency_contact = request.POST.get('emergency_contact', '')
            profile.emergency_phone = request.POST.get('emergency_phone', '')
            profile.notes = request.POST.get('notes', '')
            
            # تحديث الفرع
            branch_id = request.POST.get('branch')
            if branch_id:
                try:
                    profile.branch = Branch.objects.get(id=branch_id)
                except Branch.DoesNotExist:
                    profile.branch = None
            else:
                profile.branch = None
            
            profile.save()
            
            messages.success(request, 'تم تحديث الملف الشخصي بنجاح')
            return redirect('users:profile')
            
        except Exception as e:
            messages.error(request, f'حدث خطأ في تحديث الملف الشخصي: {str(e)}')
            print(f"Error in profile_edit_view: {e}")
    
    context = {
        'profile': profile,
        'branches': branches,
        'user': request.user
    }
    return render(request, 'users/profile_edit.html', context)


# API Views
@login_required
def api_user_list(request):
    """API للحصول على قائمة المستخدمين"""
    search = request.GET.get('search', '')
    role = request.GET.get('role', '')
    
    profiles = UserProfile.objects.all()
    
    if search:
        profiles = profiles.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__username__icontains=search)
        )
    
    if role:
        profiles = profiles.filter(role=role)
    
    data = []
    for profile in profiles[:50]:  # حد أقصى 50 نتيجة
        data.append({
            'id': profile.user.id,
            'username': profile.user.username,
            'full_name': profile.user.get_full_name(),
            'role': profile.get_role_display(),
            'status': profile.get_status_display(),
            'job_id': profile.job_id,
        })
    
    return JsonResponse({'users': data})


@login_required
def api_user_detail(request, user_id):
    """API للحصول على تفاصيل المستخدم"""
    try:
        user = User.objects.get(id=user_id)
        profile = user.profile
        
        data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.get_full_name(),
            'role': profile.get_role_display(),
            'status': profile.get_status_display(),
            'job_id': profile.job_id,
            'phone': profile.phone,
            'position': profile.position,
            'department': profile.department,
            'hire_date': profile.hire_date.isoformat() if profile.hire_date else None,
            'salary': float(profile.salary) if profile.salary else None,
            'work_hours': profile.work_hours,
            'work_days': profile.work_days,
        }
        
        return JsonResponse({'user': data})
    except User.DoesNotExist:
        return JsonResponse({'error': 'المستخدم غير موجود'}, status=404)


@login_required
def change_password_view(request):
    """تغيير كلمة المرور للمستخدم الحالي"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تغيير كلمة المرور بنجاح')
            return redirect('users:profile')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'users/change_password.html', {'form': form})

@login_required
def api_regions(request):
    choices = []
    try:
        from apps.branches.models import Branch
        choices = [{'value': k, 'label': v} for k, v in Branch.REGION_CHOICES]
        db_ok = True
        try:
            Branch.objects.exists()
        except Exception:
            db_ok = False
    except Exception:
        choices = [{'value': k, 'label': v} for k, v in UserProfile.REGION_CHOICES]
        db_ok = False
    return JsonResponse({'regions': choices, 'db_ok': db_ok})
