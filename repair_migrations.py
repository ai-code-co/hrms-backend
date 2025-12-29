
import os
import django
from django.db import connection
from django.core.management import call_command

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

def table_exists(table_name):
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES LIKE %s", [table_name])
        return cursor.fetchone() is not None

def repair_migrations():
    print("🔧 Starting Generic Migration Repair...")

    # Map of App Label -> Main Table Name (to check existence)
    # This covers the most likely breakdown points in your project.
    apps_to_check = {
        # Core & Auth
        'auth_app': 'auth_app_user',
        'admin': 'django_admin_log',
        'auth': 'auth_group',
        'contenttypes': 'django_content_type',
        'sessions': 'django_session',

        # Local Apps
        'token_blacklist': 'token_blacklist_blacklistedtoken',
        'inventory': 'inventory_device',  # or inventory_devicetype
        'leaves': 'leaves_leave',
        'employees': 'employees_employee',
        'attendance': 'attendance_attendance',
        'departments': 'departments_department',
        'holidays': 'holidays_holiday',
        'payroll': 'payroll_payslip',
        'organizations': 'organizations_company',
        'notifications': 'notifications_notification',
        'jet': 'jet_pinnedapplication', # Third party
    }

    for app, table in apps_to_check.items():
        print(f"🔍 Checking {app} (Table: {table})...")
        try:
            if table_exists(table):
                print(f"   ⚠️ Table '{table}' EXISTS. Fake-applying {app}.0001...")
                # We specifically fake 0001 because that's what creates the table
                call_command('migrate', app, '0001', fake=True)
                print(f"   ✅ {app}.0001 fake-applied.")
            else:
                print(f"   ℹ️ Table '{table}' missing. Will be created normally.")
        except Exception as e:
            print(f"   ❌ Error checking/faking {app}: {e}")

    # After checking/faking individual apps, run the full migrate to catch up everything else
    print("\n🚀 Running standard migrate for all apps (catch-up mode)...")
    try:
        call_command('migrate')
        print("✅ All migrations applied successfully!")
    except Exception as e:
        print(f"❌ Database migration failed: {e}")

if __name__ == "__main__":
    repair_migrations()
