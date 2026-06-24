import requests
import random
import mysql.connector
import datetime
from time import sleep

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Devyaansh2006.",
    "database": "emergency_hospital_db",
    "autocommit": True
}

def clean_db():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print("Cleaning existing admissions and patients...")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.execute("TRUNCATE TABLE admission")
    cursor.execute("DELETE FROM patient")
    cursor.execute("UPDATE bed SET status = 'Available'")
    cursor.execute("UPDATE doctor SET availability_status = 'Available', fatigued_until = NULL")
    
    # Let's also insert some clean new beds if they don't exist
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.commit()
    cursor.close()
    conn.close()
    print("Database cleaned!")

API_URL = "http://localhost:8000/api"

NAMES = [
    ("Aarav Joshi", "Male"), ("Neha Desai", "Female"), ("Siddharth Iyer", "Male"),
    ("Pooja Nair", "Female"), ("Rohan Kulkarni", "Male"), ("Ananya Menon", "Female"),
    ("Karan Rao", "Male"), ("Sneha Pillai", "Female"), ("Vikram Reddy", "Male"),
    ("Meera Varma", "Female"), ("Rahul Sengupta", "Male"), ("Riya Banerjee", "Female"),
    ("Aditya Das", "Male"), ("Kavya Shetty", "Female"), ("Arjun Patil", "Male"),
    ("Maya Kadam", "Female"), ("Devanshu Sharma", "Male"), ("Isha Choudhury", "Female"),
    ("Rishi Nambiar", "Male"), ("Tanvi Agarwal", "Female")
]

# Mapping rules we implemented:
# Critical: Dr: ICU, Emergency, Surgery, Cardiology, Neurology / Bed: ICU
# High: Dr: Emergency, Surgery, Orthopedics, Cardiology, Neurology / Bed: Emergency, ICU
# Medium: Dr: General, Orthopedics, Pediatrics, ENT / Bed: General, Emergency
# Low: Dr: General, Dermatology, ENT, Pediatrics / Bed: General

LEVELS = ["Critical", "High", "Medium", "Low"]

def seed_data():
    clean_db()
    
    # Get available doctors and beds from API
    try:
        docs = requests.get(f"{API_URL}/doctors").json()
        beds = requests.get(f"{API_URL}/beds").json()
    except Exception as e:
        print(f"Failed to reach API: {e}")
        return

    print("Generating 20 fake patients and admitting them...")
    
    for i, (name, gender) in enumerate(NAMES):
        p_id = 400 + i
        age = random.randint(18, 80)
        level = random.choice(LEVELS)
        
        # 1. Create Patient
        p_data = {
            "patient_id": p_id,
            "name": name,
            "age": age,
            "gender": gender,
            "emergency_level": level
        }
        res = requests.post(f"{API_URL}/patients", json=p_data)
        if res.status_code not in (200, 201):
            print(f"Failed to create patient {name}: {res.text}")
            continue
            
        print(f"Created Patient: {name} ({level})")

        # 2. Admit Patient (safely matching our new strict logic)
        # Refresh beds/docs to get current availability
        docs = requests.get(f"{API_URL}/doctors").json()
        beds = requests.get(f"{API_URL}/beds").json()
        
        allowed_docs = []
        allowed_beds = []
        
        if level == "Critical":
            allowed_docs = [d for d in docs if d["specialization"] in ["ICU", "Emergency", "Surgery", "Cardiology", "Neurology"] and d["availability_status"] == "Available"]
            allowed_beds = [b for b in beds if b["bed_type"] in ["ICU"] and b["status"] == "Available"]
        elif level == "High":
            allowed_docs = [d for d in docs if d["specialization"] in ["Emergency", "Surgery", "Orthopedics", "Cardiology", "Neurology"] and d["availability_status"] == "Available"]
            allowed_beds = [b for b in beds if b["bed_type"] in ["Emergency", "ICU"] and b["status"] == "Available"]
        elif level == "Medium":
            allowed_docs = [d for d in docs if d["specialization"] in ["General", "Orthopedics", "Pediatrics", "ENT"] and d["availability_status"] == "Available"]
            allowed_beds = [b for b in beds if b["bed_type"] in ["General", "Emergency"] and b["status"] == "Available"]
        elif level == "Low":
            allowed_docs = [d for d in docs if d["specialization"] in ["General", "Dermatology", "ENT", "Pediatrics"] and d["availability_status"] == "Available"]
            allowed_beds = [b for b in beds if b["bed_type"] in ["General"] and b["status"] == "Available"]
            
        if not allowed_docs or not allowed_beds:
            print(f"  -> Skipping admission. No available beds/doctors for {level}.")
            continue
            
        target_doc = random.choice(allowed_docs)
        target_bed = random.choice(allowed_beds)
        
        # Ensure we pass an admission ID above existing ones
        a_id = 900 + i
        
        adm_data = {
            "admission_id": a_id,
            "patient_id": p_id,
            "doctor_id": target_doc["doctor_id"],
            "bed_id": target_bed["bed_id"],
            "admission_date": datetime.datetime.now().strftime("%Y-%m-%d")  # API will use NOW() anyway
        }
        
        adm_res = requests.post(f"{API_URL}/admissions", json=adm_data)
        if adm_res.status_code in (200, 201):
            print(f"  -> Admitted to {target_doc['name']} ({target_doc['specialization']}) in Bed {target_bed['bed_id']} ({target_bed['bed_type']})")
        else:
            print(f"  -> Admission failed: {adm_res.text}")

        sleep(0.1)
        
if __name__ == "__main__":
    seed_data()
