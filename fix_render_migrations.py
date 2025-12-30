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
from django.db import connections, OperationalError, ProgrammingError, migrations
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

def get_table_name(app_label, model_name):
    """Predict table name for a model."""
    return f"{app_label}_{model_name.lower()}"

def fix_migrations():
    print("🚀 Starting ULTIMATE robust migration process...")
    
    try:
        connection = connections['default']
        connection.prepare_database()
        
        # We need a temporary executor to load the migration files
        temp_executor = MigrationExecutor(connection)
        recorder = MigrationRecorder(connection)
        
        # 1. GENERIC DRIFT DETECTION
        print("🔍 Scanning all applied migrations for DB drift...")
        applied_migrations = recorder.applied_migrations() # Set of (app, name)
        
        unfaked_any = False
        with connection.cursor() as cursor:
            # Sort applied migrations to process them in order
            sorted_applied = sorted(list(applied_migrations))
            
            for app_label, migration_name in sorted_applied:
                try:
                    migration = temp_executor.loader.get_migration(app_label, migration_name)
                    drift_detected = False
                    
                    for op in migration.operations:
                        if isinstance(op, migrations.CreateModel):
                            table = get_table_name(app_label, op.name)
                            if not check_table_exists(cursor, table):
                                print(f"   🚨 Table MISSING: {table} (from {app_label}.{migration_name})")
                                drift_detected = True
                        elif isinstance(op, migrations.AddField):
                            table = get_table_name(app_label, op.model_name)
                            if not check_column_exists(cursor, table, op.name):
                                print(f"   � Column MISSING: {table}.{op.name} (from {app_label}.{migration_name})")
                                drift_detected = True
                        
                        if drift_detected:
                            break
                    
                    if drift_detected:
                        print(f"   🔄 Un-faking {app_label}.{migration_name} and its descendants...")
                        # Un-fake this and everything after it in this app to be safe
                        for a, n in sorted_applied:
                            if a == app_label and n >= migration_name:
                                recorder.record_unapplied(a, n)
                        unfaked_any = True
                except Exception:
                    # Skip migrations we can't load or parse (3rd party etc)
                    continue

        # 2. RUN MIGRATIONS
        # Refresh executor to see new unapplied migrations
        executor = MigrationExecutor(connection)
        executor.loader.build_graph() 
        
        targets = executor.loader.graph.leaf_nodes()
        unapplied = executor.migration_plan(targets)
        
        if not unapplied:
            print("✅ Database is already perfectly synced.")
            return

        print(f"📋 Processing {len(unapplied)} pending/re-synced migrations...")
        
        for migration_task, backwards in unapplied:
            app_label = migration_task.app_label
            migration_name = migration_task.name
            
            print(f"⏳ {app_label}.{migration_name}...")
            
            try:
                # Try to apply normally
                call_command('migrate', app_label, migration_name, verbosity=1)
                print(f"   ✅ Done.")
            except (OperationalError, ProgrammingError, Exception) as e:
                err_str = str(e).lower()
                # Patterns that indicate the table/column/index already exists
                exists_errs = ["already exists", "duplicate column", "duplicate key", "1050", "1060", "1061"]
                
                if any(p in err_str for p in exists_errs):
                    print(f"   ⚠️ Existing object detected. Fake-applying...")
                    call_command('migrate', app_label, migration_name, fake=True, verbosity=1)
                else:
                    print(f"   ❌ Critical error: {e}")
                    sys.exit(1)

        print("\n✨ Migration sync complete!")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    fix_migrations()
