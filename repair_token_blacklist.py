import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def repair():
    with connection.cursor() as cursor:
        print("Starting Database Repair for Token Blacklist...")
        
        # 1. Drop the corrupted tables
        print("Dropping corrupted tables...")
        cursor.execute("DROP TABLE IF EXISTS token_blacklist_blacklistedtoken;")
        cursor.execute("DROP TABLE IF EXISTS token_blacklist_outstandingtoken;")
        
        # 2. Clear migration history so Django re-runs them correctly
        print("Clearing migration history for token_blacklist...")
        cursor.execute("DELETE FROM django_migrations WHERE app = 'token_blacklist';")
        
        print("Repair complete! Now run 'python manage.py migrate' to recreate tables correctly.")

if __name__ == "__main__":
    repair()
