#!/usr/bin/env python
"""
Docker staging runner script for worktable_system project.
"""

import os
import sys
import subprocess

def run_docker_staging():
    """Run the project using Docker in staging mode."""
    
    print("🐳 Starting project with Docker (staging mode)...")
    
    # Build and run with docker-compose for staging
    subprocess.run(['docker-compose', '-f', 'docker-compose.yml', '-f', 'docker-compose.staging.yml', 'up', '--build'])
    
    print("✅ Docker staging services started!")

if __name__ == '__main__':
    run_docker_staging()
