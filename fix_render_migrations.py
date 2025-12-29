#!/usr/bin/env python
"""
Fix migration state mismatch on Render deployment.
Run this when migrations fail with "Table already exists" errors.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command
from django.db import connection

def fix_migrations():
    print("🔧 Fixing migration state mismatch...")
    
    # Get list of tables that exist
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES")
        existing_tables = [row[0] for row in cursor.fetchall()]
    
    print(f"📊 Found {len(existing_tables)} existing tables")
    
    # Apps to fake migrations for
    apps_to_fake = [
        'admin',
        'auth',
        'contenttypes',
        'sessions',
        'token_blacklist',
        'auth_app',
        'employees',
        'attendance',
        'holidays',
        'leaves',
        'payroll',
        'inventory',
        'notifications',
        'departments',
        'organizations',
        'jet',
    ]
    
    for app in apps_to_fake:
        # Check if app has any tables
        app_has_tables = any(app in table.lower() for table in existing_tables)
        
        if app_has_tables:
            print(f"✅ Faking ALL migrations for {app}...")
            try:
                call_command('migrate', app, '--fake', verbosity=0)
            except Exception as e:
                print(f"⚠️  {app}: {e}")
        else:
            print(f"⏭️  Skipping {app} (no tables)")
    
    print("\n✨ Migration state fixed! Starting server...")

if __name__ == "__main__":
    fix_migrations()
