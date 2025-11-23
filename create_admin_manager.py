#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktable_system.settings')
django.setup()

from django.contrib.auth.models import User
from apps.users.models import UserProfile

def create_admin_manager():
    """إنشاء مستخدم مدير الإدارة"""
    try:
        # إنشاء المستخدم
        admin_manager = User.objects.create_user(
            username='admin_manager',
            email='admin_manager@example.com',
            password='admin123',
            first_name='مدير',
            last_name='الإدارة'
        )
        
        # إنشاء البروفايل
        profile = UserProfile.objects.create(
            user=admin_manager,
            role='admin_manager',
            status='active',
            phone='01234567890'
        )
        
        print('✅ تم إنشاء مدير الإدارة بنجاح!')
        print(f'👤 اسم المستخدم: admin_manager')
        print(f'🔑 كلمة المرور: admin123')
        print(f'🎭 الدور: {profile.role}')
        print(f'📊 الحالة: {profile.status}')
        print(f'📞 الهاتف: {profile.phone}')
        
        return admin_manager
        
    except Exception as e:
        print(f'❌ خطأ في إنشاء مدير الإدارة: {e}')
        return None

if __name__ == '__main__':
    create_admin_manager()