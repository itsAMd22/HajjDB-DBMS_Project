USE hajj_db;

DELIMITER $$

CREATE TRIGGER trg_after_pilgrim_insert
AFTER INSERT ON hajjJatri
FOR EACH ROW
BEGIN
    INSERT INTO medical_records (pilgrim_id)
    VALUES (NEW.pilgrim_id);
END$$


CREATE TRIGGER trg_after_payment_insert
AFTER INSERT ON payments
FOR EACH ROW
BEGIN
    UPDATE registration
    SET    current_status = 'Confirmed'
    WHERE  registration_id = NEW.registration_id
    AND    fn_outstanding_balance(NEW.registration_id) <= 0;
END$$

CREATE TRIGGER trg_after_payment_update
AFTER UPDATE ON payments
FOR EACH ROW
BEGIN
    UPDATE registration
    SET    current_status = 'Confirmed'
    WHERE  registration_id = NEW.registration_id
    AND    fn_outstanding_balance(NEW.registration_id) <= 0;
END$$

DELIMITER ;
