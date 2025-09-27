#!/usr/bin/env python
"""
Docker web shell_plus script for worktable_system project.
"""

import os
import sys
import subprocess

def run_docker_web_shell_plus():
    """Run Django shell_plus in Docker container."""
    
    print("🐳 Running Django shell_plus in Docker container...")
    
    # Run shell_plus
    subprocess.run(['docker-compose', 'exec', 'web', 'python', 'manage.py', 'shell_plus'])
    
    print("✅ Django shell_plus completed!")

if __name__ == '__main__':
    run_docker_web_shell_plus()
