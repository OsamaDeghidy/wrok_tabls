#!/usr/bin/env python
"""
Setup script for worktable_system project.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def setup_project():
    """Setup the project with initial data."""
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktable_system.settings')
    django.setup()
    
    print("🚀 Setting up worktable_system project...")
    
    # Run migrations
    print("📦 Running migrations...")
    execute_from_command_line(['manage.py', 'makemigrations'])
    execute_from_command_line(['manage.py', 'migrate'])
    
    # Create superuser
    print("👤 Creating superuser...")
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@worktable.com',
            password='admin123'
        )
        print("✅ Superuser created: admin/admin123")
    else:
        print("ℹ️  Superuser already exists")
    
    # Create sample data
    print("📊 Creating sample data...")
    create_sample_data()
    
    print("✅ Project setup completed!")
    print("🌐 Run 'python manage.py runserver' to start the development server")

def create_sample_data():
    """Create sample data for development."""
    from apps.branches.models import Branch
    from apps.employees.models import Employee
    from apps.users.models import User
    
    # Create sample branches
    if not Branch.objects.exists():
        branches = [
            {'name': 'فرع الرياض', 'code': 'RYD001', 'category': 'A'},
            {'name': 'فرع جدة', 'code': 'JED001', 'category': 'B'},
            {'name': 'فرع الدمام', 'code': 'DMM001', 'category': 'C'},
        ]
        
        for branch_data in branches:
            Branch.objects.create(**branch_data)
        
        print("✅ Sample branches created")
    
    # Create sample employees
    if not Employee.objects.exists():
        branch = Branch.objects.first()
        if branch:
            employees = [
                {'employee_number': '98979001', 'first_name': 'أحمد', 'last_name': 'محمد', 'branch': branch},
                {'employee_number': '98979002', 'first_name': 'فاطمة', 'last_name': 'علي', 'branch': branch},
                {'employee_number': '98979003', 'first_name': 'خالد', 'last_name': 'سعد', 'branch': branch},
            ]
            
            for emp_data in employees:
                Employee.objects.create(**emp_data)
            
            print("✅ Sample employees created")

if __name__ == '__main__':
    setup_project()
