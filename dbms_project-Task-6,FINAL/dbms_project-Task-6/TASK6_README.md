# Task 6 — Database Transaction Demonstration

## Overview

This document explains how the **Emergency Hospital Management System** uses database transactions to ensure **consistency**, handle **conflicting scenarios**, and maintain **concurrency control** across multiple tables.

All demonstrations are implemented in [`task6_transactions_demo.py`](task6_transactions_demo.py) and can be executed via:

```bash
python task6_transactions_demo.py
```

---

## 1. Transactions in the System

A **transaction** is a group of SQL operations that either all succeed (**COMMIT**) or all fail (**ROLLBACK**). Our system uses `InnoDB`, which supports full ACID transactions.

| Property      | How It Is Applied                                                                 |
|---------------|-----------------------------------------------------------------------------------|
| **Atomicity**     | Admission INSERT + trigger UPDATEs on `bed` and `doctor` happen as one unit.  |
| **Consistency**   | CHECK, FOREIGN KEY, and ENUM constraints reject invalid data before commit.   |
| **Isolation**     | `SELECT ... FOR UPDATE` row locks prevent two transactions from modifying the same row simultaneously. |
| **Durability**    | Once a COMMIT succeeds, the data is permanently written to disk by InnoDB.    |

---

## 2. Transaction Scenarios Demonstrated

### Scenario 1 — Admission (Multi-Table Atomicity)

**What happens:** A single `INSERT INTO admission` fires the `trg_after_admission_insert` trigger, which atomically:
- Sets the assigned **bed** status → `Occupied`
- Sets the assigned **doctor** status → `Busy`

```
START TRANSACTION;
  INSERT INTO admission (...) VALUES (...);
  -- trigger fires automatically:
  --   UPDATE bed SET status = 'Occupied' ...
  --   UPDATE doctor SET availability_status = 'Busy' ...
COMMIT;
```

**Effect:** Three tables (`admission`, `bed`, `doctor`) are modified in a single atomic operation. If any step fails, the entire transaction rolls back.

---

### Scenario 2 — Discharge (Trigger-Based State Reversal)

**What happens:** Updating an admission to `Discharged` fires the `trg_after_discharge_update` trigger, which:
- Sets the **bed** status → `Available`
- Checks if the **doctor** has other active patients:
  - If **no** → sets doctor → `Available`
  - If **yes** → doctor stays `Busy`

```
START TRANSACTION;
  UPDATE admission SET status = 'Discharged', discharge_date = CURDATE()
    WHERE admission_id = 9901;
  -- trigger fires:
  --   UPDATE bed SET status = 'Available' ...
  --   IF no other active admissions FOR doctor THEN
  --       UPDATE doctor SET availability_status = 'Available'
COMMIT;
```

**Effect:** The discharge cleanly reverses all state changes made during admission, maintaining referential consistency.

---

### Scenario 3 — Conflict: Double-Booking a Bed

**Problem:** Two administrators simultaneously try to admit two different patients to bed 1008.

**Without concurrency control:** Both transactions read bed status as `Available`, both insert, and the bed is double-booked — a critical data integrity violation.

**With SELECT ... FOR UPDATE:**

```
-- Transaction A                          -- Transaction B
START TRANSACTION;                        START TRANSACTION;
SELECT ... FROM bed                       SELECT ... FROM bed
  WHERE bed_id=1008 FOR UPDATE;             WHERE bed_id=1008 FOR UPDATE;
-- A acquires lock                        -- B WAITS (blocked by A's lock)
-- A sees status = 'Available'
INSERT INTO admission (...);
COMMIT;                                   -- B now acquires lock
                                          -- B sees status = 'Occupied'
                                          ROLLBACK; ← conflict detected!
```

**Effect:** Row-level locking ensures **only one** transaction succeeds. The second detects the conflict and safely rolls back. No double-booking occurs.

---

### Scenario 4 — Conflict: Inventory Race Condition

**Problem:** Two nurses simultaneously try to consume 40 units from a stock of 50 Oxygen Cylinders. Without locking, both would read `qty=50`, deduct 40 each, and the stock would become **-30** (impossible!).

**With SELECT ... FOR UPDATE:**

```
-- Transaction A                          -- Transaction B
START TRANSACTION;                        START TRANSACTION;
SELECT quantity FROM inventory            SELECT quantity FROM inventory
  WHERE id=501 FOR UPDATE;                  WHERE id=501 FOR UPDATE;
-- A reads qty=50, locks row              -- B WAITS
UPDATE SET quantity=10;
COMMIT;                                   -- B now reads qty=10
                                          -- 10 < 40 → insufficient stock
                                          ROLLBACK;
```

**Effect:** Stock never goes negative. The CHECK constraint (`quantity >= 0`) provides a secondary safety net.

---

### Scenario 5 — Constraint Enforcement

MySQL CHECK, FOREIGN KEY, and ENUM constraints immediately reject invalid data:

| Test Case | Constraint Violated | Result |
|-----------|---------------------|--------|
| Patient age = 200 | `chk_age_valid` (age BETWEEN 0 AND 120) | ❌ REJECTED |
| Admission with non-existent doctor_id | `admission_ibfk_2` (FK → doctor) | ❌ REJECTED |
| Setting inventory quantity = -5 | `chk_quantity_positive` (quantity ≥ 0) | ❌ REJECTED |
| Discharge date before admission date | `chk_dates` (discharge ≥ admission) | ❌ REJECTED |

**Effect:** No invalid data can enter the database, regardless of the application code.

---

## 3. Concurrency Control Mechanisms

| Mechanism | Purpose | Used Where |
|-----------|---------|------------|
| `START TRANSACTION` / `COMMIT` / `ROLLBACK` | Group operations atomically | All admission, discharge, inventory operations |
| `SELECT ... FOR UPDATE` (Row-Level Locking) | Prevent concurrent modification of the same row | Bed booking, inventory deduction |
| `SERIALIZABLE` Isolation Level | Strictest isolation; prevents phantom reads | Conflict scenarios 3 & 4 |
| Triggers | Automatically enforce multi-table state transitions | Admission → bed/doctor, Discharge → bed/doctor, Inventory → notification |
| CHECK Constraints | Prevent invalid values at the database level | Age range, positive quantities, date ordering |
| FOREIGN KEY Constraints | Prevent orphan references | admission → patient, doctor, bed |

---

## 4. How the Database Is Affected

### State Transition Diagram

```
  ADMISSION FLOW:
  ┌─────────────┐    INSERT admission    ┌──────────────┐
  │ Bed:        │ ──────────────────────→ │ Bed:         │
  │ Available   │   (trigger fires)       │ Occupied     │
  └─────────────┘                         └──────────────┘
  ┌─────────────┐                         ┌──────────────┐
  │ Doctor:     │ ──────────────────────→ │ Doctor:      │
  │ Available   │                         │ Busy         │
  └─────────────┘                         └──────────────┘

  DISCHARGE FLOW:
  ┌─────────────┐    UPDATE admission     ┌──────────────┐
  │ Bed:        │ ──────────────────────→ │ Bed:         │
  │ Occupied    │   status='Discharged'   │ Available    │
  └─────────────┘   (trigger fires)       └──────────────┘
  ┌─────────────┐                         ┌──────────────┐
  │ Doctor:     │ ──────────(if no other  │ Doctor:      │
  │ Busy        │   active patients)────→ │ Available    │
  └─────────────┘                         └──────────────┘
```

### Tables Modified by Each Transaction

| Transaction | admission | bed | doctor | inventory | notification |
|-------------|:---------:|:---:|:------:|:---------:|:------------:|
| Admit Patient | INSERT | UPDATE (trigger) | UPDATE (trigger) | – | – |
| Discharge Patient | UPDATE | UPDATE (trigger) | UPDATE (trigger) | – | – |
| Use Inventory | – | – | – | UPDATE | INSERT (trigger, if low stock) |
| Add Patient | – | – | – | – | – |

---

## 5. Summary

The Emergency Hospital Management System uses MySQL's InnoDB transaction engine with:

- **Atomic multi-table transactions** via triggers to keep `bed`, `doctor`, and `admission` in sync
- **Row-level locking** (`SELECT ... FOR UPDATE`) to prevent conflicts like double-booking beds and inventory race conditions
- **CHECK and FK constraints** as a safety net that blocks invalid data regardless of application logic
- **Serializable isolation** for critical concurrent operations

These mechanisms together ensure that the database remains **consistent**, **concurrent-safe**, and **durable** even under simultaneous access by multiple hospital staff.

---

## 6. Running the Demo

```bash
# Ensure MySQL is running and the database is initialised
python task6_transactions_demo.py
```

The script will:
1. Create temporary test data
2. Run all 5 scenarios with printed output
3. Clean up test data automatically

No permanent changes are made to the database.
