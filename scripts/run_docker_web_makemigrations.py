#!/usr/bin/env python
"""
Docker web makemigrations script for worktable_system project.
"""

import os
import sys
import subprocess

def run_docker_web_makemigrations():
    """Run makemigrations in Docker container."""
    
    print("🐳 Running makemigrations in Docker container...")
    
    # Run makemigrations
    subprocess.run(['docker-compose', 'exec', 'web', 'python', 'manage.py', 'makemigrations'])
    
    print("✅ Makemigrations completed!")

if __name__ == '__main__':
    run_docker_web_makemigrations()
