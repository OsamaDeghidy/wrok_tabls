#!/usr/bin/env python
"""
Docker web script for worktable_system project.
"""

import os
import sys
import subprocess

def run_docker_web():
    """Open web shell in Docker container."""
    
    print("🐳 Opening web shell in Docker container...")
    
    # Open web shell
    subprocess.run(['docker-compose', 'exec', 'web', 'bash'])
    
    print("✅ Web shell opened!")

if __name__ == '__main__':
    run_docker_web()
