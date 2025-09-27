#!/usr/bin/env python
"""
Cleanup script for worktable_system project.
"""

import os
import sys
import shutil
import django
from django.core.management import execute_from_command_line

def cleanup():
    """Clean up temporary files and caches."""
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktable_system.settings')
    django.setup()
    
    print("🧹 Cleaning up project...")
    
    # Remove Python cache files
    for root, dirs, files in os.walk('.'):
        for dir_name in dirs:
            if dir_name == '__pycache__':
                shutil.rmtree(os.path.join(root, dir_name))
                print(f"✅ Removed {os.path.join(root, dir_name)}")
    
    # Remove .pyc files
    for root, dirs, files in os.walk('.'):
        for file_name in files:
            if file_name.endswith('.pyc'):
                os.remove(os.path.join(root, file_name))
                print(f"✅ Removed {os.path.join(root, file_name)}")
    
    # Remove log files
    if os.path.exists('logs'):
        shutil.rmtree('logs')
        print("✅ Removed logs directory")
    
    # Remove static files
    if os.path.exists('staticfiles'):
        shutil.rmtree('staticfiles')
        print("✅ Removed staticfiles directory")
    
    # Remove media files (optional)
    if os.path.exists('media'):
        shutil.rmtree('media')
        print("✅ Removed media directory")
    
    print("✅ Cleanup completed!")

if __name__ == '__main__':
    cleanup()
