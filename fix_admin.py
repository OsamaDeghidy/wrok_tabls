#!/usr/bin/env python
"""
Script to fix admin issues and apply migrations
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktable_system.settings')
django.setup()

from django.core.management import execute_from_command_line

def main():
    print("🔧 إصلاح مشاكل الإدارة...")
    
    # Apply migrations
    print("1. تطبيق المايجريشن...")
    try:
        execute_from_command_line(['manage.py', 'migrate'])
        print("✅ تم تطبيق المايجريشن بنجاح")
    except Exception as e:
        print(f"❌ خطأ في المايجريشن: {e}")
        return
    
    # Create superuser
    print("2. إنشاء مستخدم superuser...")
    try:
        from django.contrib.auth.models import User
        from apps.users.models import UserProfile
        
        # Check if admin exists
        if User.objects.filter(username='admin').exists():
            print("✅ المستخدم admin موجود بالفعل")
            admin_user = User.objects.get(username='admin')
        else:
            # Create admin user
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@company.com',
                password='admin123',
                first_name='المدير',
                last_name='العام'
            )
            print("✅ تم إنشاء مستخدم admin بنجاح")
        
        # Create UserProfile for admin
        if not UserProfile.objects.filter(user=admin_user).exists():
            UserProfile.objects.create(
                user=admin_user,
                role='super_admin',
                job_id='ADMIN001',
                work_hours=8,
                position='مدير عام',
                department='الإدارة العليا'
            )
            print("✅ تم إنشاء ملف المستخدم الشخصي للمدير")
        
        print("\n🎉 تم إصلاح المشاكل بنجاح!")
        print("\n📋 معلومات تسجيل الدخول:")
        print("🌐 الرابط: http://127.0.0.1:5000/admin/")
        print("👤 اسم المستخدم: admin")
        print("🔑 كلمة المرور: admin123")
        
    except Exception as e:
        print(f"❌ خطأ في إنشاء المستخدم: {e}")

if __name__ == '__main__':
    main()


