# 🏥 Emergency Hospital System - Friend Setup Guide

This guide will help you get the system running on your local machine with the **exact same data** and configuration.

## 1. Prerequisites
- **Python 3.10+**
- **MySQL Server** installed and running.
- **Git**

## 2. Clone and Install
Clone the repository and install the required Python libraries:
```bash
git clone https://github.com/Devyaansh-123/dbms_project.git
cd hospital
pip install -r requirements.txt
```

## 3. Database Setup (Crucial!)
You must replicate the database structure and data. 

1. Open your MySQL terminal or a GUI (like MySQL Workbench).
2. Create the database:
   ```sql
   CREATE DATABASE emergency_hospital_db;
   ```
3. Import the exact data from the provided dump:
   ```bash
   # Run this in your terminal (replace 'root' with your username if different)
   mysql -u root -p emergency_hospital_db < database_dump.sql
   ```
   *If you are on Windows, you can also open `database_dump.sql` in MySQL Workbench and run the whole script.*

## 4. Configuration
Open `main.py` and ensure the `DB_CONFIG` (lines 29-35) matches your local MySQL settings:
```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "YOUR_MYSQL_PASSWORD", # Change this to yours!
    "database": "emergency_hospital_db",
    "autocommit": True
}
```

## 5. Run the System
Start the backend server:
```bash
python main.py
```
Then open your browser to: **`http://127.0.0.1:8000/static/index.html`**

---

### 🔑 Test Credentials (Admin)
- **Username**: `admin1`
- **Password**: `admin1`
- *(Or use `admin` / `admin`)*

### 👨‍⚕️ Test Credentials (Doctor)
- **Username**: `drsharma201`
- **Password**: `doctor_201`
