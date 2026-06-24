
-- Task 5 - Emergency Hospital Management System
-- SQL Triggers for emergency_hospital_db


USE emergency_hospital_db;


-- TRIGGER 1: After a new admission is inserted,
--   - Set the assigned bed status to 'Occupied'
--   - Set the assigned doctor availability to 'Busy'

DROP TRIGGER IF EXISTS trg_after_admission_insert;

DELIMITER $$

CREATE TRIGGER trg_after_admission_insert
AFTER INSERT ON admission
FOR EACH ROW
BEGIN
    -- Update bed status to Occupied
    UPDATE bed
    SET status = 'Occupied'
    WHERE bed_id = NEW.bed_id;

    -- Update doctor availability to Busy
    UPDATE doctor
    SET availability_status = 'Busy'
    WHERE doctor_id = NEW.doctor_id;
END$$

DELIMITER ;

-- TRIGGER 2: After an admission is updated to 'Discharged',
--   - Set the bed back to 'Available'
--   - Set the doctor back to 'Available'
--   Also handles: if discharge_date is set but status not yet
--   changed, check for consistency

DROP TRIGGER IF EXISTS trg_after_discharge_update;

DELIMITER $$

CREATE TRIGGER trg_after_discharge_update
AFTER UPDATE ON admission
FOR EACH ROW
BEGIN
    -- Check if the admission status changed to Discharged
    IF NEW.status = 'Discharged' AND OLD.status != 'Discharged' THEN

        -- Free up the bed
        UPDATE bed
        SET status = 'Available'
        WHERE bed_id = NEW.bed_id;

        -- Check if the doctor has any other active admissions
        -- If not, set doctor back to Available
        IF (SELECT COUNT(*) FROM admission
            WHERE doctor_id = NEW.doctor_id
              AND status = 'Active') = 0 THEN
            UPDATE doctor
            SET availability_status = 'Available'
            WHERE doctor_id = NEW.doctor_id;
        END IF;

    END IF;
END$$

DELIMITER ;



SHOW TRIGGERS FROM emergency_hospital_db;
