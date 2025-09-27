#!/usr/bin/env python
"""
Production server runner script for worktable_system project.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def run_production():
    """Run the production server."""
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktable_system.settings')
    django.setup()
    
    print("🚀 Starting production server...")
    print("🌐 Server will be available at http://0.0.0.0:8000")
    print("⏹️  Press Ctrl+C to stop the server")
    
    # Run server with production settings
    execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000', '--settings=config.settings.prod'])

if __name__ == '__main__':
    run_production()
