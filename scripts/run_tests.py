#!/usr/bin/env python
"""
Test runner script for worktable_system project.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def run_tests():
    """Run all tests for the project."""
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktable_system.settings')
    django.setup()
    
    print("🧪 Running tests...")
    
    # Run tests
    execute_from_command_line(['manage.py', 'test'])
    
    print("✅ Tests completed!")

if __name__ == '__main__':
    run_tests()
