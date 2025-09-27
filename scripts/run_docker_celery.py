#!/usr/bin/env python
"""
Docker Celery script for worktable_system project.
"""

import os
import sys
import subprocess

def run_docker_celery():
    """Open Celery shell in Docker container."""
    
    print("🐳 Opening Celery shell in Docker container...")
    
    # Open Celery shell
    subprocess.run(['docker-compose', 'exec', 'celery', 'celery', '-A', 'worktable_system', 'shell'])
    
    print("✅ Celery shell opened!")

if __name__ == '__main__':
    run_docker_celery()
