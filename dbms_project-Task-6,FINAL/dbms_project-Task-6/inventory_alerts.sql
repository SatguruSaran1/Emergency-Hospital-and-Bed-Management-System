-- ============================================================
-- INVENTORY AUTO-ALERT SYSTEM
-- Triggers a notification when stock falls below threshold
-- ============================================================

USE emergency_hospital_db;

-- 1. Create Notifications Table
CREATE TABLE IF NOT EXISTS notification (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    message VARCHAR(255) NOT NULL,
    type ENUM('Info', 'Warning', 'Critical') DEFAULT 'Warning',
    is_read BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. Create the Low Stock Trigger
DROP TRIGGER IF EXISTS trg_inventory_check;
DELIMITER $$

CREATE TRIGGER trg_inventory_check
AFTER UPDATE ON inventory
FOR EACH ROW
BEGIN
    -- Only trigger if stock WAS above threshold and is NOW at or below it
    IF NEW.quantity <= NEW.threshold_level AND OLD.quantity > NEW.threshold_level THEN
        INSERT INTO notification (message, type)
        VALUES (
            CONCAT('Low Stock Alert: "', 
                   (SELECT resource_name FROM resource WHERE resource_id = NEW.resource_id), 
                   '" is at ', NEW.quantity, ' (Threshold: ', NEW.threshold_level, ')'),
            'Critical'
        );
    END IF;
END$$

DELIMITER ;
