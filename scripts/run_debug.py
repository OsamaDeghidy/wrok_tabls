#!/usr/bin/env python
"""
Debug server runner script for worktable_system project.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def run_debug():
    """Run the debug server."""
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktable_system.settings')
    django.setup()
    
    print("🐛 Starting debug server...")
    print("🌐 Server will be available at http://127.0.0.1:8000")
    print("📊 Admin panel at http://127.0.0.1:8000/admin")
    print("🔍 Debug toolbar enabled")
    print("⏹️  Press Ctrl+C to stop the server")
    
    # Run server with debug settings
    execute_from_command_line(['manage.py', 'runserver', '--settings=config.settings.dev', '--verbosity=2'])

if __name__ == '__main__':
    run_debug()
