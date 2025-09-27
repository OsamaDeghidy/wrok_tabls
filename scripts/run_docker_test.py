#!/usr/bin/env python
"""
Docker test runner script for worktable_system project.
"""

import os
import sys
import subprocess

def run_docker_test():
    """Run the project using Docker in test mode."""
    
    print("🐳 Starting project with Docker (test mode)...")
    
    # Build and run with docker-compose for testing
    subprocess.run(['docker-compose', '-f', 'docker-compose.yml', '-f', 'docker-compose.test.yml', 'up', '--build'])
    
    print("✅ Docker test services started!")

if __name__ == '__main__':
    run_docker_test()
