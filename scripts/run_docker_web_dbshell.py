#!/usr/bin/env python
"""
Docker web dbshell script for worktable_system project.
"""

import os
import sys
import subprocess

def run_docker_web_dbshell():
    """Run Django dbshell in Docker container."""
    
    print("🐳 Running Django dbshell in Docker container...")
    
    # Run dbshell
    subprocess.run(['docker-compose', 'exec', 'web', 'python', 'manage.py', 'dbshell'])
    
    print("✅ Django dbshell completed!")

if __name__ == '__main__':
    run_docker_web_dbshell()
