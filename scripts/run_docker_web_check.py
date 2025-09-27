#!/usr/bin/env python
"""
Docker web check script for worktable_system project.
"""

import os
import sys
import subprocess

def run_docker_web_check():
    """Run Django checks in Docker container."""
    
    print("🐳 Running Django checks in Docker container...")
    
    # Run checks
    subprocess.run(['docker-compose', 'exec', 'web', 'python', 'manage.py', 'check'])
    
    print("✅ Django checks completed!")

if __name__ == '__main__':
    run_docker_web_check()
