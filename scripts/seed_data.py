#!/usr/bin/env python
"""
Seed data script for worktable_system project.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def seed_data():
    """Seed the database with initial data."""
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktable_system.settings')
    django.setup()
    
    print("🌱 Seeding database with initial data...")
    
    # Import models
    from apps.users.models import User
    from apps.branches.models import Branch
    from apps.employees.models import Employee
    from apps.schedules.models import Schedule
    from apps.leaves.models import LeaveRequest
    from apps.violations.models import Violation
    
    # Create users
    if not User.objects.exists():
        users = [
            {'username': 'admin', 'email': 'admin@worktable.com', 'first_name': 'مدير', 'last_name': 'النظام', 'is_staff': True, 'is_superuser': True},
            {'username': 'manager1', 'email': 'manager1@worktable.com', 'first_name': 'أحمد', 'last_name': 'المدير', 'is_staff': True},
            {'username': 'coordinator1', 'email': 'coordinator1@worktable.com', 'first_name': 'فاطمة', 'last_name': 'المنسق', 'is_staff': False},
        ]
        
        for user_data in users:
            user = User.objects.create_user(**user_data)
            if user_data['username'] == 'admin':
                user.set_password('admin123')
            else:
                user.set_password('password123')
            user.save()
        
        print("✅ Users created")
    
    # Create branches
    if not Branch.objects.exists():
        branches = [
            {'name': 'فرع الرياض الرئيسي', 'code': 'RYD001', 'category': 'A', 'region': 'الرياض', 'open_time': '08:00', 'close_time': '22:00'},
            {'name': 'فرع جدة', 'code': 'JED001', 'category': 'B', 'region': 'جدة', 'open_time': '09:00', 'close_time': '21:00'},
            {'name': 'فرع الدمام', 'code': 'DMM001', 'category': 'C', 'region': 'الدمام', 'open_time': '10:00', 'close_time': '20:00'},
        ]
        
        for branch_data in branches:
            Branch.objects.create(**branch_data)
        
        print("✅ Branches created")
    
    # Create employees
    if not Employee.objects.exists():
        branch = Branch.objects.first()
        if branch:
            employees = [
                {'employee_number': '98979001', 'first_name': 'أحمد', 'last_name': 'محمد', 'branch': branch, 'job_title': 'مدير فرع'},
                {'employee_number': '98979002', 'first_name': 'فاطمة', 'last_name': 'علي', 'branch': branch, 'job_title': 'منسق'},
                {'employee_number': '98979003', 'first_name': 'خالد', 'last_name': 'سعد', 'branch': branch, 'job_title': 'موظف'},
                {'employee_number': '98979004', 'first_name': 'نورا', 'last_name': 'حسن', 'branch': branch, 'job_title': 'موظف'},
            ]
            
            for emp_data in employees:
                Employee.objects.create(**emp_data)
            
            print("✅ Employees created")
    
    print("✅ Database seeded successfully!")

if __name__ == '__main__':
    seed_data()
