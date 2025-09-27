#!/usr/bin/env python
"""
Docker web shell script for worktable_system project.
"""

import os
import sys
import subprocess

def run_docker_web_shell():
    """Open Django shell in Docker container."""
    
    print("🐳 Opening Django shell in Docker container...")
    
    # Open Django shell
    subprocess.run(['docker-compose', 'exec', 'web', 'python', 'manage.py', 'shell'])
    
    print("✅ Django shell opened!")

if __name__ == '__main__':
    run_docker_web_shell()
