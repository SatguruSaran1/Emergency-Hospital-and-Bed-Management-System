# Emergency Hospital Resource and Bed Management System

This is a comprehensive full-stack web application designed to manage critical hospital operations. It features a robust Python/FastAPI backend, a dynamic Vanilla JS/HTML/CSS frontend, and a highly optimized MySQL relational database utilizing embedded SQL queries, triggers, and scheduled events in place of an ORM.

## Features
- **Patient & Admission Management:** Admit patients based on emergency severity (Critical, High, Medium, Low) and allocate appropriate doctors and beds.
- **Smart Bed Allocation:** Track bed availability across different wards (General, ICU, Emergency).
- **Automated Doctor Fatigue Engine:** Automatically sets doctors to 'Fatigued' status after handling a certain number of critical patients and clears it after a rest period via MySQL scheduled events.
- **Real-Time Inventory Alerts:** Database triggers monitor critical medical stock and automatically generate system alerts when items fall below their threshold levels.
- **Role-Based Access Control:** Secure SHA-256 password hashing for Admin and Doctor roles with tailored interactive dashboards.

## Prerequisites
Before you begin, ensure you have the following installed:
- **Python 3.8+**
- **MySQL Server 8.0+**

## Installation & Setup

### 1. Download the Project
Clone this repository to your local machine:
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git
cd YOUR_REPOSITORY_NAME
```

### 2. Set Up a Virtual Environment (Recommended)
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
Install the required Python packages using pip:
```bash
pip install -r requirements.txt
```

### 4. Database Configuration
1. Open your MySQL client (e.g., MySQL Workbench or terminal).
2. Create the database and tables by importing the `init_db.sql` or `database_dump.sql` file provided in the repository:
   ```sql
   CREATE DATABASE emergency_hospital_db;
   USE emergency_hospital_db;
   SOURCE path/to/database_dump.sql;
   ```
3. Open `main.py` and `seed.py` in your code editor. Locate the `DB_CONFIG` dictionary and update the `user` and `password` fields to match your local MySQL credentials.

### 5. Generate Dummy Data (Optional)
If you want to populate the database with realistic fake patients and admissions for testing, run the seeder script:
```bash
python seed.py
```

### 6. Run the Application
Start the FastAPI server using Uvicorn:
```bash
uvicorn main:app --reload
```
The application will now be running at: `http://localhost:8000`

## How to Use the System
Once the server is running, navigate to `http://localhost:8000/static/index.html` in your web browser. 

### Default Login Credentials
The system automatically generates accounts on startup:

**Admin Accounts:**
- **Username:** `admin1` (up to `admin10`)
- **Password:** `admin1` (same as username)

**Doctor Accounts:**
- **Username:** `dr<name><id>` (e.g., for Dr. John Doe with ID 1, use `drjohndoe1`)
- **Password:** `doctor_<id>` (e.g., `doctor_1`)

From the dashboard, admins can manage hospital inventory, admit/discharge patients, update bed statuses, and view real-time statistics. Doctors can view their active patients and manage their fatigue statuses.

## Tech Stack
- **Backend:** Python, FastAPI
- **Database:** MySQL (Raw Embedded SQL, Triggers, Events)
- **Frontend:** HTML, CSS, Vanilla JavaScript
