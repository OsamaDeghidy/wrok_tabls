#!/usr/bin/env python
"""
Docker logs script for worktable_system project.
"""

import os
import sys
import subprocess

def run_docker_logs():
    """Show Docker service logs."""
    
    print("🐳 Showing Docker service logs...")
    
    # Show logs for all services
    subprocess.run(['docker-compose', 'logs', '-f'])
    
    print("✅ Docker logs displayed!")

if __name__ == '__main__':
    run_docker_logs()
