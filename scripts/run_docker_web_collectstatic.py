#!/usr/bin/env python
"""
Docker web collectstatic script for worktable_system project.
"""

import os
import sys
import subprocess

def run_docker_web_collectstatic():
    """Run collectstatic in Docker container."""
    
    print("🐳 Running collectstatic in Docker container...")
    
    # Run collectstatic
    subprocess.run(['docker-compose', 'exec', 'web', 'python', 'manage.py', 'collectstatic', '--noinput'])
    
    print("✅ Collectstatic completed!")

if __name__ == '__main__':
    run_docker_web_collectstatic()
