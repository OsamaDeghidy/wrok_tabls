#!/usr/bin/env python
"""
Celery worker runner script for worktable_system project.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def run_celery():
    """Run Celery worker."""
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktable_system.settings')
    django.setup()
    
    print("🔄 Starting Celery worker...")
    print("⏹️  Press Ctrl+C to stop the worker")
    
    # Run Celery worker
    execute_from_command_line(['manage.py', 'celery', 'worker', '--loglevel=info'])

if __name__ == '__main__':
    run_celery()
