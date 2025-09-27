#!/usr/bin/env python
"""
Update dependencies script for worktable_system project.
"""

import os
import sys
import subprocess

def update_dependencies():
    """Update project dependencies."""
    
    print("🔄 Updating dependencies...")
    
    # Update Python dependencies
    print("Updating Python packages...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', '-r', 'requirements.txt'])
    
    # Update Node.js dependencies (if needed)
    if os.path.exists('package.json'):
        print("Updating Node.js packages...")
        subprocess.run(['npm', 'update'])
    
    print("✅ Dependencies updated successfully!")

if __name__ == '__main__':
    update_dependencies()
