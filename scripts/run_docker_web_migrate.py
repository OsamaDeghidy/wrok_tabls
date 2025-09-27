#!/usr/bin/env python
"""
Docker web migrate script for worktable_system project.
"""

import os
import sys
import subprocess

def run_docker_web_migrate():
    """Run migrations in Docker container."""
    
    print("🐳 Running migrations in Docker container...")
    
    # Run migrations
    subprocess.run(['docker-compose', 'exec', 'web', 'python', 'manage.py', 'migrate'])
    
    print("✅ Migrations completed!")

if __name__ == '__main__':
    run_docker_web_migrate()
