import os
import django
from datetime import datetime, timedelta, date, time
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktable_system.settings')
django.setup()

from django.contrib.auth.models import User
from apps.users.models import UserProfile
from apps.branches.models import Branch, BranchShift
from apps.employees.models import Employee
from apps.schedules.models import Schedule, ScheduleEntry

def create_users_and_branches():
    print("جاري إنشاء بيانات الفروع التجريبية...")
    
    # 1. إنشاء المعارض الإضافية
    branches_info = [
        {"name": "معرض الرياض الرئيسي", "code": "1001", "shifts": [
            ("الشفت الصباحي", time(8, 0), time(16, 0)),
            ("الشفت المسائي", time(16, 0), time(0, 0)),
        ]},
        {"name": "معرض جدة", "code": "2001", "shifts": [
            ("الشفت الأول", time(9, 0), time(13, 0)),
            ("الشفت الثاني", time(17, 0), time(21, 0)),
        ]},
        {"name": "معرض الدمام", "code": "3001", "shifts": [
            ("الشفت الصباحي", time(8, 0), time(16, 0)),
            ("الشفت المسائي", time(16, 0), time(0, 0)),
        ]},
        {"name": "معرض مكة", "code": "4001", "shifts": [
            ("الشفت الصباحي", time(7, 0), time(15, 0)),
            ("الشفت المسائي", time(15, 0), time(23, 0)),
        ]},
        {"name": "معرض الخبر", "code": "5001", "shifts": [
            ("الشفت الصباحي", time(9, 0), time(17, 0)),
            ("الشفت المسائي", time(17, 0), time(1, 0)),
        ]},
    ]
    
    branches = {}
    for b in branches_info:
        branch, _ = Branch.objects.get_or_create(
            name=b["name"],
            defaults={
                'code': b["code"],
                'type': 'branch',
                'category': 'A',
                'status': 'active',
                'working_days': ['saturday', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday']
            }
        )
        branches[b["code"]] = branch
        
        for s_name, s_start, s_end in b["shifts"]:
            BranchShift.objects.get_or_create(
                branch=branch, name=s_name,
                defaults={'start_time': s_start, 'end_time': s_end, 'days': ['saturday', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday'], 'is_active': True}
            )

    print("جاري إنشاء حسابات المدراء ومسؤولين الموافقات...")
    # 2. إنشاء المدراء
    managers = [
        ('admin_manager1', 'admin_mgr@test.com', 'أحمد', 'مدير الإدارة', 'admin_manager', None),
        ('ops_manager1', 'ops_mgr@test.com', 'سالم', 'مدير العمليات', 'operations_manager', None),
        ('region_manager1', 'reg_mgr@test.com', 'عمر', 'مدير المنطقة', 'region_manager', None),
        ('coordinator1', 'coord@test.com', 'فهد', 'المنسق', 'coordinator', None),
    ]
    
    for code, branch in branches.items():
        managers.append((f'bm_{code}', f'bm_{code}@test.com', f'مدير_{code}', 'الفرع', 'branch_manager', branch))

    for uname, email, fname, lname, role, branch in managers:
        user, created = User.objects.get_or_create(username=uname, defaults={'email': email, 'first_name': fname, 'last_name': lname})
        if created:
            user.set_password('pass1234')
            user.save()
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = role
        if branch:
            profile.branch = branch
        profile.save()

    print("جاري إنشاء الموظفين للمعطيات الجديدة...")
    # 3. إنشاء الموظفين (5 موظفين لكل فرع)
    employees_data = []
    for code, branch in branches.items():
        # 3 موظفين بدوام 8 ساعات
        for i in range(1, 4):
            employees_data.append((f'emp{i}_{code}_8h', f'emp{i}_{code}_8h@test.com', f'موظف{i} {code}', branch, 8))
        # موظفين بدوام 9 ساعات
        for i in range(4, 6):
            employees_data.append((f'emp{i}_{code}_9h', f'emp{i}_{code}_9h@test.com', f'موظف{i} {code}', branch, 9))

    for uname, email, fname, branch, whours in employees_data:
        user, created = User.objects.get_or_create(username=uname, defaults={'email': email, 'first_name': fname, 'last_name': 'توزيع'})
        if created:
            user.set_password('pass1234')
            user.save()
        
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = 'employee'
        profile.branch = branch
        profile.work_hours = whours
        profile.work_days = 6 if whours == 8 else 5
        profile.save()

        Employee.objects.get_or_create(
            user=user,
            defaults={
                'job_title': 'بائع',
                'employment_type': 'full_time',
                'status': 'active',
                'hire_date': date(2023, 1, 1),
                'employee_number': f'EMP-{code}-{user.id}'
            }
        )

    print("جاري إنشاء الجداول التشغيلية وتوزيع الموظفين فيها بشكل ذكي...")
    # 4. توزيع الموظفين على جداول سابقة وحالية ومستقبلية
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday() + 2) # السبت
    if start_of_week > today:
        start_of_week -= timedelta(days=7)
        
    weeks = [
        (start_of_week - timedelta(days=7), 'approved'),       # جدول الأسبوع الماضي (مُعتمد)
        (start_of_week, 'pending_coordinator'),                # جدول الأسبوع الحالي (بانتظار المنسق)
        (start_of_week + timedelta(days=7), 'draft'),          # مسودة للرداسة الأسبوع القادم
    ]

    for sd, status in weeks:
        ed = sd + timedelta(days=6)
        for code, branch in branches.items():
            schedule, created_sched = Schedule.objects.get_or_create(
                branch=branch,
                start_date=sd,
                end_date=ed,
                defaults={
                    'schedule_type': 'weekly',
                    'status': status,
                    'notes': f'الجدول التلقائي ({status})',
                    'created_by': User.objects.get(username=f'bm_{code}')
                }
            )
            
            if created_sched: # نفذ التوزيع فقط إذا الجدول انعمل جديد
                shifts = list(BranchShift.objects.filter(branch=branch, is_active=True))
                employees = list(User.objects.filter(profile__branch=branch, profile__role='employee'))
                
                # توزيع الموظفين
                for emp in employees:
                    max_days = emp.profile.work_days
                    whours = emp.profile.work_hours
                    assigned_days = 0
                    current_date = sd
                    
                    while current_date <= ed and assigned_days < max_days:
                        # احتمالية 20% أن يكون يوم الجمعة راحة، وإلا داوم عادي
                        if current_date.weekday() == 4 and random.random() < 0.2:
                            current_date += timedelta(days=1)
                            continue
                            
                        # اختيار شفت عشوائي لهذا الموظف في هذا اليوم
                        shift = random.choice(shifts)
                        
                        start_time_d = datetime.combine(date.today(), shift.start_time)
                        end_time_d = datetime.combine(date.today(), shift.end_time)
                        if end_time_d <= start_time_d:
                            end_time_d += timedelta(days=1)
                        total_shift_hours = (end_time_d - start_time_d).total_seconds() / 3600
                        
                        # حساب الساعات المخصصة لهذا الشفت (لا يمكن تتجاوز ساعات الموظف)
                        assigned_hours = min(whours, total_shift_hours)
                        
                        # إنشاء إدخال التوزيع
                        ScheduleEntry.objects.create(
                            schedule=schedule,
                            employee=emp,
                            date=current_date,
                            shift=shift,
                            start_time=shift.start_time,
                            end_time=shift.end_time,
                            hours=assigned_hours
                        )
                        assigned_days += 1
                        current_date += timedelta(days=1)


    print("\n=============================================")
    print("✅ تم بنجاح إنشاء 5 معارض مع الجداول وتوزيع الموظفين بالكامل!")
    print("=============================================")
    print("تم الآن إضافة معارض (الرياض، جدة، الدمام، مكة، الخبر).")
    print("كل معرض لديه 5 موظفين (3 يعملون 8 ساعات، و2 يعملون 9 ساعات).")
    print("لكل فرع تم إنشاء 3 جداول:")
    print(" - الأسبوع الماضي: جدول معتمد (approved)")
    print(" - الأسبوع الحالي: في مسار الموافقة (pending_coordinator)")
    print(" - الأسبوع القادم: مسودة (draft)")
    print("وتم توزيع جميع الموظفين تلقائياً بحيث لا يتجاوزون الحد الأقصى لأيام العمل!")
    print("=============================================\n")

if __name__ == '__main__':
    create_users_and_branches()
