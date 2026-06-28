
-- TASK 6: Database Transaction Demonstration - GUIDE
-- Emergency Hospital Management System


/*
   DOCUMENTATION / GUIDE:

   
   SCENARIO 1: Admission (Atomicity)
   - What is in DB now: Bed 9001 and Doctor 204 are 'Available'.
   - What will happen: We insert an admission record.
   - Triggers: 'trg_after_admission_insert' will automatically update bed 9001 to 'Occupied' 
     and doctor 204 to 'Busy'.
   - After: One INSERT updated 3 tables atomically.

   SCENARIO 2: Discharge (Consistency)
   - What is in DB now: Bed 9001 is 'Occupied', Doctor 204 is 'Busy'.
   - What will happen: We update the admission status to 'Discharged'.
   - Triggers: 'trg_after_discharge_update' will reset bed 9001 to 'Available' 
     and doctor 204 to 'Available'.
   - After: Database state is logically reversed to a clean state.

   SCENARIO 3: Double Booking (Isolation)
   - What is in DB now: Bed 9001 is 'Available'.
   - What will happen: 
     1. Session A successfully admits a patient (Bed becomes Occupied).
     2. Session B tries to book the SAME bed.
     3. The INSERT for Session B will fail because bed_id is UNIQUE.
   - Proof: The second query is blocked, proving concurrency protection.

   SCENARIO 4: Inventory Race Condition
   - What is in DB now: Oxygen Cylinder (ID 501) has qty = 50.
   - What will happen: 
     1. User A locks row and deducts 40 (50 -> 10).
     2. User B locks row, sees 10, wants 40, but fails.
   - After: Stock never goes negative.

   SCENARIO 5: Constraint Enforcement
   - Logic: MySQL rejects invalid data (invalid IDs or duplicate unique keys).
   - This proves the database maintains integrity even if the app sends bad data.
*/



-- EXECUTABLE SQL CODE STARTS HERE


USE emergency_hospital_db;

-- 1. SETUP
    DELETE FROM admission WHERE admission_id IN (9901, 9902, 99997, 99998, 99999);
    DELETE FROM bed WHERE bed_id IN (9001, 9002);
    DELETE FROM patient WHERE patient_id IN (9901, 9902);
    INSERT INTO patient VALUES (9901, 'Test Patient A', 30, 'Male', 'Medium');
    INSERT INTO patient VALUES (9902, 'Test Patient B', 28, 'Female', 'Low');
    INSERT INTO bed VALUES (9001, 'General', 'Available', 102);
    INSERT INTO bed VALUES (9002, 'General', 'Available', 102);
    UPDATE doctor SET availability_status = 'Available' WHERE doctor_id = 204;

-- 2. SCENARIO 1 (Admission)
    START TRANSACTION;
    INSERT INTO admission (admission_id, admission_date, discharge_date, status, patient_id, doctor_id, bed_id)
    VALUES (9901, NOW(), NULL, 'Active', 9901, 204, 9001);
    COMMIT;
    SELECT bed_id, status FROM bed WHERE bed_id = 9001;
    SELECT doctor_id, name, availability_status FROM doctor WHERE doctor_id = 204;

-- 3. SCENARIO 2 (Discharge)
    START TRANSACTION;
    UPDATE admission SET status = 'Discharged', discharge_date = CURDATE() WHERE admission_id = 9901;
    COMMIT;
    SELECT bed_id, status FROM bed WHERE bed_id = 9001;
    SELECT doctor_id, name, availability_status FROM doctor WHERE doctor_id = 204;

-- 4. SCENARIO 3 (Double Booking)
    DELETE FROM admission WHERE admission_id = 9901;
    -- Session A
    START TRANSACTION;
    INSERT INTO admission (admission_id, admission_date, discharge_date, status, patient_id, doctor_id, bed_id)
    VALUES (9901, NOW(), NULL, 'Active', 9901, 204, 9001);
    COMMIT;
    -- Session B (Will fail)
    START TRANSACTION;
    SELECT bed_id, status FROM bed WHERE bed_id = 9001 FOR UPDATE;
    INSERT INTO admission (admission_id, admission_date, discharge_date, status, patient_id, doctor_id, bed_id)
    VALUES (9902, NOW(), NULL, 'Active', 9902, 204, 9001);
    ROLLBACK;
    SELECT * FROM admission WHERE bed_id = 9001;

-- 5. SCENARIO 4 (Inventory)
    UPDATE inventory SET quantity = 50 WHERE inventory_id = 501;
    START TRANSACTION;
    SELECT quantity FROM inventory WHERE inventory_id = 501 FOR UPDATE;
    UPDATE inventory SET quantity = quantity - 40 WHERE inventory_id = 501;
    COMMIT;
    START TRANSACTION;
    SELECT quantity FROM inventory WHERE inventory_id = 501 FOR UPDATE;
    ROLLBACK;
    SELECT quantity FROM inventory WHERE inventory_id = 501;

-- 6. SCENARIO 5 (Constraints)
    -- 5a. Invalid Patient
    INSERT INTO admission VALUES (99999, NOW(), NULL, 'Active', 88888, 204, 9002);
    -- 5b. Invalid Doctor
    INSERT INTO admission VALUES (99998, NOW(), NULL, 'Active', 9902, 99999, 9002);
    -- 5c. Duplicate Bed
    INSERT INTO admission VALUES (99997, NOW(), NULL, 'Active', 9902, 204, 9001);

-- 7. CLEANUP
    DELETE FROM admission WHERE admission_id IN (9901, 9902, 99997, 99998, 99999);
    DELETE FROM bed WHERE bed_id IN (9001, 9002);
    DELETE FROM patient WHERE patient_id IN (9901, 9902);
    UPDATE doctor SET availability_status = 'Available' WHERE doctor_id = 204;
    UPDATE inventory SET quantity = 50 WHERE inventory_id = 501;
