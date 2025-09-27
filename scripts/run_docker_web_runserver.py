#!/usr/bin/env python
"""
Docker web runserver script for worktable_system project.
"""

import os
import sys
import subprocess

def run_docker_web_runserver():
    """Run Django runserver in Docker container."""
    
    print("🐳 Running Django runserver in Docker container...")
    
    # Run runserver
    subprocess.run(['docker-compose', 'exec', 'web', 'python', 'manage.py', 'runserver', '0.0.0.0:8000'])
    
    print("✅ Django runserver completed!")

if __name__ == '__main__':
    run_docker_web_runserver()
