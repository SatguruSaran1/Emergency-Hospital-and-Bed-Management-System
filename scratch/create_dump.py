import subprocess
import os

# Configuration from main.py
DB_USER = "root"
DB_PASS = "Devyaansh2006."
DB_NAME = "emergency_hospital_db"
DUMP_FILE = "database_dump.sql"

def create_dump():
    # Use mysqldump via subprocess to avoid shell quoting issues with the password '.'
    try:
        # Note: -p[password] with no space
        cmd = [
            "mysqldump",
            "--no-defaults",
            f"-u{DB_USER}",
            f"-p{DB_PASS}",
            "--databases",
            DB_NAME,
            "--routines",
            "--triggers"
        ]
        
        print(f"Executing: {' '.join(cmd[:3])} -p*** ...")
        
        with open(DUMP_FILE, "w", encoding="utf-8") as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
            
        if result.returncode == 0:
            print(f"Successfully created {DUMP_FILE}")
            # Check file size
            size = os.path.getsize(DUMP_FILE)
            print(f"File size: {size} bytes")
        else:
            print(f"Error creating dump: {result.stderr}")
            
    except Exception as e:
        print(f"An exception occurred: {e}")

if __name__ == "__main__":
    create_dump()
