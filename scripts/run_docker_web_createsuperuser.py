#!/usr/bin/env python
"""
Docker web createsuperuser script for worktable_system project.
"""

import os
import sys
import subprocess

def run_docker_web_createsuperuser():
    """Run createsuperuser in Docker container."""
    
    print("🐳 Running createsuperuser in Docker container...")
    
    # Run createsuperuser
    subprocess.run(['docker-compose', 'exec', 'web', 'python', 'manage.py', 'createsuperuser'])
    
    print("✅ Createsuperuser completed!")

if __name__ == '__main__':
    run_docker_web_createsuperuser()
