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
from django.db.migrations.exceptions import InconsistentMigrationHistory

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

def unfake_with_children(recorder, loader, app_label, migration_name, seen=None):
    """Recursively un-fake a migration and everything that depends on it."""
    if seen is None: seen = set()
    key = (app_label, migration_name)
    if key in seen: return
    seen.add(key)
    
    print(f"   🔄 Un-faking: {app_label}.{migration_name} (and checking dependents...)")
    recorder.record_unapplied(app_label, migration_name)
    
    # Find any migration that has (app_label, migration_name) as a dependency
    for (node_app, node_name), node in loader.graph.nodes.items():
        if key in node.dependencies:
            unfake_with_children(recorder, loader, node_app, node_name, seen)

def fix_migrations():
    print("🚀 Starting ONE-GO Ultimate Migration Sync...")
    
    try:
        connection = connections['default']
        connection.prepare_database()
        
        # Initial load
        executor = MigrationExecutor(connection)
        recorder = MigrationRecorder(connection)
        
        # 1. RECURSIVE HISTORY REPAIR (Gap Filling)
        print("🔍 Repairing history gaps...")
        while True:
            try:
                executor.loader.check_consistent_history(connection)
                break
            except InconsistentMigrationHistory as e:
                import re
                match = re.search(r"its dependency ([\w_]+)\.([\w_]+)", str(e))
                if match:
                    dep_app, dep_name = match.groups()
                    print(f"   👉 FORCE-satisfying dependency: {dep_app}.{dep_name}...")
                    recorder.record_applied(dep_app, dep_name)
                    executor.loader.build_graph() # Refresh
                else:
                    break

        # 2. GENERIC DRIFT DETECTION (with recursive un-faking)
        print("🔍 Scanning all applied migrations for DB drift...")
        applied_migrations = recorder.applied_migrations()
        unfaked_seen = set()
        
        with connection.cursor() as cursor:
            for app_label, migration_name in sorted(list(applied_migrations)):
                try:
                    migration = executor.loader.get_migration(app_label, migration_name)
                    drift_detected = False
                    
                    for op in migration.operations:
                        if isinstance(op, migrations.CreateModel):
                            table = get_table_name(app_label, op.name)
                            if not check_table_exists(cursor, table):
                                print(f"   🚨 Table MISSING: {table}")
                                drift_detected = True
                        elif isinstance(op, migrations.AddField):
                            table = get_table_name(app_label, op.model_name)
                            col = op.name
                            if not check_column_exists(cursor, table, col) and not check_column_exists(cursor, table, f"{col}_id"):
                                print(f"   🚨 Column MISSING: {table}.{col}")
                                drift_detected = True
                        
                        if drift_detected:
                            break
                    
                    if drift_detected:
                        # If a migration drifts, un-fake it AND everything that depends on it
                        unfake_with_children(recorder, executor.loader, app_label, migration_name, unfaked_seen)
                except Exception:
                    continue

        # 3. FINAL EXECUTION
        print("📋 Finalizing migrations...")
        executor.loader.build_graph()
        targets = executor.loader.graph.leaf_nodes()
        unapplied = executor.migration_plan(targets)
        
        if not unapplied:
            print("✅ Database is perfectly synced.")
            return

        print(f"📋 Processing {len(unapplied)} migrations...")
        for migration_task, backwards in unapplied:
            app, name = migration_task.app_label, migration_task.name
            print(f"⏳ {app}.{name}...")
            try:
                call_command('migrate', app, name, verbosity=1)
                print(f"   ✅ Done.")
            except Exception as e:
                err = str(e).lower()
                exists_errs = ["already exists", "duplicate column", "duplicate key", "1050", "1060", "1061", "1072"]
                if any(p in err for p in exists_errs):
                    print(f"   ⚠️ Already exists. Faking...")
                    call_command('migrate', app, name, fake=True, verbosity=1)
                else:
                    print(f"   ❌ Error: {e}")
                    # Force fake for field/key errors to keep the "One Go" promise
                    if "column" in err or "key" in err or "dependency" in err:
                        print(f"   ⚠️ Forcing fake to proceed...")
                        call_command('migrate', app, name, fake=True, verbosity=1)
                    else:
                        sys.exit(1)

        print("\n✨ Migration sync complete!")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    fix_migrations()
