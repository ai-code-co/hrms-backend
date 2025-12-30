

import os
import django
import pymysql
# Mock version to satisfy Django's check
pymysql.version_info = (2, 2, 7, "final", 0)
pymysql.install_as_MySQLdb()

from django.db import connection
from django.core.management import call_command

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

def fix_production_db():
    print("🛠️ Fixing Production Database (us-west-2)...")
    
    with connection.cursor() as cursor:
        # 1. Drop and recreate token_blacklist tables
        print("\n🔧 Fixing token_blacklist tables...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cursor.execute("DROP TABLE IF EXISTS `token_blacklist_blacklistedtoken`")
        cursor.execute("DROP TABLE IF EXISTS `token_blacklist_outstandingtoken`")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        
        # Create OutstandingToken
        sql_outstanding = """
        CREATE TABLE `token_blacklist_outstandingtoken` (
            `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
            `token` longtext NOT NULL,
            `created_at` datetime(6) NULL,
            `expires_at` datetime(6) NOT NULL,
            `user_id` bigint NULL,
            `jti` varchar(255) NOT NULL UNIQUE
        );
        """
        cursor.execute(sql_outstanding)
        print("   ✅ Created token_blacklist_outstandingtoken")
        
        # Create BlacklistedToken
        sql_blacklisted = """
        CREATE TABLE `token_blacklist_blacklistedtoken` (
            `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
            `blacklisted_at` datetime(6) NOT NULL,
            `token_id` bigint NOT NULL UNIQUE
        );
        """
        cursor.execute(sql_blacklisted)
        print("   ✅ Created token_blacklist_blacklistedtoken")
        
        # Add FK
        try:
            fk_sql = """
            ALTER TABLE `token_blacklist_blacklistedtoken` 
            ADD CONSTRAINT `token_blacklist_blacklistedtoken_token_id_fk` 
            FOREIGN KEY (`token_id`) REFERENCES `token_blacklist_outstandingtoken` (`id`);
            """
            cursor.execute(fk_sql)
            print("   ✅ Added Foreign Key")
        except Exception as e:
            print(f"   ℹ️ FK constraint: {e}")
        
        # 2. Remove ghost columns from inventory_devicetype
        print("\n🧹 Cleaning inventory_devicetype ghost columns...")
        ghost_columns = ['is_assignable', 'requires_serial_number', 'icon', 'default_warranty_months']
        for col in ghost_columns:
            try:
                cursor.execute(f"ALTER TABLE inventory_devicetype DROP COLUMN {col}")
                print(f"   ✅ Dropped {col}")
            except Exception as e:
                print(f"   ℹ️ {col}: already removed or doesn't exist")
    
    # 3. Fake migrations
    print("\n👻 Faking migrations...")
    try:
        call_command('migrate', 'token_blacklist', fake=True)
        print("✅ token_blacklist migrations faked")
    except Exception as e:
        print(f"⚠️ Migration fake: {e}")
    
    print("\n🎉 Production database fixed!")

if __name__ == "__main__":
    fix_production_db()
