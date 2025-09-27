#!/usr/bin/env python
"""
Docker development runner script for worktable_system project.
"""

import os
import sys
import subprocess

def run_docker_dev():
    """Run the project using Docker in development mode."""
    
    print("🐳 Starting project with Docker (development mode)...")
    
    # Build and run with docker-compose for development
    subprocess.run(['docker-compose', '-f', 'docker-compose.yml', '-f', 'docker-compose.dev.yml', 'up', '--build'])
    
    print("✅ Docker development services started!")

if __name__ == '__main__':
    run_docker_dev()
