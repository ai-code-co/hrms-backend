import os
import django
import pymysql

# 1. Driver Setup
pymysql.version_info = (2, 2, 1, "final", 0)
pymysql.install_as_MySQLdb()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection, transaction
from django.core.management import call_command

def rebuild():
    print("🧨 Starting Nuclear TiDB Rebuild...")
    
    with connection.cursor() as cursor:
        print("🔍 Scanning for tables to drop...")
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Disable foreign key checks for dropping
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        for table in tables:
            print(f"🗑️  Dropping {table}...")
            cursor.execute(f"DROP TABLE IF EXISTS `{table}`")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    
    print("\n🏗️  Running Fresh Migrations...")
    call_command('migrate')
    
    print("\n📊 Populating Test Data...")
    # Import here after models are potentially refreshed in memory
    from populate_tidb_all import populate_db
    populate_db()
    
    print("\n✨ REBUILD COMPLETE! TiDB is now perfectly synced and populated.")

if __name__ == "__main__":
    rebuild()
