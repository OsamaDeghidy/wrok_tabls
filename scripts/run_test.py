#!/usr/bin/env python
"""
Test server runner script for worktable_system project.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def run_test():
    """Run the test server."""
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktable_system.settings')
    django.setup()
    
    print("🧪 Starting test server...")
    print("🌐 Server will be available at http://127.0.0.1:8000")
    print("📊 Admin panel at http://127.0.0.1:8000/admin")
    print("⏹️  Press Ctrl+C to stop the server")
    
    # Run server with test settings
    execute_from_command_line(['manage.py', 'runserver', '--settings=config.settings.test'])

if __name__ == '__main__':
    run_test()
