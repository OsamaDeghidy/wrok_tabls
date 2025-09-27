#!/usr/bin/env python
"""
Docker stop script for worktable_system project.
"""

import os
import sys
import subprocess

def run_docker_stop():
    """Stop all Docker services."""
    
    print("🐳 Stopping all Docker services...")
    
    # Stop all services
    subprocess.run(['docker-compose', 'down'])
    
    print("✅ All Docker services stopped!")

if __name__ == '__main__':
    run_docker_stop()
