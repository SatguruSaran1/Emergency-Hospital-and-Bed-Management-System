"""
Emergency Hospital Management System - Backend
Task 5: FastAPI + Embedded SQL (no ORM)
Database: emergency_hospital_db (MySQL)
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import mysql.connector
from mysql.connector import errors as mysql_errors
import os
import hashlib
import secrets


# App Initialization

app = FastAPI(title="Emergency Hospital Management System", version="1.0.0")

# In-memory session store: token -> username
sessions: dict = {}

# Database Configuration

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "x1m4",
    "database": "emergency_hospital_db",
    "autocommit": True
}

def get_db():
    """Create and return a new DB connection."""
    return mysql.connector.connect(**DB_CONFIG)



# Password Hashing (SHA-256 + salt)

def hash_password(password: str) -> str:
    """Hash a password with a random salt using SHA-256."""
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{hashed}"

def verify_password(password: str, stored: str) -> bool:
    """Verify a plaintext password against a stored salt:hash."""
    parts = stored.split(":")
    if len(parts) != 2:
        return False
    salt, hashed = parts
    return hashlib.sha256((salt + password).encode()).hexdigest() == hashed


# Startup: Create users table & default admin

@app.on_event("startup")
def startup():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username VARCHAR(50) PRIMARY KEY,
            password_hash VARCHAR(200) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN role ENUM('Admin', 'Doctor') DEFAULT 'Admin'")
    except Exception:
        pass
        
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN doctor_id INT DEFAULT NULL")
    except Exception:
        pass
    conn.commit()
    # Create 10 default admin accounts if they don't exist
    for i in range(1, 11):
        username = f"admin{i}"
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s", (username,))
        if cursor.fetchone()[0] == 0:
            ph = hash_password(username)
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, 'Admin')",
                (username, ph)
            )
            
    # Doctor users
    cursor.execute("SELECT doctor_id, name FROM doctor")
    for doc in cursor.fetchall():
        doc_id = doc[0]
        name_clean = str(doc[1]).replace('Dr. ', '').replace(' ', '').lower()
        username = f"dr{name_clean}{doc_id}"
        password = f"doctor_{doc_id}"
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s", (username,))
        if cursor.fetchone()[0] == 0:
            ph = hash_password(password)
            cursor.execute(
                "INSERT INTO users (username, password_hash, role, doctor_id) VALUES (%s, %s, %s, %s)",
                (username, ph, 'Doctor', doc_id)
            )
            
    # DOCTOR FATIGUE ENGINE AUTOMATED SETUP 
    # 1. Schema Updates
    cursor.execute("ALTER TABLE doctor MODIFY COLUMN availability_status ENUM('Available','Busy','On Leave','Fatigued') DEFAULT 'Available'")
    try:
        cursor.execute("ALTER TABLE doctor ADD COLUMN fatigued_until DATETIME DEFAULT NULL")
    except Exception as e:
        if "Duplicate column name" not in str(e): print("Warning adding fatigued_until:", e)
    cursor.execute("ALTER TABLE admission MODIFY COLUMN admission_date DATETIME NOT NULL")
    
    # 2. Trigger Logic
    # (doctor_fatigue_check trigger removed - moved to python API layer to avoid mutating table errors)
    
    # 4. INVENTORY AUTO-ALERT SETUP
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notification (
            notification_id INT AUTO_INCREMENT PRIMARY KEY,
            message VARCHAR(255) NOT NULL,
            type ENUM('Info', 'Warning', 'Critical') DEFAULT 'Warning',
            is_read BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("DROP TRIGGER IF EXISTS trg_inventory_check")
    cursor.execute("""
        CREATE TRIGGER trg_inventory_check
        AFTER UPDATE ON inventory
        FOR EACH ROW
        BEGIN
            IF NEW.quantity <= NEW.threshold_level AND OLD.quantity > NEW.threshold_level THEN
                INSERT INTO notification (message, type)
                VALUES (
                    CONCAT('Low Stock Alert: "', 
                           (SELECT resource_name FROM resource WHERE resource_id = NEW.resource_id), 
                           '" is at ', NEW.quantity, ' (Threshold: ', NEW.threshold_level, ')'),
                    'Critical'
                );
            END IF;
        END
    """)
    conn.commit()
    # 3. Scheduled Event (Cooldown Cleanup)
    try:
        cursor.execute("SET GLOBAL event_scheduler = ON")
    except Exception as e:
        pass # May fail if not SUPER user

    cursor.execute("DROP EVENT IF EXISTS clear_doctor_fatigue")
    cursor.execute("""
        CREATE EVENT clear_doctor_fatigue
        ON SCHEDULE EVERY 1 MINUTE
        DO
            UPDATE doctor 
            SET availability_status = 'Available',
                fatigued_until = NULL
            WHERE availability_status = 'Fatigued'
              AND fatigued_until <= NOW()
    """)
    conn.commit()
    cursor.close()
    conn.close()


def query_db(sql: str, params=None, fetch=True):
    """Execute a SQL query and return results."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params or ())
        if fetch:
            return cursor.fetchall()
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()

def execute_db(sql: str, params=None):
    """Execute a DML statement (INSERT/UPDATE/DELETE)."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params or ())
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()


# Pydantic Models (Request Schemas)

class PatientCreate(BaseModel):
    patient_id: int
    name: str
    age: int
    gender: str
    emergency_level: str

class AdmissionCreate(BaseModel):
    admission_id: int
    patient_id: int
    doctor_id: int
    bed_id: int
    admission_date: str

class DoctorStatusUpdate(BaseModel):
    availability_status: str

class BedStatusUpdate(BaseModel):
    status: str

class DischargeRequest(BaseModel):
    discharge_date: str

class BedCreate(BaseModel):
    bed_id: int
    ward_id: int
    bed_type: str

class InventoryUpdate(BaseModel):
    action: str
    amount: int

class InventoryCreate(BaseModel):
    resource_name: str
    hospital_id: int
    quantity: int
    threshold_level: int

class LoginRequest(BaseModel):
    username: str
    password: str

class LogoutRequest(BaseModel):
    token: str

class NotificationRead(BaseModel):
    is_read: bool = True


# AUTH ROUTES


@app.post("/api/login")
def login(req: LoginRequest):
    """Authenticate user and return a session token."""
    users = query_db(
        "SELECT password_hash, role, doctor_id FROM users WHERE username = %s", (req.username,)
    )
    if not users or not verify_password(req.password, users[0]["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = secrets.token_hex(32)
    sessions[token] = {
        "username": req.username,
        "role": users[0].get("role", "Admin"),
        "doctor_id": users[0].get("doctor_id")
    }
    return {"token": token, "username": req.username, "role": sessions[token]["role"], "doctor_id": sessions[token]["doctor_id"]}


@app.post("/api/logout")
def logout(req: LogoutRequest):
    """Invalidate a session token."""
    sessions.pop(req.token, None)
    return {"message": "Logged out"}


@app.get("/api/me")
def me(token: str):
    """Return the logged-in user for a given token."""
    if not token or token not in sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_data = sessions[token]
    if isinstance(user_data, str):
        return {"username": user_data, "role": "Admin", "doctor_id": None}
    return user_data

def get_current_user(authorization: Optional[str] = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        user_data = sessions.get(token)
        if isinstance(user_data, str):
            return {"username": user_data, "role": "Admin", "doctor_id": None}
        return user_data
    return None


# ROUTES


# Dashboard
@app.get("/api/dashboard")
def get_dashboard(user: Optional[dict] = Depends(get_current_user)):
    """
    Embedded SQL: Aggregation + subqueries across multiple tables.
    Returns key stats for the dashboard.
    """
    role = user.get("role", "").lower() if user else ""
    if role == "doctor":
        doc_id = user["doctor_id"]
        total_patients = query_db("SELECT COUNT(DISTINCT patient_id) AS cnt FROM admission WHERE doctor_id = %s", (doc_id,))[0]["cnt"]
        active_admissions = query_db("SELECT COUNT(*) AS cnt FROM admission WHERE status = 'Active' AND doctor_id = %s", (doc_id,))[0]["cnt"]
        fatigued_doctors = query_db("SELECT COUNT(*) AS cnt FROM doctor WHERE availability_status = 'Fatigued' AND doctor_id = %s", (doc_id,))[0]["cnt"]
        critical_patients = query_db("SELECT COUNT(*) AS cnt FROM admission a JOIN patient p ON a.patient_id = p.patient_id WHERE a.status = 'Active' AND p.emergency_level = 'Critical' AND a.doctor_id = %s", (doc_id,))[0]["cnt"]
        
        return {
            "total_patients": total_patients,
            "active_admissions": active_admissions,
            "available_beds": 0,
            "occupied_beds": 0,
            "available_doctors": 0,
            "fatigued_doctors": fatigued_doctors,
            "low_stock_items": 0,
            "critical_patients": critical_patients,
            "total_hospitals": 0,
        }
        
    # Total patients
    total_patients = query_db("SELECT COUNT(*) AS cnt FROM patient")[0]["cnt"]

    # Active admissions
    active_admissions = query_db(
        "SELECT COUNT(*) AS cnt FROM admission WHERE status = 'Active'"
    )[0]["cnt"]

    # Available beds
    available_beds = query_db(
        "SELECT COUNT(*) AS cnt FROM bed WHERE status = 'Available'"
    )[0]["cnt"]

    # Occupied beds
    occupied_beds = query_db(
        "SELECT COUNT(*) AS cnt FROM bed WHERE status = 'Occupied'"
    )[0]["cnt"]

    # Available doctors
    available_doctors = query_db(
        "SELECT COUNT(*) AS cnt FROM doctor WHERE availability_status = 'Available'"
    )[0]["cnt"]

    # Low stock items (quantity < threshold_level)
    low_stock = query_db(
        """
        SELECT COUNT(*) AS cnt FROM inventory
        WHERE quantity < threshold_level
        """
    )[0]["cnt"]

    # Fatigued doctors
    fatigued_doctors = query_db(
        "SELECT COUNT(*) AS cnt FROM doctor WHERE availability_status = 'Fatigued'"
    )[0]["cnt"]

    # Critical patients currently admitted
    critical_patients = query_db(
        """
        SELECT COUNT(*) AS cnt
        FROM admission a
        JOIN patient p ON a.patient_id = p.patient_id
        WHERE a.status = 'Active' AND p.emergency_level = 'Critical'
        """
    )[0]["cnt"]

    # Total hospitals
    total_hospitals = query_db("SELECT COUNT(*) AS cnt FROM hospital")[0]["cnt"]

    return {
        "total_patients": total_patients,
        "active_admissions": active_admissions,
        "available_beds": available_beds,
        "occupied_beds": occupied_beds,
        "available_doctors": available_doctors,
        "fatigued_doctors": fatigued_doctors,
        "low_stock_items": low_stock,
        "critical_patients": critical_patients,
        "total_hospitals": total_hospitals,
    }


#  Hospitals 
@app.get("/api/hospitals")
def get_hospitals():
    """Get all hospitals with ward and bed counts."""
    sql = """
        SELECT 
            h.hospital_id,
            h.name,
            h.location,
            h.contact_no,
            COUNT(DISTINCT w.ward_id) AS total_wards,
            COUNT(DISTINCT b.bed_id) AS total_beds,
            SUM(CASE WHEN b.status = 'Available' THEN 1 ELSE 0 END) AS available_beds
        FROM hospital h
        LEFT JOIN ward w ON h.hospital_id = w.hospital_id
        LEFT JOIN bed b ON w.ward_id = b.ward_id
        GROUP BY h.hospital_id, h.name, h.location, h.contact_no
        ORDER BY h.hospital_id
    """
    return query_db(sql)


#  Patients
@app.get("/api/patients")
def get_patients(user: Optional[dict] = Depends(get_current_user)):
    """
    Embedded SQL: LEFT JOIN to check if patient is currently admitted.
    """
    role = user.get("role", "").lower() if user else ""
    if role == "doctor":
        doc_id = user["doctor_id"]
        sql = f"""
            SELECT 
                p.patient_id, p.name, p.age, p.gender, p.emergency_level,
                'Admitted' AS current_status, a.admission_id
            FROM patient p
            JOIN admission a ON p.patient_id = a.patient_id AND a.status = 'Active'
            WHERE a.doctor_id = {doc_id}
            ORDER BY 
                CASE p.emergency_level
                    WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 WHEN 'Low' THEN 4 ELSE 5
                END
        """
    else:
        sql = """
            SELECT 
                p.patient_id, p.name, p.age, p.gender, p.emergency_level,
                CASE WHEN a.status = 'Active' THEN 'Admitted' ELSE 'Not Admitted' END AS current_status,
                a.admission_id
            FROM patient p
            LEFT JOIN admission a ON p.patient_id = a.patient_id AND a.status = 'Active'
            ORDER BY 
                CASE p.emergency_level
                    WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 WHEN 'Low' THEN 4 ELSE 5
                END
        """
    return query_db(sql)

@app.post("/api/patients")
def create_patient(patient: PatientCreate):
    """Add a new patient."""
    # Check for duplicate
    existing = query_db(
        "SELECT patient_id FROM patient WHERE patient_id = %s",
        (patient.patient_id,)
    )
    if existing:
        raise HTTPException(status_code=400, detail="Patient ID already exists")

    sql = """
        INSERT INTO patient (patient_id, name, age, gender, emergency_level)
        VALUES (%s, %s, %s, %s, %s)
    """
    execute_db(sql, (
        patient.patient_id, patient.name, patient.age,
        patient.gender, patient.emergency_level
    ))
    return {"message": "Patient added successfully", "patient_id": patient.patient_id}

@app.get("/api/patients/{patient_id}")
def get_patient(patient_id: int):
    """Get a single patient's details with admission history."""
    patient = query_db(
        "SELECT * FROM patient WHERE patient_id = %s", (patient_id,)
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    history = query_db(
        """
        SELECT 
            a.admission_id, a.admission_date, a.discharge_date, a.status,
            d.name AS doctor_name, d.specialization,
            b.bed_type, w.ward_type,
            h.name AS hospital_name
        FROM admission a
        JOIN doctor d ON a.doctor_id = d.doctor_id
        JOIN bed b ON a.bed_id = b.bed_id
        JOIN ward w ON b.ward_id = w.ward_id
        JOIN hospital h ON w.hospital_id = h.hospital_id
        WHERE a.patient_id = %s
        ORDER BY a.admission_date DESC
        """,
        (patient_id,)
    )
    return {"patient": patient[0], "admission_history": history}


#  Doctors 
@app.get("/api/doctors")
def get_doctors():
    """Get all doctors with their active patient count."""
    sql = """
        SELECT 
            d.doctor_id,
            d.name,
            d.specialization,
            d.availability_status,
            COUNT(a.admission_id) AS active_patients
        FROM doctor d
        LEFT JOIN admission a ON d.doctor_id = a.doctor_id AND a.status = 'Active'
        GROUP BY d.doctor_id, d.name, d.specialization, d.availability_status
        ORDER BY d.doctor_id
    """
    return query_db(sql)

@app.put("/api/doctors/{doctor_id}/status")
def update_doctor_status(doctor_id: int, body: DoctorStatusUpdate):
    """Manually update a doctor's availability status."""
    valid = ['Available', 'Busy', 'On Leave', 'Fatigued']
    if body.availability_status not in valid:
        raise HTTPException(status_code=400, detail=f"Status must be one of {valid}")

    existing = query_db(
        "SELECT doctor_id, availability_status FROM doctor WHERE doctor_id = %s", (doctor_id,)
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Doctor not found")
        
    doc = existing[0]
    if doc["availability_status"] == 'Fatigued' and body.availability_status != 'Fatigued':
        raise HTTPException(status_code=400, detail="Cannot manually change status while doctor is fatigued. It will automatically clear after the rest period.")

    if body.availability_status == 'Fatigued':
        execute_db(
            """
            UPDATE doctor 
            SET availability_status = %s, fatigued_until = DATE_ADD(NOW(), INTERVAL 8 HOUR) 
            WHERE doctor_id = %s
            """,
            (body.availability_status, doctor_id)
        )
    else:
        execute_db(
            "UPDATE doctor SET availability_status = %s, fatigued_until = NULL WHERE doctor_id = %s",
            (body.availability_status, doctor_id)
        )
    return {"message": f"Doctor status updated to {body.availability_status}"}


# Beds 
@app.get("/api/beds")
def get_beds():
    """
    Embedded SQL: Multi-table JOIN (bed -> ward -> hospital).
    Returns all beds with location context.
    """
    sql = """
        SELECT 
            b.bed_id,
            b.bed_type,
            b.status,
            w.ward_id,
            w.ward_type,
            h.hospital_id,
            h.name AS hospital_name,
            h.location AS hospital_location
        FROM bed b
        JOIN ward w ON b.ward_id = w.ward_id
        JOIN hospital h ON w.hospital_id = h.hospital_id
        ORDER BY b.status ASC, b.bed_id ASC
    """
    return query_db(sql)

@app.post("/api/beds")
def add_bed(bed: BedCreate):
    """Add a new bed to a ward."""
    valid_types = ['General', 'ICU', 'Private', 'Semi-Private']
    if bed.bed_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Bed type must be one of {valid_types}")

    # Check bed_id not duplicate
    if query_db("SELECT bed_id FROM bed WHERE bed_id = %s", (bed.bed_id,)):
        raise HTTPException(status_code=400, detail="Bed ID already exists")

    # Check ward exists
    if not query_db("SELECT ward_id FROM ward WHERE ward_id = %s", (bed.ward_id,)):
        raise HTTPException(status_code=404, detail="Ward not found")

    execute_db(
        "INSERT INTO bed (bed_id, ward_id, bed_type, status) VALUES (%s, %s, %s, 'Available')",
        (bed.bed_id, bed.ward_id, bed.bed_type)
    )
    return {"message": "Bed added successfully", "bed_id": bed.bed_id}


@app.delete("/api/beds/{bed_id}")
def delete_bed(bed_id: int):
    """Remove a bed. Blocked if bed is currently Occupied."""
    existing = query_db("SELECT bed_id, status FROM bed WHERE bed_id = %s", (bed_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Bed not found")
    if existing[0]["status"] == "Occupied":
        raise HTTPException(status_code=400, detail="Cannot delete an occupied bed — discharge the patient first")

    execute_db("DELETE FROM bed WHERE bed_id = %s", (bed_id,))
    return {"message": f"Bed {bed_id} removed successfully"}


@app.put("/api/beds/{bed_id}/status")
def update_bed_status(bed_id: int, body: BedStatusUpdate):
    """Manually update bed status."""
    valid = ['Available', 'Occupied', 'Maintenance']
    if body.status not in valid:
        raise HTTPException(status_code=400, detail=f"Status must be one of {valid}")

    existing = query_db("SELECT bed_id FROM bed WHERE bed_id = %s", (bed_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Bed not found")

    execute_db(
        "UPDATE bed SET status = %s WHERE bed_id = %s",
        (body.status, bed_id)
    )
    return {"message": "Bed status updated"}


# Admissions
@app.get("/api/admissions")
def get_admissions(user: Optional[dict] = Depends(get_current_user)):
    """
    Embedded SQL: Complex multi-table JOIN across 6 tables.
    Returns full admission details.
    """
    role = user.get("role", "").lower() if user else ""
    if role == "doctor":
        doc_id = user["doctor_id"]
        sql = f"""
            SELECT 
                a.admission_id, a.admission_date, a.discharge_date, a.status,
                p.patient_id, p.name AS patient_name, p.age AS patient_age, p.emergency_level,
                d.doctor_id, d.name AS doctor_name, d.specialization,
                b.bed_id, b.bed_type, w.ward_type, h.name AS hospital_name
            FROM admission a
            JOIN patient p ON a.patient_id = p.patient_id
            JOIN doctor d ON a.doctor_id = d.doctor_id
            JOIN bed b ON a.bed_id = b.bed_id
            JOIN ward w ON b.ward_id = w.ward_id
            JOIN hospital h ON w.hospital_id = h.hospital_id
            WHERE a.doctor_id = {doc_id}
            ORDER BY CASE a.status WHEN 'Active' THEN 0 ELSE 1 END, a.admission_date DESC
        """
    else:
        sql = """
            SELECT 
                a.admission_id, a.admission_date, a.discharge_date, a.status,
                p.patient_id, p.name AS patient_name, p.age AS patient_age, p.emergency_level,
                d.doctor_id, d.name AS doctor_name, d.specialization,
                b.bed_id, b.bed_type, w.ward_type, h.name AS hospital_name
            FROM admission a
            JOIN patient p ON a.patient_id = p.patient_id
            JOIN doctor d ON a.doctor_id = d.doctor_id
            JOIN bed b ON a.bed_id = b.bed_id
            JOIN ward w ON b.ward_id = w.ward_id
            JOIN hospital h ON w.hospital_id = h.hospital_id
            ORDER BY CASE a.status WHEN 'Active' THEN 0 ELSE 1 END, a.admission_date DESC
        """
    return query_db(sql)

@app.post("/api/admissions")
def create_admission(admission: AdmissionCreate):
    """
    Admit a patient.
    NOTE: Trigger trg_after_admission_insert fires automatically
    to set bed -> Occupied and doctor -> Busy.
    """
    # Validation mappings
    ALLOWED_DOCTORS = {
        "Critical": ["ICU", "Emergency", "Surgery", "Cardiology", "Neurology"],
        "High": ["Emergency", "Surgery", "Orthopedics", "Cardiology", "Neurology"],
        "Medium": ["General", "Orthopedics", "Pediatrics", "ENT"],
        "Low": ["General", "Dermatology", "ENT", "Pediatrics"]
    }
    
    ALLOWED_BEDS = {
        "Critical": ["ICU"],
        "High": ["Emergency", "ICU"],
        "Medium": ["General", "Emergency"],
        "Low": ["General"]
    }

    # Validate patient exists and get their emergency level
    p_info = query_db("SELECT emergency_level FROM patient WHERE patient_id = %s", (admission.patient_id,))
    if not p_info:
        raise HTTPException(status_code=404, detail="Patient not found")
    e_level = p_info[0]["emergency_level"]

    # Check if doctor is fatigued and validate specialization
    doc = query_db("SELECT availability_status, specialization FROM doctor WHERE doctor_id = %s", (admission.doctor_id,))
    if not doc:
        raise HTTPException(status_code=404, detail="Doctor not found")
    if doc[0]["availability_status"] == 'Fatigued':
        raise HTTPException(status_code=400, detail="Doctor is fatigued and cannot accept new patients")
    if doc[0]["specialization"] not in ALLOWED_DOCTORS.get(e_level, []):
        raise HTTPException(status_code=400, detail=f"A {e_level} patient cannot be assigned to a {doc[0]['specialization']} specialist.")

    # Check patient not already admitted
    active = query_db(
        "SELECT admission_id FROM admission WHERE patient_id = %s AND status = 'Active'",
        (admission.patient_id,)
    )
    if active:
        raise HTTPException(status_code=400, detail="Patient already has an active admission")

    # Check bed is Available and validate bed type
    bed = query_db(
        "SELECT status, bed_type FROM bed WHERE bed_id = %s", (admission.bed_id,)
    )
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
    if bed[0]["status"] != "Available":
        raise HTTPException(status_code=400,
                            detail=f"Bed is not available (current status: {bed[0]['status']})")
    if bed[0]["bed_type"] not in ALLOWED_BEDS.get(e_level, []):
        raise HTTPException(status_code=400, detail=f"{e_level} severity patients cannot be placed in a {bed[0]['bed_type']} bed.")

    # Check admission ID not duplicate
    if query_db("SELECT admission_id FROM admission WHERE admission_id = %s",
                (admission.admission_id,)):
        raise HTTPException(status_code=400, detail="Admission ID already exists")

    sql = """
        INSERT INTO admission (admission_id, admission_date, discharge_date, status,
                               patient_id, doctor_id, bed_id)
        VALUES (%s, NOW(), NULL, 'Active', %s, %s, %s)
    """
    try:
        execute_db(sql, (
            admission.admission_id,
            admission.patient_id, admission.doctor_id, admission.bed_id
        ))
    except mysql_errors.IntegrityError as e:
        if "bed_id" in str(e):
            raise HTTPException(status_code=400,
                detail="This bed is already assigned to another active admission. Please select a different bed.")
        if "admission_id" in str(e):
            raise HTTPException(status_code=400,
                detail="Admission ID already in use. Please use a different ID.")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # Fatigue check logic
    if e_level == "Critical":
        critical_count = query_db("""
            SELECT COUNT(*) AS cnt FROM admission a
            JOIN patient p ON a.patient_id = p.patient_id
            WHERE a.doctor_id = %s 
              AND p.emergency_level = 'Critical'
              AND a.admission_date >= DATE_SUB(NOW(), INTERVAL 12 HOUR)
        """, (admission.doctor_id,))[0]["cnt"]
        
        if critical_count >= 5:
            execute_db("""
                UPDATE doctor 
                SET availability_status = 'Fatigued',
                    fatigued_until = DATE_ADD(NOW(), INTERVAL 8 HOUR)
                WHERE doctor_id = %s
            """, (admission.doctor_id,))

    return {"message": "Patient admitted successfully. Bed and doctor status updated by trigger."}

@app.put("/api/admissions/{admission_id}/discharge")
def discharge_patient(admission_id: int, body: DischargeRequest):
    """
    Discharge a patient.
    NOTE: Trigger trg_after_discharge_update fires automatically
    to free the bed and (if no other active patients) reset doctor status.
    """
    admission = query_db(
        "SELECT * FROM admission WHERE admission_id = %s", (admission_id,)
    )
    if not admission:
        raise HTTPException(status_code=404, detail="Admission not found")
    if admission[0]["status"] == "Discharged":
        raise HTTPException(status_code=400, detail="Patient already discharged")

    execute_db(
        """
        UPDATE admission
        SET status = 'Discharged', discharge_date = %s
        WHERE admission_id = %s
        """,
        (body.discharge_date, admission_id)
    )
    # Trigger fires here automatically (trg_after_discharge_update)
    return {"message": "Patient discharged. Bed freed and doctor status updated by trigger."}


# Inventory
@app.get("/api/inventory")
def get_inventory():
    """
    Embedded SQL: JOIN with resource table + computed low_stock flag.
    Shows inventory with alert when quantity < threshold.
    """
    sql = """
        SELECT 
            i.inventory_id,
            r.resource_name,
            i.quantity,
            i.threshold_level,
            h.name AS hospital_name,
            h.location,
            CASE WHEN i.quantity < i.threshold_level THEN TRUE ELSE FALSE END AS low_stock,
            ROUND((i.quantity / i.threshold_level) * 100, 1) AS stock_percent
        FROM inventory i
        JOIN resource r ON i.resource_id = r.resource_id
        JOIN hospital h ON i.hospital_id = h.hospital_id
        ORDER BY low_stock DESC, i.quantity ASC
    """
    return query_db(sql)

@app.put("/api/inventory/{inventory_id}")
def update_inventory_stock(
    inventory_id: int,
    update: InventoryUpdate,
    user: Optional[dict] = Depends(get_current_user)
):
    """
    Update stock quantity safely (prevent going below zero).
    Role-based enforcement:
      - Admin  → may only 'add' (restock).
      - Doctor → may only 'use' (consume).
    The trg_inventory_check trigger fires automatically on any UPDATE
    to inventory.quantity, so low-stock notifications are unaffected.
    """
    role = user.get("role", "").lower() if user else "admin"

    # --- Role-based action guard ---
    if update.action == 'use' and role != 'doctor':
        raise HTTPException(
            status_code=403,
            detail="Only doctors are authorised to consume inventory items."
        )
    if update.action == 'add' and role == 'doctor':
        raise HTTPException(
            status_code=403,
            detail="Doctors cannot restock inventory. Please contact an admin."
        )

    inv = query_db("SELECT quantity FROM inventory WHERE inventory_id = %s", (inventory_id,))
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    current_qty = inv[0]["quantity"]
    new_qty = current_qty

    if update.action == 'use':
        if current_qty < update.amount:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot use {update.amount}: Only {current_qty} in stock."
            )
        new_qty -= update.amount
    elif update.action == 'add':
        new_qty += update.amount
    else:
        raise HTTPException(status_code=400, detail="Action must be 'use' or 'add'")

    # This UPDATE fires trg_inventory_check automatically on the DB side
    execute_db("UPDATE inventory SET quantity = %s WHERE inventory_id = %s", (new_qty, inventory_id))
    return {"message": "Stock updated successfully", "new_quantity": new_qty}

@app.post("/api/inventory")
def create_inventory_item(item: InventoryCreate):
    """Register a completely new resource or track an existing one for a specific hospital."""
    # Find or create resource
    res = query_db("SELECT resource_id FROM resource WHERE LOWER(resource_name) = LOWER(%s)", (item.resource_name,))
    
    if res:
        res_id = res[0]["resource_id"]
    else:
        max_res = query_db("SELECT IFNULL(MAX(resource_id), 0) as m FROM resource")[0]["m"]
        res_id = max_res + 1
        execute_db("INSERT INTO resource (resource_id, resource_name) VALUES (%s, %s)", (res_id, item.resource_name))
        
    # Check if this hospital already tracks this resource
    existing_inv = query_db("SELECT inventory_id FROM inventory WHERE hospital_id = %s AND resource_id = %s", (item.hospital_id, res_id))
    if existing_inv:
        raise HTTPException(status_code=400, detail=f"This hospital already tracks '{item.resource_name}'. Please update its stock instead.")
        
    max_inv = query_db("SELECT IFNULL(MAX(inventory_id), 0) as m FROM inventory")[0]["m"]
    inv_id = max_inv + 1
    
    execute_db("""
        INSERT INTO inventory (inventory_id, quantity, threshold_level, hospital_id, resource_id) 
        VALUES (%s, %s, %s, %s, %s)
    """, (inv_id, item.quantity, item.threshold_level, item.hospital_id, res_id))
    
    return {"message": "New inventory item registered successfully."}


#  Wards 
@app.get("/api/wards")
def get_wards():
    """Get all wards with bed availability."""
    sql = """
        SELECT 
            w.ward_id,
            w.ward_type,
            w.capacity,
            COUNT(b.bed_id) AS total_beds,
            SUM(CASE WHEN b.status = 'Available' THEN 1 ELSE 0 END) AS available_beds,
            SUM(CASE WHEN b.status = 'Occupied' THEN 1 ELSE 0 END) AS occupied_beds
        FROM ward w
        LEFT JOIN bed b ON w.ward_id = b.ward_id
        GROUP BY w.ward_id, w.ward_type, w.capacity
        ORDER BY w.ward_id
    """
    return query_db(sql)


#  Available Options for Forms
@app.get("/api/available-beds")
def get_available_beds():
    """Get only available beds for admission form.
    Double-checks against the admission table to exclude beds
    that have an active admission (even if status not yet updated).
    """
    sql = """
        SELECT b.bed_id, b.bed_type, w.ward_type
        FROM bed b
        JOIN ward w ON b.ward_id = w.ward_id
        WHERE b.status = 'Available'
          AND b.bed_id NOT IN (
              SELECT bed_id FROM admission WHERE status = 'Active'
          )
        ORDER BY b.bed_id
    """
    return query_db(sql)

@app.get("/api/available-doctors")
def get_available_doctors():
    """Get only available doctors for admission form."""
    sql = """
        SELECT doctor_id, name, specialization
        FROM doctor
        WHERE availability_status = 'Available'
        ORDER BY doctor_id
    """
    return query_db(sql)

@app.get("/api/unadmitted-patients")
def get_unadmitted_patients():
    """Get patients without active admission for admission form."""
    sql = """
        SELECT p.patient_id, p.name, p.age, p.emergency_level
        FROM patient p
        WHERE p.patient_id NOT IN (
            SELECT patient_id FROM admission WHERE status = 'Active'
        )
        ORDER BY 
            CASE p.emergency_level
                WHEN 'Critical' THEN 1
                WHEN 'High' THEN 2
                WHEN 'Medium' THEN 3
                WHEN 'Low' THEN 4
                ELSE 5
            END
    """
    return query_db(sql)



# REPORT ENDPOINTS (Section 9 of Project Doc)

@app.get("/api/reports/emergency-readiness")
def report_emergency_readiness():
    """
    Section 9E: Hospital-wise bed occupancy & emergency readiness report.
    Shows each hospital's total/available/occupied beds + resource status.
    """
    sql = """
        SELECT
            h.hospital_id,
            COUNT(DISTINCT w.ward_id)  AS total_wards,
            COUNT(DISTINCT b.bed_id)   AS total_beds,
            SUM(CASE WHEN b.status = 'Available'   THEN 1 ELSE 0 END) AS available_beds,
            SUM(CASE WHEN b.status = 'Occupied'    THEN 1 ELSE 0 END) AS occupied_beds,
            SUM(CASE WHEN b.status = 'Maintenance' THEN 1 ELSE 0 END) AS maintenance_beds,
            ROUND(
                SUM(CASE WHEN b.status = 'Occupied' THEN 1 ELSE 0 END) * 100.0
                / NULLIF(COUNT(DISTINCT b.bed_id), 0), 1
            ) AS occupancy_pct,
            (SELECT COUNT(*) FROM inventory i
             WHERE i.hospital_id = h.hospital_id
               AND i.quantity <= i.threshold_level) AS low_stock_count,
            (SELECT COUNT(*) FROM admission a
              JOIN bed bb ON a.bed_id = bb.bed_id
              JOIN ward ww ON bb.ward_id = ww.ward_id
             WHERE ww.hospital_id = h.hospital_id
               AND a.status = 'Active') AS active_admissions
        FROM hospital h
        LEFT JOIN ward w  ON h.hospital_id = w.hospital_id
        LEFT JOIN bed  b  ON w.ward_id = b.ward_id
        GROUP BY h.hospital_id
        ORDER BY h.hospital_id
    """
    return query_db(sql)


@app.get("/api/reports/doctor-patients")
def report_doctor_patients():
    """
    Section 9D: List all doctors with their currently assigned patients.
    """
    sql = """
        SELECT
            d.doctor_id,
            d.name          AS doctor_name,
            d.specialization,
            d.availability_status,
            p.patient_id,
            p.name          AS patient_name,
            p.age,
            p.emergency_level,
            a.admission_id,
            a.admission_date,
            b.bed_type,
            w.ward_type,
            h.name          AS hospital_name
        FROM doctor d
        JOIN admission a  ON d.doctor_id  = a.doctor_id  AND a.status = 'Active'
        JOIN patient   p  ON a.patient_id = p.patient_id
        JOIN bed       b  ON a.bed_id     = b.bed_id
        JOIN ward      w  ON b.ward_id    = w.ward_id
        JOIN hospital  h  ON w.hospital_id = h.hospital_id
        ORDER BY d.doctor_id, p.emergency_level
    """
    return query_db(sql)


@app.get("/api/reports/daily-stats")
def report_daily_stats():
    """
    Section 9E: Daily admission and discharge counts for the last 30 days.
    """
    sql = """
        SELECT
            dates.day,
            COALESCE(adm.admissions, 0) AS admissions,
            COALESCE(dis.discharges, 0) AS discharges
        FROM (
            SELECT DATE(admission_date) AS day FROM admission
            UNION
            SELECT DATE(discharge_date) AS day FROM admission WHERE discharge_date IS NOT NULL
        ) dates
        LEFT JOIN (
            SELECT DATE(admission_date) AS day, COUNT(*) AS admissions
            FROM admission GROUP BY DATE(admission_date)
        ) adm ON dates.day = adm.day
        LEFT JOIN (
            SELECT DATE(discharge_date) AS day, COUNT(*) AS discharges
            FROM admission WHERE discharge_date IS NOT NULL
            GROUP BY DATE(discharge_date)
        ) dis ON dates.day = dis.day
        ORDER BY dates.day DESC
        LIMIT 30
    """
    return query_db(sql)


@app.get("/api/reports/resource-shortage")
def report_resource_shortage():
    """
    Section 9C: Resources falling below threshold — shortage alerts.
    """
    sql = """
        SELECT
            h.name              AS hospital_name,
            h.location,
            r.resource_name,
            i.quantity,
            i.threshold_level,
            (i.threshold_level - i.quantity) AS shortage_amount,
            ROUND((i.quantity / i.threshold_level) * 100, 1) AS stock_pct
        FROM inventory i
        JOIN resource r  ON i.resource_id  = r.resource_id
        JOIN hospital h  ON i.hospital_id  = h.hospital_id
        WHERE i.quantity < i.threshold_level
        ORDER BY shortage_amount DESC
    """
    return query_db(sql)



# Serve Frontend Static Files

static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.get("/login")
def serve_login():
    return FileResponse(
        os.path.join(static_path, "login.html"),
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/")
def serve_frontend():
    return FileResponse(
        os.path.join(static_path, "index.html"),
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )



# Run Server

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

# NOTIFICATIONS (INVENTORY ALERTS)


@app.get("/api/notifications")
def get_notifications(unread_only: bool = True):
    """Fetch system notifications/alerts."""
    if unread_only:
        return query_db("SELECT * FROM notification WHERE is_read = FALSE ORDER BY created_at DESC")
    return query_db("SELECT * FROM notification ORDER BY created_at DESC LIMIT 50")

@app.post("/api/notifications/{notif_id}/read")
def mark_notification_read(notif_id: int):
    """Mark an alert as read/dismissed."""
    execute_db("UPDATE notification SET is_read = TRUE WHERE notification_id = %s", (notif_id,))
    return {"message": "Notification dismissed"}
