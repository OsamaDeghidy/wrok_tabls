#!/usr/bin/env python
"""
Docker local runner script for worktable_system project.
"""

import os
import sys
import subprocess

def run_docker_local():
    """Run the project using Docker in local mode."""
    
    print("🐳 Starting project with Docker (local mode)...")
    
    # Build and run with docker-compose for local development
    subprocess.run(['docker-compose', '-f', 'docker-compose.yml', '-f', 'docker-compose.local.yml', 'up', '--build'])
    
    print("✅ Docker local services started!")

if __name__ == '__main__':
    run_docker_local()
