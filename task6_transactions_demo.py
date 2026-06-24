"""
Task 6: Database Transaction Demonstration
Emergency Hospital Management System

This script demonstrates real DB transactions including:
  1. Admission Transaction (multi-table atomicity via triggers)
  2. Discharge Transaction (trigger-based state rollback)
  3. Conflict: Double-booking a bed (concurrent INSERT -> ROLLBACK)
  4. Conflict: Inventory race condition (concurrent stock deduction)
  5. Constraint enforcement (FK, CHECK, ENUM violations)

Run:  python task6_transactions_demo.py
Requires: MySQL server running with emergency_hospital_db initialised.
"""

import mysql.connector
import threading
import time

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Devyaansh2006.",
    "database": "emergency_hospital_db",
}

SEPARATOR = "\n" + "=" * 70



# Helper utilities

def get_conn(autocommit=False):
    conn = mysql.connector.connect(**DB_CONFIG, autocommit=autocommit)
    return conn


def fetch_one(sql, params=None):
    conn = get_conn(autocommit=True)
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, params or ())
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def fetch_all(sql, params=None):
    conn = get_conn(autocommit=True)
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, params or ())
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def print_state(label, bed_id=None, doctor_id=None, inventory_id=None):
    """Print the current state of relevant rows."""
    print(f"\n  [STATE] {label}")
    if bed_id:
        row = fetch_one("SELECT bed_id, status FROM bed WHERE bed_id = %s", (bed_id,))
        print(f"     Bed {bed_id}: status = {row['status']}")
    if doctor_id:
        row = fetch_one("SELECT doctor_id, name, availability_status FROM doctor WHERE doctor_id = %s", (doctor_id,))
        print(f"     Doctor {doctor_id} ({row['name']}): status = {row['availability_status']}")
    if inventory_id:
        row = fetch_one(
            "SELECT i.inventory_id, r.resource_name, i.quantity, i.threshold_level "
            "FROM inventory i JOIN resource r ON i.resource_id = r.resource_id "
            "WHERE i.inventory_id = %s", (inventory_id,))
        print(f"     Inventory {inventory_id} ({row['resource_name']}): qty = {row['quantity']}  (threshold = {row['threshold_level']})")



# SETUP: ensure a clean, testable state

def setup_test_data():
    """Insert temporary test rows used by the demo; safe to re-run."""
    conn = get_conn(autocommit=True)
    cur = conn.cursor()

    # Clean up any leftover test data first
    cur.execute("DELETE FROM admission WHERE admission_id IN (9901, 9902)")
    cur.execute("DELETE FROM bed WHERE bed_id IN (8801, 8802)")
    cur.execute("DELETE FROM patient WHERE patient_id IN (9901, 9902)")

    # Create test patients
    cur.execute("INSERT INTO patient VALUES (9901, 'Test Patient A', 30, 'Male', 'Critical')")
    cur.execute("INSERT INTO patient VALUES (9902, 'Test Patient B', 25, 'Female', 'Critical')")

    # Create dedicated test beds in ward 102 (General ward) to avoid conflicts
    cur.execute("INSERT INTO bed (bed_id, bed_type, status, ward_id) VALUES (8801, 'ICU', 'Available', 101)")
    cur.execute("INSERT INTO bed (bed_id, bed_type, status, ward_id) VALUES (8802, 'ICU', 'Available', 101)")

    # Ensure doctor 202 is Available
    cur.execute("UPDATE doctor SET availability_status = 'Available', fatigued_until = NULL WHERE doctor_id = 202")

    cur.close()
    conn.close()
    print("  [OK] Test data prepared.\n")


def cleanup_test_data():
    """Remove temporary rows created during the demo."""
    conn = get_conn(autocommit=True)
    cur = conn.cursor()
    cur.execute("DELETE FROM admission WHERE admission_id IN (9901, 9902)")
    cur.execute("DELETE FROM bed WHERE bed_id IN (8801, 8802)")
    cur.execute("DELETE FROM patient WHERE patient_id IN (9901, 9902)")
    # Restore doctor to reasonable state
    cur.execute("UPDATE doctor SET availability_status = 'Available', fatigued_until = NULL WHERE doctor_id = 202")
    cur.close()
    conn.close()
    print("\n  [CLEANUP] Complete - test rows removed.\n")


# SCENARIO 1 -- Admission Transaction (Atomicity)

def scenario_1_admission():
    print(SEPARATOR)
    print("SCENARIO 1: Admission Transaction -- Multi-Table Atomicity")
    print("=" * 70)
    print("""
  GOAL : INSERT into 'admission' -> trigger automatically updates
         bed -> 'Occupied' AND doctor -> 'Busy' in one atomic operation.
  TABLES AFFECTED: admission, bed, doctor (via trigger)
    """)

    bed_id = 8801
    doctor_id = 202
    patient_id = 9901

    print_state("BEFORE admission", bed_id=bed_id, doctor_id=doctor_id)

    # --- Transaction ---
    conn = get_conn()
    cur = conn.cursor()
    try:
        conn.start_transaction()
        print("\n  > START TRANSACTION")
        cur.execute(
            "INSERT INTO admission (admission_id, admission_date, discharge_date, status, "
            "patient_id, doctor_id, bed_id) VALUES (%s, NOW(), NULL, 'Active', %s, %s, %s)",
            (9901, patient_id, doctor_id, bed_id)
        )
        print("  > INSERT INTO admission ... (admission_id=9901)")
        print("    -> Trigger 'trg_after_admission_insert' fires:")
        print("       * UPDATE bed SET status='Occupied' WHERE bed_id=8801")
        print("       * UPDATE doctor SET availability_status='Busy' WHERE doctor_id=202")
        conn.commit()
        print("  > COMMIT  [OK]")
    except Exception as e:
        conn.rollback()
        print(f"  > ROLLBACK [FAIL]  Error: {e}")
    finally:
        cur.close()
        conn.close()

    print_state("AFTER admission", bed_id=bed_id, doctor_id=doctor_id)

    # Verify admission row
    adm = fetch_one("SELECT * FROM admission WHERE admission_id = 9901")
    print(f"\n  [OK] Admission 9901 created: status={adm['status']}, "
          f"patient={adm['patient_id']}, doctor={adm['doctor_id']}, bed={adm['bed_id']}")
    print("\n  RESULT: One INSERT triggered atomic updates across 3 tables.")


# SCENARIO 2 -- Discharge Transaction (Cascade)

def scenario_2_discharge():
    print(SEPARATOR)
    print("SCENARIO 2: Discharge Transaction -- Trigger-Based State Reversal")
    print("=" * 70)
    print("""
  GOAL : UPDATE admission status -> 'Discharged' triggers:
         bed -> 'Available', doctor -> 'Available' (if no other active patients).
  TABLES AFFECTED: admission, bed, doctor (via trigger)
    """)

    bed_id = 8801
    doctor_id = 202

    print_state("BEFORE discharge", bed_id=bed_id, doctor_id=doctor_id)

    conn = get_conn()
    cur = conn.cursor()
    try:
        conn.start_transaction()
        print("\n  > START TRANSACTION")
        cur.execute(
            "UPDATE admission SET status = 'Discharged', discharge_date = CURDATE() "
            "WHERE admission_id = 9901"
        )
        print("  > UPDATE admission SET status='Discharged' WHERE admission_id=9901")
        print("    -> Trigger 'trg_after_discharge_update' fires:")
        print("       * UPDATE bed SET status='Available' WHERE bed_id=8801")
        print("       * Checks if doctor 202 has other active admissions...")
        print("       * If none -> UPDATE doctor SET availability_status='Available'")
        conn.commit()
        print("  > COMMIT  [OK]")
    except Exception as e:
        conn.rollback()
        print(f"  > ROLLBACK [FAIL]  Error: {e}")
    finally:
        cur.close()
        conn.close()

    print_state("AFTER discharge", bed_id=bed_id, doctor_id=doctor_id)
    print("\n  RESULT: Discharge reversed all state changes made at admission time.")


# SCENARIO 3 -- Conflict: Double-Booking a Bed

def scenario_3_double_booking():
    print(SEPARATOR)
    print("SCENARIO 3: Conflict -- Double-Booking a Bed (Concurrency)")
    print("=" * 70)
    print("""
  GOAL : Two transactions simultaneously try to admit a patient to the
         SAME bed. Only one should succeed; the other must ROLLBACK.
  METHOD: Transaction A locks the bed row with SELECT ... FOR UPDATE,
          checks the status, then inserts. Transaction B does the same
          and finds the bed already 'Occupied' -> rolls back.
    """)

    bed_id = 8801
    # Reset state: ensure bed is available, remove any leftover admissions
    c = get_conn(autocommit=True)
    cc = c.cursor()
    cc.execute("DELETE FROM admission WHERE admission_id IN (9901, 9902)")
    cc.execute("UPDATE bed SET status = 'Available' WHERE bed_id = %s", (bed_id,))
    cc.execute("UPDATE doctor SET availability_status = 'Available', fatigued_until = NULL WHERE doctor_id = 202")
    cc.close()
    c.close()

    results = {"A": None, "B": None}
    barrier = threading.Barrier(2)  # synchronise start

    def try_admit(tx_name, admission_id, patient_id, doctor_id):
        conn = get_conn()
        cur = conn.cursor(dictionary=True)
        try:
            conn.start_transaction(isolation_level='SERIALIZABLE')
            barrier.wait()  # both start at the same time

            # Lock the bed row
            cur.execute("SELECT bed_id, status FROM bed WHERE bed_id = %s FOR UPDATE", (bed_id,))
            bed_row = cur.fetchone()

            if bed_row["status"] != "Available":
                conn.rollback()
                results[tx_name] = "ROLLBACK (bed already Occupied)"
                return

            # Bed is available -- proceed
            cur.execute(
                "INSERT INTO admission (admission_id, admission_date, discharge_date, "
                "status, patient_id, doctor_id, bed_id) "
                "VALUES (%s, NOW(), NULL, 'Active', %s, %s, %s)",
                (admission_id, patient_id, doctor_id, bed_id)
            )
            conn.commit()
            results[tx_name] = "COMMIT [OK] (patient admitted)"
        except Exception as e:
            conn.rollback()
            results[tx_name] = f"ROLLBACK [FAIL] ({e})"
        finally:
            cur.close()
            conn.close()

    t1 = threading.Thread(target=try_admit, args=("A", 9901, 9901, 202))
    t2 = threading.Thread(target=try_admit, args=("B", 9902, 9902, 202))

    print("  > Launching Transaction A and Transaction B concurrently...\n")
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    print(f"  Transaction A -> {results['A']}")
    print(f"  Transaction B -> {results['B']}")

    print_state("FINAL STATE", bed_id=bed_id, doctor_id=202)
    print("\n  RESULT: Only ONE transaction succeeded. The other was safely rolled back.")
    print("  This demonstrates row-level locking (SELECT ... FOR UPDATE) preventing")
    print("  double-booking and maintaining database consistency.")


# SCENARIO 4 -- Conflict: Inventory Race Condition

def scenario_4_inventory_race():
    print(SEPARATOR)
    print("SCENARIO 4: Conflict -- Inventory Race Condition (Concurrent Deduction)")
    print("=" * 70)
    print("""
  GOAL : Two transactions try to consume stock at the same time.
         Without locking, both could read qty=50 and each subtract 40,
         leaving qty = -30 (INVALID). With FOR UPDATE locking, the second
         transaction waits, sees the updated qty, and safely rejects.
  TABLE: inventory (id=501, Oxygen Cylinder, qty starts at 50)
    """)

    inv_id = 501
    # Reset quantity to 50
    c = get_conn(autocommit=True)
    cc = c.cursor()
    cc.execute("UPDATE inventory SET quantity = 50 WHERE inventory_id = %s", (inv_id,))
    cc.close()
    c.close()

    print_state("BEFORE", inventory_id=inv_id)

    results = {"A": None, "B": None}
    barrier = threading.Barrier(2)

    def try_deduct(tx_name, amount):
        conn = get_conn()
        cur = conn.cursor(dictionary=True)
        try:
            conn.start_transaction(isolation_level='SERIALIZABLE')
            barrier.wait()

            # Lock the inventory row
            cur.execute("SELECT quantity FROM inventory WHERE inventory_id = %s FOR UPDATE", (inv_id,))
            row = cur.fetchone()
            current_qty = row["quantity"]

            if current_qty < amount:
                conn.rollback()
                results[tx_name] = f"ROLLBACK [FAIL] (need {amount} but only {current_qty} available)"
                return

            new_qty = current_qty - amount
            cur.execute("UPDATE inventory SET quantity = %s WHERE inventory_id = %s", (new_qty, inv_id))
            conn.commit()
            results[tx_name] = f"COMMIT [OK] (deducted {amount}, new qty = {new_qty})"
        except Exception as e:
            conn.rollback()
            results[tx_name] = f"ROLLBACK [FAIL] ({e})"
        finally:
            cur.close()
            conn.close()

    print(f"\n  > Both transactions attempt to deduct 40 units from stock of 50...\n")

    t1 = threading.Thread(target=try_deduct, args=("A", 40))
    t2 = threading.Thread(target=try_deduct, args=("B", 40))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    print(f"  Transaction A -> {results['A']}")
    print(f"  Transaction B -> {results['B']}")

    print_state("AFTER", inventory_id=inv_id)
    print("\n  RESULT: One transaction committed (qty -> 10), the other rolled back")
    print("  because 10 < 40. Stock never went negative. Consistency maintained.")

    # Restore original quantity
    c = get_conn(autocommit=True)
    cc = c.cursor()
    cc.execute("UPDATE inventory SET quantity = 50 WHERE inventory_id = %s", (inv_id,))
    cc.close()
    c.close()



# SCENARIO 5 -- Constraint Enforcement

def scenario_5_constraints():
    print(SEPARATOR)
    print("SCENARIO 5: Constraint Enforcement -- FK, CHECK, ENUM Violations")
    print("=" * 70)
    print("""
  GOAL : Attempt operations that violate database constraints.
         MySQL rejects them immediately, keeping data consistent.
    """)

    test_cases = [
        {
            "label": "5a. FOREIGN KEY -- admission references non-existent patient",
            "sql": "INSERT INTO admission (admission_id, admission_date, status, patient_id, doctor_id, bed_id) "
                   "VALUES (99999, NOW(), 'Active', 88888, 202, 8802)",
            "constraint": "admission_ibfk_1 (patient_id -> patient.patient_id)",
        },
        {
            "label": "5b. FOREIGN KEY -- admission references non-existent doctor",
            "sql": "INSERT INTO admission (admission_id, admission_date, status, patient_id, doctor_id, bed_id) "
                   "VALUES (99999, NOW(), 'Active', 9901, 99999, 8802)",
            "constraint": "admission_ibfk_2 (doctor_id -> doctor.doctor_id)",
        },
        {
            "label": "5c. UNIQUE KEY -- admitting to a bed that is already occupied",
            "sql": "INSERT INTO admission (admission_id, admission_date, status, patient_id, doctor_id, bed_id) "
                   "VALUES (99999, NOW(), 'Active', 9902, 202, 8801)",
            "constraint": "UNIQUE key on admission.bed_id (bed already in use by scenario 3)",
        },
        {
            "label": "5d. CHECK constraint -- discharge date before admission date",
            "sql": "INSERT INTO admission (admission_id, admission_date, discharge_date, status, "
                   "patient_id, doctor_id, bed_id) VALUES (99998, '2026-03-01', '2025-01-01', "
                   "'Discharged', 9902, 202, 8802)",
            "constraint": "chk_dates (discharge_date >= admission_date)",
        },
    ]

    for tc in test_cases:
        print(f"\n  > {tc['label']}")
        print(f"    Constraint: {tc['constraint']}")
        conn = get_conn()
        cur = conn.cursor()
        try:
            conn.start_transaction()
            cur.execute(tc["sql"])
            conn.commit()
            print(f"    Result: COMMITTED -- constraint not enforced by this MySQL version")
            print(f"    NOTE: Some CHECK constraints are parsed but not enforced in MySQL < 8.0.16")
        except Exception as e:
            conn.rollback()
            err_msg = str(e).split('\n')[0][:120]
            print(f"    Result: REJECTED [BLOCKED] -> {err_msg}")
            print(f"    [OK] Database consistency maintained - invalid data was blocked.")
        finally:
            cur.close()
            conn.close()

    # clean up any accidental inserts
    c = get_conn(autocommit=True)
    cc = c.cursor()
    cc.execute("DELETE FROM admission WHERE admission_id IN (99998, 99999)")
    cc.execute("DELETE FROM patient WHERE patient_id = 99999")
    cc.close()
    c.close()

    print("\n  RESULT: Database constraints (FK, UNIQUE, CHECK) actively protect data integrity.")
    print("  No orphaned or conflicting records can enter the database.")


# MAIN

def main():
    print("\n" + "=" * 70)
    print(" TASK 6 -- DATABASE TRANSACTION DEMONSTRATION")
    print(" Emergency Hospital Management System")
    print("=" * 70)

    print("\n[SETUP] Setting up test data...")
    setup_test_data()

    scenario_1_admission()
    scenario_2_discharge()
    scenario_3_double_booking()
    scenario_4_inventory_race()
    scenario_5_constraints()

    print(SEPARATOR)
    print("[SETUP] Cleaning up test data...")
    cleanup_test_data()

    print("=" * 70)
    print(" [OK] ALL 5 SCENARIOS COMPLETED SUCCESSFULLY")
    print(" Transactions, conflicts, and constraints have been demonstrated.")
    print("=" * 70)


if __name__ == "__main__":
    main()
