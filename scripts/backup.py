#!/usr/bin/env python
"""
Backup script for worktable_system project.
"""

import os
import sys
import django
from datetime import datetime
from django.core.management import execute_from_command_line

def backup_database():
    """Backup the database."""
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktable_system.settings')
    django.setup()
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = 'backups'
    
    # Create backup directory
    os.makedirs(backup_dir, exist_ok=True)
    
    print(f"📦 Creating database backup...")
    
    # For SQLite
    if os.path.exists('db.sqlite3'):
        backup_file = f"{backup_dir}/db_backup_{timestamp}.sqlite3"
        os.system(f"cp db.sqlite3 {backup_file}")
        print(f"✅ Database backed up to {backup_file}")
    
    # For PostgreSQL (if configured)
    else:
        print("ℹ️  PostgreSQL backup not implemented yet")
    
    print("✅ Backup completed!")

if __name__ == '__main__':
    backup_database()
