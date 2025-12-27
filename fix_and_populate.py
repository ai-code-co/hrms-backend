import os
import django
import pymysql
import sys

# 1. Driver Fix (Bypass macOS dlopen issues and Django version check)
pymysql.version_info = (2, 2, 1, "final", 0)
pymysql.install_as_MySQLdb()

# 2. Django Setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def fix_schema_and_populate():
    with connection.cursor() as cursor:
        print("🔍 Checking TiDB Schema...")
        cursor.execute("DESCRIBE departments_designation")
        columns = [row[0] for row in cursor.fetchall()]
        
        if 'department_id' not in columns:
            print("🧹  Truncating corrupt departments_designation table...")
            cursor.execute("TRUNCATE TABLE departments_designation")
            print("🏗️  Fixing missing column: departments_designation.department_id")
            cursor.execute("ALTER TABLE departments_designation ADD COLUMN department_id bigint(20) NOT NULL")
            cursor.execute("ALTER TABLE departments_designation ADD CONSTRAINT fk_designation_department FOREIGN KEY (department_id) REFERENCES departments_department(id)")
            print("✅ Schema fixed.")
        else:
            print("✅ Schema matches.")

    # Now import and run population
    from populate_tidb_all import populate_db
    populate_db()

if __name__ == "__main__":
    fix_schema_and_populate()
