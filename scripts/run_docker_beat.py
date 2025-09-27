#!/usr/bin/env python
"""
Docker Celery Beat script for worktable_system project.
"""

import os
import sys
import subprocess

def run_docker_beat():
    """Open Celery Beat shell in Docker container."""
    
    print("🐳 Opening Celery Beat shell in Docker container...")
    
    # Open Celery Beat shell
    subprocess.run(['docker-compose', 'exec', 'celery-beat', 'celery', '-A', 'worktable_system', 'shell'])
    
    print("✅ Celery Beat shell opened!")

if __name__ == '__main__':
    run_docker_beat()
