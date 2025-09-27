#!/usr/bin/env python
"""
Docker restart script for worktable_system project.
"""

import os
import sys
import subprocess

def run_docker_restart():
    """Restart all Docker services."""
    
    print("🐳 Restarting all Docker services...")
    
    # Stop all services
    subprocess.run(['docker-compose', 'down'])
    
    # Start all services
    subprocess.run(['docker-compose', 'up', '--build', '-d'])
    
    print("✅ All Docker services restarted!")

if __name__ == '__main__':
    run_docker_restart()
