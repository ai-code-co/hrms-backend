import subprocess
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
# Local Database
LOCAL_DB_NAME = os.getenv("DB_NAME", "")
LOCAL_DB_USER = os.getenv("DB_USER", "")
LOCAL_DB_PASS = os.getenv("DB_PASSWORD", "")
LOCAL_DB_HOST = os.getenv("DB_HOST", "localhost")
LOCAL_DB_PORT = os.getenv("DB_PORT", "3306")

# Remote TiDB Cloud (Update these or put in .env)
REMOTE_DB_HOST = os.getenv("REMOTE_DB_HOST", "gateway01.ap-southeast-1.prod.aws.tidbcloud.com")
REMOTE_DB_USER = os.getenv("REMOTE_DB_USER", "") # e.g. "xxxxxx.root"
REMOTE_DB_PASS = os.getenv("REMOTE_DB_PASS", "")
REMOTE_DB_NAME = os.getenv("REMOTE_DB_NAME", LOCAL_DB_NAME)
REMOTE_DB_PORT = os.getenv("REMOTE_DB_PORT", "4000")

DUMP_FILE = "db_dump.sql"

def run_command(command, shell=True):
    print(f"Executing: {command}")
    try:
        subprocess.check_call(command, shell=shell)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        return False

def migrate():
    print("--- Starting Migration from Local MySQL to TiDB Cloud ---")
    
    if not LOCAL_DB_NAME or not LOCAL_DB_USER:
        print("Error: Local database credentials missing in .env")
        return

    # 1. Export local data
    print(f"\nPhase 1: Exporting local database '{LOCAL_DB_NAME}'...")
    dump_cmd = (
        f"mysqldump -h {LOCAL_DB_HOST} -P {LOCAL_DB_PORT} -u {LOCAL_DB_USER} "
        f"-p'{LOCAL_DB_PASS}' --set-gtid-purged=OFF --no-tablespaces {LOCAL_DB_NAME} > {DUMP_FILE}"
    )
    if not run_command(dump_cmd):
        print("Failed to export local data.")
        return

    print(f"Successfully exported local data to {DUMP_FILE}")

    # 2. Preparation for TiDB (Optional: remove MySQL specific comments that might not be supported)
    # Most mysqldump files work fine with TiDB as it is MySQL compatible.

    # 3. Import to TiDB Cloud
    print(f"\nPhase 2: Importing to TiDB Cloud '{REMOTE_DB_NAME}'...")
    if not REMOTE_DB_USER or not REMOTE_DB_PASS:
        print("Error: Remote TiDB credentials missing. Please set them in the script or .env")
        return

    # TiDB Cloud requires SSL usually. mysql client handles it with --ssl-mode=REQUIRED or similar
    import_cmd = (
        f"mysql -h {REMOTE_DB_HOST} -P {REMOTE_DB_PORT} -u {REMOTE_DB_USER} "
        f"-p'{REMOTE_DB_PASS}' --ssl-mode=REQUIRED {REMOTE_DB_NAME} < {DUMP_FILE}"
    )
    
    if not run_command(import_cmd):
        print("Failed to import data to TiDB.")
        return

    print("\n--- Migration Completed Successfully! ---")
    print(f"Cleanup: You can delete {DUMP_FILE} after verification.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--import-only":
        # Logic for import only if dump exists
        pass
    migrate()
