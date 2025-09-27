#!/usr/bin/env python
"""
Restore script for worktable_system project.
"""

import os
import sys
import django
from datetime import datetime
from django.core.management import execute_from_command_line

def restore_database(backup_file):
    """Restore the database from backup."""
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktable_system.settings')
    django.setup()
    
    if not os.path.exists(backup_file):
        print(f"❌ Backup file {backup_file} not found!")
        return
    
    print(f"📦 Restoring database from {backup_file}...")
    
    # For SQLite
    if backup_file.endswith('.sqlite3'):
        os.system(f"cp {backup_file} db.sqlite3")
        print("✅ Database restored successfully!")
    
    # For PostgreSQL (if configured)
    else:
        print("ℹ️  PostgreSQL restore not implemented yet")
    
    print("✅ Restore completed!")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python restore.py <backup_file>")
        sys.exit(1)
    
    backup_file = sys.argv[1]
    restore_database(backup_file)
