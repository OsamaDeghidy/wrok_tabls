from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.db import transaction, models
from django.contrib.auth.models import User
from .models import UserProfile
from apps.branches.models import Branch

def LoginView(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user:
                if user.is_active:
                    login(request, user)
                    messages.success(request, f'مرحباً {user.get_full_name()}!')
                    return redirect('dashboard:index')
                else:
                    messages.error(request, 'حسابك غير نشط. يرجى التواصل مع الإدارة')
            else:
                messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة')
        else:
            messages.error(request, 'يرجى ملء جميع الحقول')
    
    return render(request, 'users/login.html')

def LogoutView(request):
    from django.contrib.auth import logout
    logout(request)
    messages.info(request, 'تم تسجيل الخروج بنجاح')
    return redirect('users:login')

def ForgotPasswordView(request):
    return HttpResponse("Forgot Password")

def ResetPasswordView(request, token):
    return HttpResponse(f"Reset Password: {token}")

@login_required
def UserProfileView(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        messages.error(request, 'ملفك الشخصي غير موجود')
        return redirect('users:edit_profile')
    
    return render(request, 'users/profile.html', {'user_profile': user_profile})

@login_required
def UserEditProfileView(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        messages.error(request, 'ملفك الشخصي غير موجود')
        return redirect('users:profile')
    
    if request.method == 'POST':
        try:
            # تحديث البيانات الأساسية
            request.user.first_name = request.POST.get('first_name', request.user.first_name)
            request.user.last_name = request.POST.get('last_name', request.user.last_name)
            request.user.email = request.POST.get('email', request.user.email)
            request.user.save()
            
            # تحديث بيانات الملف الشخصي
            user_profile.phone = request.POST.get('phone', user_profile.phone)
            user_profile.position = request.POST.get('position', user_profile.position)
            user_profile.department = request.POST.get('department', user_profile.department)
            user_profile.save()
            
            messages.success(request, 'تم تحديث الملف الشخصي بنجاح')
            return redirect('users:profile')
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء تحديث الملف الشخصي: {str(e)}')
    
    return render(request, 'users/edit_profile.html', {'user_profile': user_profile})

@login_required
def UserChangePasswordView(request):
    if request.method == 'POST':
        try:
            from django.contrib.auth import update_session_auth_hash
            from django.contrib.auth.forms import PasswordChangeForm
            
            form = PasswordChangeForm(request.user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)  # Important!
                messages.success(request, 'تم تغيير كلمة المرور بنجاح')
                return redirect('users:profile')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء تغيير كلمة المرور: {str(e)}')
    
    return render(request, 'users/change_password.html')

@login_required
def UserListView(request):
    # الحصول على ملف المستخدم الشخصي
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        messages.error(request, 'ملفك الشخصي غير موجود')
        return redirect('users:profile')
    
    # التحقق من الصلاحيات
    if not user_profile.can_manage_employees:
        messages.error(request, 'ليس لديك صلاحية لعرض قائمة المستخدمين')
        return redirect('dashboard:index')
    
    # الحصول على المستخدمين حسب الصلاحيات
    if user_profile.can_view_all_branches:
        user_profiles = UserProfile.objects.select_related('user', 'branch').all()
    else:
        # مدير المعرض يرى موظفي فرعه فقط
        user_profiles = UserProfile.objects.select_related('user', 'branch').filter(branch=user_profile.branch)
    
    # فلترة حسب الدور
    role_filter = request.GET.get('role')
    if role_filter:
        user_profiles = user_profiles.filter(role=role_filter)
    
    # فلترة حسب الفرع
    branch_filter = request.GET.get('branch')
    if branch_filter:
        user_profiles = user_profiles.filter(branch_id=branch_filter)
    
    # فلترة حسب الحالة
    status_filter = request.GET.get('status')
    if status_filter:
        user_profiles = user_profiles.filter(status=status_filter)
    
    # فلترة حسب البحث
    search = request.GET.get('search')
    if search:
        user_profiles = user_profiles.filter(
            models.Q(user__first_name__icontains=search) |
            models.Q(user__last_name__icontains=search) |
            models.Q(user__username__icontains=search) |
            models.Q(user__email__icontains=search) |
            models.Q(job_id__icontains=search) |
            models.Q(phone__icontains=search)
        )
    
    # فلترة حسب القسم
    department_filter = request.GET.get('department')
    if department_filter:
        user_profiles = user_profiles.filter(department__icontains=department_filter)
    
    context = {
        'users': user_profiles,
        'branches': Branch.objects.filter(is_active=True),
        'roles': UserProfile.ROLE_CHOICES,
        'statuses': UserProfile.STATUS_CHOICES,
        'search': search,
        'role_filter': role_filter,
        'branch_filter': branch_filter,
        'status_filter': status_filter,
        'department_filter': department_filter,
    }
    
    return render(request, 'users/list.html', context)

@login_required
def UserCreateView(request):
    # الحصول على ملف المستخدم الشخصي
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        messages.error(request, 'ملفك الشخصي غير موجود')
        return redirect('users:profile')
    
    # التحقق من الصلاحيات
    if not user_profile.can_manage_employees:
        messages.error(request, 'ليس لديك صلاحية لإضافة مستخدمين')
        return redirect('users:list')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # استخراج البيانات
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                username = request.POST.get('username')
                email = request.POST.get('email')
                password = request.POST.get('password')
                phone = request.POST.get('phone', '')
                role = request.POST.get('role')
                branch_id = request.POST.get('branch')
                job_id = request.POST.get('job_id', '')
                work_hours = request.POST.get('work_hours', 8)
                position = request.POST.get('position', '')
                department = request.POST.get('department', '')
                
                # التحقق من البيانات
                if not all([first_name, last_name, username, email, password, role]):
                    messages.error(request, 'يرجى ملء جميع الحقول المطلوبة')
                    return render(request, 'users/form.html')
                
                # إنشاء المستخدم الأساسي
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                
                # إنشاء ملف المستخدم الشخصي
                user_profile = UserProfile.objects.create(
                    user=user,
                    phone=phone,
                    role=role,
                    job_id=job_id,
                    work_hours=int(work_hours),
                    position=position,
                    department=department
                )
                
                # تعيين الفرع
                if branch_id:
                    try:
                        branch = Branch.objects.get(id=branch_id)
                        user_profile.branch = branch
                        user_profile.save()
                    except Branch.DoesNotExist:
                        messages.error(request, 'الفرع المحدد غير موجود')
                        return render(request, 'users/form.html')
                
                messages.success(request, f'تم إنشاء المستخدم {user.get_full_name()} بنجاح')
                return redirect('users:detail', pk=user_profile.id)
                
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء إنشاء المستخدم: {str(e)}')
    
    context = {
        'branches': Branch.objects.filter(is_active=True),
        'roles': UserProfile.ROLE_CHOICES,
        'work_hours_choices': UserProfile.WORK_HOURS_CHOICES,
    }
    
    return render(request, 'users/form.html', context)

@login_required
def UserDetailView(request, pk):
    user_detail = get_object_or_404(UserProfile, id=pk)
    
    # الحصول على ملف المستخدم الشخصي الحالي
    try:
        current_user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        messages.error(request, 'ملفك الشخصي غير موجود')
        return redirect('users:profile')
    
    # التحقق من الصلاحيات
    if not current_user_profile.can_manage_employees:
        if user_detail.user.id != request.user.id:
            messages.error(request, 'ليس لديك صلاحية لعرض تفاصيل هذا المستخدم')
            return redirect('dashboard:index')
    
    # مدير المعرض يمكنه رؤية موظفي فرعه فقط
    if current_user_profile.can_manage_own_branch_only:
        if user_detail.branch != current_user_profile.branch:
            messages.error(request, 'يمكنك رؤية موظفي فرعك فقط')
            return redirect('users:list')
    
    return render(request, 'users/detail.html', {'user_detail': user_detail})

@login_required
def UserEditView(request, pk):
    user_detail = get_object_or_404(UserProfile, id=pk)
    
    # الحصول على ملف المستخدم الشخصي الحالي
    try:
        current_user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        messages.error(request, 'ملفك الشخصي غير موجود')
        return redirect('users:profile')
    
    # التحقق من الصلاحيات
    if not current_user_profile.can_manage_employees:
        if user_detail.user.id != request.user.id:
            messages.error(request, 'ليس لديك صلاحية لتعديل هذا المستخدم')
            return redirect('dashboard:index')
    
    # مدير المعرض يمكنه تعديل موظفي فرعه فقط
    if current_user_profile.can_manage_own_branch_only:
        if user_detail.branch != current_user_profile.branch:
            messages.error(request, 'يمكنك تعديل موظفي فرعك فقط')
            return redirect('users:list')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # تحديث البيانات الأساسية
                user_detail.user.first_name = request.POST.get('first_name', user_detail.user.first_name)
                user_detail.user.last_name = request.POST.get('last_name', user_detail.user.last_name)
                user_detail.user.email = request.POST.get('email', user_detail.user.email)
                user_detail.user.save()
                
                # تحديث بيانات الملف الشخصي
                user_detail.phone = request.POST.get('phone', user_detail.phone)
                user_detail.role = request.POST.get('role', user_detail.role)
                user_detail.job_id = request.POST.get('job_id', user_detail.job_id)
                user_detail.work_hours = int(request.POST.get('work_hours', user_detail.work_hours))
                user_detail.position = request.POST.get('position', user_detail.position)
                user_detail.department = request.POST.get('department', user_detail.department)
                user_detail.status = request.POST.get('status', user_detail.status)
                
                # تحديث الفرع
                branch_id = request.POST.get('branch')
                if branch_id:
                    try:
                        branch = Branch.objects.get(id=branch_id)
                        user_detail.branch = branch
                    except Branch.DoesNotExist:
                        messages.error(request, 'الفرع المحدد غير موجود')
                        return render(request, 'users/form.html', {'user_detail': user_detail})
                
                user_detail.save()
                messages.success(request, f'تم تحديث المستخدم {user_detail.user.get_full_name()} بنجاح')
                return redirect('users:detail', pk=user_detail.id)
                
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء تحديث المستخدم: {str(e)}')
    
    context = {
        'user_detail': user_detail,
        'branches': Branch.objects.filter(is_active=True),
        'roles': UserProfile.ROLE_CHOICES,
        'work_hours_choices': UserProfile.WORK_HOURS_CHOICES,
        'statuses': UserProfile.STATUS_CHOICES,
    }
    
    return render(request, 'users/form.html', context)

@login_required
def UserDeleteView(request, pk):
    user_detail = get_object_or_404(UserProfile, id=pk)
    
    # الحصول على ملف المستخدم الشخصي الحالي
    try:
        current_user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        messages.error(request, 'ملفك الشخصي غير موجود')
        return redirect('users:profile')
    
    # التحقق من الصلاحيات
    if not current_user_profile.can_manage_employees:
        messages.error(request, 'ليس لديك صلاحية لحذف المستخدمين')
        return redirect('users:list')
    
    # مدير المعرض يمكنه حذف موظفي فرعه فقط
    if current_user_profile.can_manage_own_branch_only:
        if user_detail.branch != current_user_profile.branch:
            messages.error(request, 'يمكنك حذف موظفي فرعك فقط')
            return redirect('users:list')
    
    # منع حذف المستخدم نفسه
    if user_detail.user.id == request.user.id:
        messages.error(request, 'لا يمكنك حذف حسابك الخاص')
        return redirect('users:list')
    
    if request.method == 'POST':
        try:
            user_name = user_detail.user.get_full_name()
            user_detail.user.delete()  # حذف المستخدم الأساسي سيحذف الملف الشخصي تلقائياً
            messages.success(request, f'تم حذف المستخدم {user_name} بنجاح')
            return redirect('users:list')
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حذف المستخدم: {str(e)}')
    
    return render(request, 'users/delete_confirm.html', {'user_detail': user_detail})

def RegisterView(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # استخراج البيانات من النموذج
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                username = request.POST.get('username')
                email = request.POST.get('email')
                password1 = request.POST.get('password1')
                password2 = request.POST.get('password2')
                phone = request.POST.get('phone', '')
                role = request.POST.get('role')
                branch_id = request.POST.get('branch')
                
                # التحقق من صحة البيانات
                if password1 != password2:
                    messages.error(request, 'كلمة المرور غير متطابقة')
                    return render(request, 'users/register.html')
                
                if not all([first_name, last_name, username, email, password1, role]):
                    messages.error(request, 'يرجى ملء جميع الحقول المطلوبة')
                    return render(request, 'users/register.html')
                
                # التحقق من وجود المستخدم
                if User.objects.filter(username=username).exists():
                    messages.error(request, 'اسم المستخدم موجود بالفعل')
                    return render(request, 'users/register.html')
                
                if User.objects.filter(email=email).exists():
                    messages.error(request, 'البريد الإلكتروني موجود بالفعل')
                    return render(request, 'users/register.html')
                
                # إنشاء المستخدم الأساسي
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password1,
                    first_name=first_name,
                    last_name=last_name
                )
                
                # إنشاء ملف المستخدم الشخصي
                user_profile = UserProfile.objects.create(
                    user=user,
                    phone=phone,
                    role=role
                )
                
                # تعيين الفرع إذا كان مطلوباً
                if branch_id and role in ['employee', 'branch_manager']:
                    try:
                        branch = Branch.objects.get(id=branch_id)
                        user_profile.branch = branch
                        user_profile.save()
                    except Branch.DoesNotExist:
                        messages.error(request, 'الفرع المحدد غير موجود')
                        return render(request, 'users/register.html')
                
                # تسجيل الدخول التلقائي
                user = authenticate(username=username, password=password1)
                if user:
                    login(request, user)
                    messages.success(request, f'مرحباً {user.get_full_name()}! تم إنشاء حسابك بنجاح')
                    return redirect('dashboard:index')
                
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء إنشاء الحساب: {str(e)}')
    
    # عرض النموذج
    branches = Branch.objects.filter(status='active')
    return render(request, 'users/register.html', {'branches': branches})