#!/usr/bin/env python
"""
Docker web runserver_plus script for worktable_system project.
"""

import os
import sys
import subprocess

def run_docker_web_runserver_plus():
    """Run Django runserver_plus in Docker container."""
    
    print("🐳 Running Django runserver_plus in Docker container...")
    
    # Run runserver_plus
    subprocess.run(['docker-compose', 'exec', 'web', 'python', 'manage.py', 'runserver_plus', '0.0.0.0:8000'])
    
    print("✅ Django runserver_plus completed!")

if __name__ == '__main__':
    run_docker_web_runserver_plus()