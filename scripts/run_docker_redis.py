#!/usr/bin/env python
"""
Docker Redis script for worktable_system project.
"""

import os
import sys
import subprocess

def run_docker_redis():
    """Open Redis shell in Docker container."""
    
    print("🐳 Opening Redis shell in Docker container...")
    
    # Open Redis shell
    subprocess.run(['docker-compose', 'exec', 'redis', 'redis-cli'])
    
    print("✅ Redis shell opened!")

if __name__ == '__main__':
    run_docker_redis()
