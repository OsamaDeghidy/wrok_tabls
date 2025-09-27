#!/usr/bin/env python
"""
Docker debug runner script for worktable_system project.
"""

import os
import sys
import subprocess

def run_docker_debug():
    """Run the project using Docker in debug mode."""
    
    print("🐳 Starting project with Docker (debug mode)...")
    
    # Build and run with docker-compose for debugging
    subprocess.run(['docker-compose', '-f', 'docker-compose.yml', '-f', 'docker-compose.debug.yml', 'up', '--build'])
    
    print("✅ Docker debug services started!")

if __name__ == '__main__':
    run_docker_debug()
