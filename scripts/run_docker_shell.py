#!/usr/bin/env python
"""
Docker shell script for worktable_system project.
"""

import os
import sys
import subprocess

def run_docker_shell():
    """Open shell in Docker container."""
    
    print("🐳 Opening shell in Docker container...")
    
    # Open shell in web container
    subprocess.run(['docker-compose', 'exec', 'web', 'bash'])
    
    print("✅ Docker shell opened!")

if __name__ == '__main__':
    run_docker_shell()
