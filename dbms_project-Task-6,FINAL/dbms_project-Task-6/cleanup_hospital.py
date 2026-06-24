import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Devyaansh2006.",
    "database": "emergency_hospital_db",
    "autocommit": True
}

def cleanup():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # 1. Update all wards to hospital_id = 1
        print("Updating wards to hospital_id = 1...")
        cursor.execute("UPDATE ward SET hospital_id = 1")
        
        # 2. Update all inventory to hospital_id = 1
        print("Updating inventory to hospital_id = 1...")
        cursor.execute("UPDATE inventory SET hospital_id = 1")
        
        # 3. Delete other hospitals
        print("Deleting other hospitals...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("DELETE FROM hospital WHERE hospital_id <> 1")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        print("Cleanup successful!")
    except Exception as e:
        print(f"Error during cleanup: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    cleanup()
