#!/usr/bin/env python
"""
Run all services script for worktable_system project.
"""

import os
import sys
import django
import subprocess
import threading
import time

def run_server():
    """Run the development server."""
    os.system('python manage.py runserver')

def run_celery():
    """Run Celery worker."""
    os.system('celery -A worktable_system worker -l info')

def run_celery_beat():
    """Run Celery beat scheduler."""
    os.system('celery -A worktable_system beat -l info')

def run_all():
    """Run all services."""
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktable_system.settings')
    django.setup()
    
    print("🚀 Starting all services...")
    print("🌐 Server: http://127.0.0.1:8000")
    print("📊 Admin: http://127.0.0.1:8000/admin")
    print("⏹️  Press Ctrl+C to stop all services")
    
    # Start services in separate threads
    server_thread = threading.Thread(target=run_server)
    celery_thread = threading.Thread(target=run_celery)
    beat_thread = threading.Thread(target=run_celery_beat)
    
    server_thread.start()
    time.sleep(2)  # Wait for server to start
    
    celery_thread.start()
    time.sleep(1)  # Wait for celery to start
    
    beat_thread.start()
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⏹️  Stopping all services...")
        sys.exit(0)

if __name__ == '__main__':
    run_all()
