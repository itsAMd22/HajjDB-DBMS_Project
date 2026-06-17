USE hajj_db;

DELIMITER $$

CREATE PROCEDURE sp_add_pilgrim(
    IN p_full_name   VARCHAR(150),
    IN p_passport_no VARCHAR(30),
    IN p_nationality VARCHAR(80),
    IN p_dob         TIMESTAMP,
    IN p_gender      CHAR(1),
    IN p_phone       VARCHAR(20),
    IN p_email       VARCHAR(120),
    IN p_address     VARCHAR(200)
)
BEGIN
    INSERT INTO hajjJatri
        (full_name, passport_no, nationality, date_of_birth, gender, phone, email, address)
    VALUES
        (p_full_name, p_passport_no, p_nationality, p_dob, p_gender, p_phone, p_email, p_address);
END$$

CREATE PROCEDURE sp_add_medical_record(
    IN p_pilgrim_id INT,
    IN p_blood_type VARCHAR(5),
    IN p_allergies  VARCHAR(30)
)
BEGIN
    INSERT INTO medical_records (pilgrim_id, blood_type, allergies)
    VALUES (p_pilgrim_id, p_blood_type, p_allergies)
    ON DUPLICATE KEY UPDATE
        blood_type = p_blood_type,
        allergies  = p_allergies;
END$$


CREATE PROCEDURE sp_add_vaccination(
    IN p_pilgrim_id       INT,
    IN p_vaccine_name     VARCHAR(100),
    IN p_vaccination_date TIMESTAMP,
    IN p_expiry_date      TIMESTAMP,
    IN p_issued_by        VARCHAR(150)
)
BEGIN
    INSERT INTO vaccinations
        (pilgrim_id, vaccine_name, vaccination_date, expiry_date, issued_by)
    VALUES
        (p_pilgrim_id, p_vaccine_name, p_vaccination_date, p_expiry_date, p_issued_by);
END$$


CREATE PROCEDURE sp_add_emergency_contact(
    IN p_pilgrim_id   INT,
    IN p_contact_name VARCHAR(150),
    IN p_relationship VARCHAR(50),
    IN p_phone        VARCHAR(20),
    IN p_email        VARCHAR(120)
)
BEGIN
    INSERT INTO emergency_contacts
        (pilgrim_id, contact_name, relationship, phone, email)
    VALUES
        (p_pilgrim_id, p_contact_name, p_relationship, p_phone, p_email);
END$$



CREATE PROCEDURE sp_register_pilgrim(
    IN p_pilgrim_id INT,
    IN p_package_id INT
)
BEGIN
    IF NOT fn_package_has_capacity(p_package_id) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Package is full. Registration rejected.';
    END IF;

    INSERT INTO registration (pilgrim_id, package_id, registration_date, current_status)
    VALUES (p_pilgrim_id, p_package_id, CURRENT_TIMESTAMP, 'Pending');
END$$



CREATE PROCEDURE sp_make_payment(
    IN p_registration_id INT,
    IN p_amount          DECIMAL(10,2),
    IN p_method          VARCHAR(50),
    IN p_txn_ref         VARCHAR(100)
)
BEGIN
    INSERT INTO payments (registration_id, amount, payment_method, transaction_ref)
    VALUES (p_registration_id, p_amount, p_method, p_txn_ref);
END$$


CREATE PROCEDURE sp_book_flight(
    IN p_flight_id  INT,
    IN p_pilgrim_id INT,
    IN p_seat_no    VARCHAR(10),
    IN p_class      VARCHAR(30),
    IN p_price      DECIMAL(10,2)
)
BEGIN
    IF fn_flight_available_seats(p_flight_id) <= 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Flight is fully booked. Booking rejected.';
    END IF;

    INSERT INTO flight_bookings
        (flight_id, pilgrim_id, seat_no, ticket_class, ticket_price, booking_date, statuss)
    VALUES
        (p_flight_id, p_pilgrim_id, p_seat_no, p_class, p_price, CURRENT_TIMESTAMP, 'Confirmed');
END$$


CREATE PROCEDURE sp_assign_room(
    IN p_hotel_id    INT,
    IN p_room_number VARCHAR(10),
    IN p_pilgrim_id  INT,
    IN p_check_in    DATE,
    IN p_check_out   DATE
)
BEGIN
    DECLARE v_capacity    INT DEFAULT 0;
    DECLARE v_current_occ INT DEFAULT 0;

    -- Get room capacity
    SELECT capacity INTO v_capacity
    FROM   rooms
    WHERE  hotel_id    = p_hotel_id
    AND    room_number = p_room_number;

    SELECT COUNT(*) INTO v_current_occ
    FROM   room_assignments
    WHERE  hotel_id      = p_hotel_id
    AND    room_number   = p_room_number
    AND    check_in_date  < p_check_out
    AND    check_out_date > p_check_in;

    IF v_current_occ >= v_capacity THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Room is at full capacity for this date range. Assignment rejected.';
    END IF;

    INSERT INTO room_assignments
        (hotel_id, room_number, pilgrim_id, check_in_date, check_out_date)
    VALUES
        (p_hotel_id, p_room_number, p_pilgrim_id, p_check_in, p_check_out);
END$$

CREATE PROCEDURE sp_join_group(
    IN p_group_id   INT,
    IN p_pilgrim_id INT
)
BEGIN
    INSERT INTO group_members (group_id, pilgrim_id)
    VALUES (p_group_id, p_pilgrim_id);
END$$

DELIMITER ;


