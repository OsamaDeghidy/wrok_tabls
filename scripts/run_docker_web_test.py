#!/usr/bin/env python
"""
Docker web test script for worktable_system project.
"""

import os
import sys
import subprocess

def run_docker_web_test():
    """Run tests in Docker container."""
    
    print("🐳 Running tests in Docker container...")
    
    # Run tests
    subprocess.run(['docker-compose', 'exec', 'web', 'python', 'manage.py', 'test'])
    
    print("✅ Tests completed!")

if __name__ == '__main__':
    run_docker_web_test()
