#!/usr/bin/env python
"""
Docker runner script for worktable_system project.
"""

import os
import sys
import subprocess

def run_docker():
    """Run the project using Docker."""
    
    print("🐳 Starting project with Docker...")
    
    # Build and run with docker-compose
    subprocess.run(['docker-compose', 'up', '--build'])
    
    print("✅ Docker services started!")

if __name__ == '__main__':
    run_docker()
