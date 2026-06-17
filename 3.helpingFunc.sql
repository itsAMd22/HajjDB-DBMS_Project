USE hajj_db;

DELIMITER $$

CREATE FUNCTION fn_package_registered_count(p_package_id INT)
RETURNS INT
READS SQL DATA
NOT DETERMINISTIC
BEGIN
    RETURN (
        SELECT COUNT(*) FROM registration
        WHERE  package_id    = p_package_id
        AND    current_status IN ('Pending','Confirmed')
    );
END$$


CREATE FUNCTION fn_package_has_capacity(p_package_id INT)
RETURNS BOOLEAN
READS SQL DATA
NOT DETERMINISTIC
BEGIN
    RETURN IFNULL(
        (SELECT fn_package_registered_count(p_package_id) < max_capacity
         FROM   hajj_packages
         WHERE  package_id = p_package_id),
        FALSE
    );
END$$



CREATE FUNCTION fn_total_paid(p_registration_id INT)
RETURNS DECIMAL(10,2)
READS SQL DATA
NOT DETERMINISTIC
BEGIN
    RETURN (
        SELECT COALESCE(SUM(amount), 0) FROM payments
        WHERE  registration_id = p_registration_id
    );
END$$



CREATE FUNCTION fn_outstanding_balance(p_registration_id INT)
RETURNS DECIMAL(10,2)
READS SQL DATA
NOT DETERMINISTIC
BEGIN
    RETURN (
        SELECT p.price - fn_total_paid(p_registration_id)
        FROM   registration r
        JOIN   hajj_packages p USING (package_id)
        WHERE  r.registration_id = p_registration_id
    );
END$$



CREATE FUNCTION fn_flight_available_seats(p_flight_id INT)
RETURNS INT
READS SQL DATA
NOT DETERMINISTIC
BEGIN
    DECLARE v_total  INT DEFAULT 0;
    DECLARE v_booked INT DEFAULT 0;

    SELECT total_seats INTO v_total
    FROM   flights
    WHERE  flight_id = p_flight_id;

    SELECT COUNT(*) INTO v_booked
    FROM   flight_bookings
    WHERE  flight_id = p_flight_id
    AND    statuss   = 'Confirmed';

    RETURN v_total - v_booked;
END$$

DELIMITER ;