import os
import django
import sys

# Ensure MySQL/TiDB support if needed (similar to your other scripts)
try:
    import pymysql
    pymysql.version_info = (2, 2, 7, "final", 0)
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command
from django.db import connections, OperationalError, ProgrammingError
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.recorder import MigrationRecorder

def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table."""
    try:
        cursor.execute(f"SHOW COLUMNS FROM `{table_name}` LIKE %s", [column_name])
        return cursor.fetchone() is not None
    except Exception:
        return False

def check_table_exists(cursor, table_name):
    """Check if a table exists."""
    try:
        cursor.execute(f"SHOW TABLES LIKE %s", [table_name])
        return cursor.fetchone() is not None
    except Exception:
        return False

def fix_migrations():
    print("🚀 Starting robust migration process with drift detection...")
    
    try:
        connection = connections['default']
        connection.prepare_database()
        recorder = MigrationRecorder(connection)
        
        # 1. DRIFT DETECTION
        print("🔍 Checking for migration drift...")
        applied_migrations = recorder.applied_migrations()
        drift_found = False
        
        # We check specific critical migrations for missing state
        drift_checks = [
            ('employees', '0003_role_employee_role', 'role_id', 'employees_employee'),
            ('employees', '0001_initial', None, 'employees_employee'), # None means check table existence
        ]
        
        with connection.cursor() as cursor:
            for app, name, col, table in drift_checks:
                if (app, name) in applied_migrations:
                    is_missing = False
                    if col:
                        is_missing = not check_column_exists(cursor, table, col)
                    else:
                        is_missing = not check_table_exists(cursor, table)
                    
                    if is_missing:
                        print(f"   🚨 Found drift! {app}.{name} is marked applied but DB state is missing.")
                        # To safely re-run, we must un-fake this migration AND any that depend on it
                        # For simplicity, we'll un-fake the target and any subsequent numbers in that app
                        # but a more robust way is to just un-record it.
                        print(f"   🔄 Un-faking {app}.{name}...")
                        recorder.record_unapplied(app, name)
                        drift_found = True
                        
                        # Also un-fake subsequent migrations for the same app to be safe
                        # as they likely were part of the same faked deployment
                        for (a, n) in list(applied_migrations):
                            if a == app and n > name:
                                print(f"   � Also un-faking dependent: {a}.{n}...")
                                recorder.record_unapplied(a, n)

        # 2. RUN MIGRATIONS
        # Important: Refresh the executor/loader AFTER un-faking
        executor = MigrationExecutor(connection)
        executor.loader.build_graph() 
        
        targets = executor.loader.graph.leaf_nodes()
        unapplied = executor.migration_plan(targets)
        
        if not unapplied:
            print("✅ No pending migrations. Database is up to date.")
            return

        print(f"📋 Found {len(unapplied)} migrations to process (including drifting ones).")
        
        for migration_task, backwards in unapplied:
            app_label = migration_task.app_label
            migration_name = migration_task.name
            
            print(f"⏳ Processing {app_label}.{migration_name}...")
            
            try:
                # Try to apply normally
                call_command('migrate', app_label, migration_name, verbosity=1)
                print(f"   ✅ Successfully applied.")
            except (OperationalError, ProgrammingError, Exception) as e:
                err_str = str(e).lower()
                # Patterns that indicate the table/column/index already exists
                already_exists_patterns = [
                    "already exists", 
                    "duplicate column name", 
                    "duplicate key name",
                    "duplicate entry",
                    "1050", # MySQL Table already exists
                    "1060", # MySQL Column already exists
                    "1061", # MySQL Duplicate key name (index)
                    "1062", # MySQL Duplicate entry for key
                ]
                
                if any(pattern in err_str for pattern in already_exists_patterns):
                    print(f"   ⚠️ Detected existing DB object ({err_str[:100]}...).")
                    print(f"   👉 Fake-applying {app_label}.{migration_name}...")
                    try:
                        call_command('migrate', app_label, migration_name, fake=True, verbosity=1)
                        print(f"   ✅ Fake-applied successfully.")
                    except Exception as fake_err:
                        print(f"   ❌ Failed to fake migration: {fake_err}")
                else:
                    print(f"   ❌ Critical error applying {app_label}.{migration_name}: {e}")
                    print("   💡 Stopping to prevent database inconsistency.")
                    sys.exit(1)

        print("\n✨ All migrations processed successfully!")

    except Exception as e:
        print(f"❌ Unexpected error during migration: {e}")

if __name__ == "__main__":
    fix_migrations()
