#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktable_system.settings')
django.setup()

from apps.users.models import User
from apps.branches.models import Branch, Shift

def create_test_data():
    print("إنشاء البيانات التجريبية...")
    
    # إنشاء فرع تجريبي
    branch, created = Branch.objects.get_or_create(
        code='MAIN001',
        defaults={
            'name': 'الفرع الرئيسي',
            'branch_type': 'main',
            'address': 'الرياض، المملكة العربية السعودية',
            'phone': '+966112345678',
            'email': 'main@company.com',
            'working_days': ['saturday', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday'],
            'is_active': True,
        }
    )
    
    if created:
        print(f"تم إنشاء الفرع: {branch.name}")
        
        # إنشاء شفتات للفرع
        shifts_data = [
            {
                'name': 'الشفت الصباحي',
                'start_time': '08:00',
                'end_time': '16:00',
                'break_start': '12:00',
                'break_end': '13:00',
            },
            {
                'name': 'الشفت المسائي',
                'start_time': '16:00',
                'end_time': '00:00',
                'break_start': '20:00',
                'break_end': '21:00',
            },
            {
                'name': 'الشفت الليلي',
                'start_time': '00:00',
                'end_time': '08:00',
                'break_start': '04:00',
                'break_end': '05:00',
            }
        ]
        
        for shift_data in shifts_data:
            shift, created = Shift.objects.get_or_create(
                branch=branch,
                name=shift_data['name'],
                defaults=shift_data
            )
            if created:
                print(f"تم إنشاء الشفت: {shift.name}")
    else:
        print(f"الفرع موجود بالفعل: {branch.name}")
    
    # إنشاء مستخدمين تجريبيين
    users_data = [
        {
            'username': 'admin',
            'email': 'admin@company.com',
            'first_name': 'أحمد',
            'last_name': 'المدير',
            'role': 'super_admin',
            'position': 'مدير عام',
            'department': 'الإدارة العليا',
            'is_staff': True,
            'is_superuser': True,
        },
        {
            'username': 'manager1',
            'email': 'manager1@company.com',
            'first_name': 'فاطمة',
            'last_name': 'علي',
            'role': 'branch_manager',
            'position': 'مديرة الفرع',
            'department': 'الإدارة',
            'branch': branch,
        },
        {
            'username': 'coordinator1',
            'email': 'coordinator1@company.com',
            'first_name': 'محمد',
            'last_name': 'حسن',
            'role': 'coordinator',
            'position': 'منسق العمليات',
            'department': 'العمليات',
            'branch': branch,
        },
        {
            'username': 'employee1',
            'email': 'employee1@company.com',
            'first_name': 'سارة',
            'last_name': 'أحمد',
            'role': 'employee',
            'position': 'موظف مبيعات',
            'department': 'المبيعات',
            'branch': branch,
            'job_id': 'EMP001',
            'work_hours': 8,
        }
    ]
    
    for user_data in users_data:
        username = user_data.pop('username')
        user, created = User.objects.get_or_create(
            username=username,
            defaults=user_data
        )
        
        if created:
            # تعيين كلمة مرور افتراضية
            user.set_password('password123')
            user.save()
            print(f"تم إنشاء المستخدم: {user.get_full_name()} ({user.username})")
        else:
            print(f"المستخدم موجود بالفعل: {user.get_full_name()} ({user.username})")
    
    print("\nتم إنشاء البيانات التجريبية بنجاح!")
    print("\nحسابات تجريبية:")
    print("1. مدير عام - admin / password123")
    print("2. مديرة الفرع - manager1 / password123")
    print("3. منسق العمليات - coordinator1 / password123")
    print("4. موظف مبيعات - employee1 / password123")

if __name__ == '__main__':
    create_test_data()


