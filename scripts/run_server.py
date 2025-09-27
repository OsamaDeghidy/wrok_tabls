#!/usr/bin/env python
"""
Development server runner script for worktable_system project.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def run_server():
    """Run the development server."""
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktable_system.settings')
    django.setup()
    
    print("🚀 Starting development server...")
    print("🌐 Server will be available at http://127.0.0.1:8000")
    print("📊 Admin panel at http://127.0.0.1:8000/admin")
    print("⏹️  Press Ctrl+C to stop the server")
    
    # Run server
    execute_from_command_line(['manage.py', 'runserver'])

if __name__ == '__main__':
    run_server()
