import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def check_tables():
    tables_to_check = [
        'auth_app_user',
        'organizations_company',
        'departments_department',
        'departments_designation',
        'employees_employee',
        'inventory_devicetype',
        'inventory_device',
        'inventory_deviceassignment',
        'leaves_leave',
        'attendance_attendance'
    ]
    
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
    print("--- Database Table Check ---")
    all_ok = True
    for table in tables_to_check:
        if table in existing_tables:
            print(f"✅ {table} exists.")
        else:
            print(f"❌ {table} MISSING!")
            all_ok = False
            
    if all_ok:
        print("\nAll core tables exist. Migration seems healthy.")
    else:
        print("\nSome tables are missing. This is likely the cause of the 500 error.")

if __name__ == "__main__":
    check_tables()
