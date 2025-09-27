#!/usr/bin/env python
"""
Docker all services runner script for worktable_system project.
"""

import os
import sys
import subprocess

def run_docker_all():
    """Run all services using Docker."""
    
    print("🐳 Starting all services with Docker...")
    
    # Build and run all services with docker-compose
    subprocess.run(['docker-compose', 'up', '--build', '-d'])
    
    print("✅ All Docker services started!")
    print("🌐 Web: http://localhost:8000")
    print("📊 Admin: http://localhost:8000/admin")
    print("⏹️  Run 'docker-compose down' to stop all services")

if __name__ == '__main__':
    run_docker_all()
