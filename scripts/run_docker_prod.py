#!/usr/bin/env python
"""
Docker production runner script for worktable_system project.
"""

import os
import sys
import subprocess

def run_docker_prod():
    """Run the project using Docker in production mode."""
    
    print("🐳 Starting project with Docker (production mode)...")
    
    # Build and run with docker-compose for production
    subprocess.run(['docker-compose', '-f', 'docker-compose.yml', '-f', 'docker-compose.prod.yml', 'up', '--build'])
    
    print("✅ Docker production services started!")

if __name__ == '__main__':
    run_docker_prod()
