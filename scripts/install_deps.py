#!/usr/bin/env python
"""
Dependencies installation script for worktable_system project.
"""

import os
import sys
import subprocess

def install_dependencies():
    """Install project dependencies."""
    
    print("📦 Installing dependencies...")
    
    # Install Python dependencies
    print("Installing Python packages...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
    
    # Install Node.js dependencies (if needed)
    if os.path.exists('package.json'):
        print("Installing Node.js packages...")
        subprocess.run(['npm', 'install'])
    
    print("✅ Dependencies installed successfully!")

if __name__ == '__main__':
    install_dependencies()
