#!/usr/bin/env python
"""
Staging server runner script for worktable_system project.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def run_staging():
    """Run the staging server."""
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktable_system.settings')
    django.setup()
    
    print("🚀 Starting staging server...")
    print("🌐 Server will be available at http://0.0.0.0:8000")
    print("⏹️  Press Ctrl+C to stop the server")
    
    # Run server with staging settings
    execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000', '--settings=config.settings.staging'])

if __name__ == '__main__':
    run_staging()
