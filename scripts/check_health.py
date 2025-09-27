#!/usr/bin/env python
"""
Health check script for worktable_system project.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def check_health():
    """Check the health of the project."""
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktable_system.settings')
    django.setup()
    
    print("🔍 Checking project health...")
    
    # Check database connection
    try:
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        print("✅ Database connection: OK")
    except Exception as e:
        print(f"❌ Database connection: FAILED - {e}")
    
    # Check Redis connection
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis connection: OK")
    except Exception as e:
        print(f"❌ Redis connection: FAILED - {e}")
    
    # Check static files
    try:
        from django.contrib.staticfiles import finders
        static_files = finders.find('css/theme.css')
        if static_files:
            print("✅ Static files: OK")
        else:
            print("❌ Static files: FAILED - theme.css not found")
    except Exception as e:
        print(f"❌ Static files: FAILED - {e}")
    
    # Check migrations
    try:
        from django.core.management import execute_from_command_line
        execute_from_command_line(['manage.py', 'check', '--deploy'])
        print("✅ Django checks: OK")
    except Exception as e:
        print(f"❌ Django checks: FAILED - {e}")
    
    print("✅ Health check completed!")

if __name__ == '__main__':
    check_health()
