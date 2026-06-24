import mysql.connector
import hashlib
import secrets

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{hashed}"

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Devyaansh2006.",
    "database": "emergency_hospital_db"
}

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

# Reset admin1 to admin1
new_hash = hash_password("admin1")
cursor.execute("UPDATE users SET password_hash = %s WHERE username = 'admin1'", (new_hash,))
conn.commit()

# Also reset admin to admin for good measure
new_hash_admin = hash_password("admin")
cursor.execute("UPDATE users SET password_hash = %s WHERE username = 'admin'", (new_hash_admin,))
conn.commit()

print("Passwords reset: admin1/admin1 and admin/admin")
cursor.close()
conn.close()
