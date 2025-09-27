#!/usr/bin/env python
"""
Docker database script for worktable_system project.
"""

import os
import sys
import subprocess

def run_docker_db():
    """Open database shell in Docker container."""
    
    print("🐳 Opening database shell in Docker container...")
    
    # Open database shell
    subprocess.run(['docker-compose', 'exec', 'db', 'psql', '-U', 'postgres', '-d', 'worktable_db'])
    
    print("✅ Database shell opened!")

if __name__ == '__main__':
    run_docker_db()
