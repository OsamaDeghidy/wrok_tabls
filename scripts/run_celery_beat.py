#!/usr/bin/env python
"""
Celery beat scheduler runner script for worktable_system project.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def run_celery_beat():
    """Run Celery beat scheduler."""
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktable_system.settings')
    django.setup()
    
    print("⏰ Starting Celery beat scheduler...")
    print("⏹️  Press Ctrl+C to stop the scheduler")
    
    # Run Celery beat
    execute_from_command_line(['manage.py', 'celery', 'beat', '--loglevel=info'])

if __name__ == '__main__':
    run_celery_beat()
