CREATE DATABASE hajj_db;
USE hajj_db;


-- strong entity 
 
CREATE TABLE hajjJatri (
    pilgrim_id    INT AUTO_INCREMENT PRIMARY KEY,
    full_name     VARCHAR(150) NOT NULL,
    passport_no   VARCHAR(30)  NOT NULL UNIQUE,   
    nationality   VARCHAR(80)  NOT NULL,
    date_of_birth TIMESTAMP NOT NULL,
    gender        CHAR(1) NOT NULL,              
    phone         VARCHAR(20) NOT NULL,
    email         VARCHAR(120) UNIQUE,
    address       VARCHAR(200),
    CONSTRAINT ck_gender CHECK (gender IN ('M','F'))
);

CREATE TABLE hajj_packages (
    package_id    INT AUTO_INCREMENT PRIMARY KEY,
    package_name  VARCHAR(150) NOT NULL,
    package_type  VARCHAR(50)  NOT NULL,  
    price         DECIMAL(10,2) NOT NULL, 
    duration_days INT NOT NULL,
    max_capacity  INT NOT NULL,
    CONSTRAINT ck_pkg_type CHECK (package_type IN ('Economy','Standard','Premium','VIP')),
    CONSTRAINT ck_positive_price CHECK (price > 0)
);

CREATE TABLE hotels (
    hotel_id      INT AUTO_INCREMENT PRIMARY KEY,
    hotel_name    VARCHAR(150) NOT NULL,
    location_city VARCHAR(50)  NOT NULL,
    star_rating   INT NOT NULL,
    total_rooms   INT NOT NULL,
    CONSTRAINT ck_city CHECK (location_city IN ('Makkah','Madinah','Other')),
    CONSTRAINT ck_stars CHECK (star_rating BETWEEN 1 AND 5)
);

CREATE TABLE flights (
    flight_id           INT AUTO_INCREMENT PRIMARY KEY,
    airline_name        VARCHAR(100) NOT NULL,
    flight_no           VARCHAR(20)  NOT NULL UNIQUE,
    origin              VARCHAR(100) NOT NULL,
    total_seats         INT NOT NULL
);

CREATE TABLE guides_muallims (
    guide_id          INT AUTO_INCREMENT PRIMARY KEY,
    guide_name        VARCHAR(150) NOT NULL,
    license_no        VARCHAR(50)  NOT NULL UNIQUE,
    language_spoken   VARCHAR(200) NOT NULL,
    years_experience  INT DEFAULT 0,
    CONSTRAINT ck_experience CHECK (years_experience >= 0)
);

CREATE TABLE transport_vehicles (
    vehicle_id        INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_type      VARCHAR(50) NOT NULL,
    plate_no          VARCHAR(20) NOT NULL UNIQUE,
    capacity          INT NOT NULL,
    driver_name       VARCHAR(150) NOT NULL,
    driver_phone      VARCHAR(20)  NOT NULL,
    route_description TEXT,
    CONSTRAINT ck_vehicle_type CHECK (vehicle_type IN ('Bus','Van','Car','Minibus')),
    CONSTRAINT ck_capacity     CHECK (capacity > 0)
);

-- weak entity

CREATE TABLE medical_records (
    record_id  INT AUTO_INCREMENT PRIMARY KEY,
    pilgrim_id INT NOT NULL UNIQUE, 
    blood_type VARCHAR(5),
    allergies  VARCHAR(30),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (pilgrim_id) REFERENCES hajjJatri(pilgrim_id) ON DELETE CASCADE,
    CONSTRAINT ck_blood CHECK (blood_type IN ('A+','A-','B+','B-','AB+','AB-','O+','O-'))
);

CREATE TABLE rooms (
    hotel_id    INT NOT NULL,
    room_number VARCHAR(10) NOT NULL,
    room_type   VARCHAR(50) NOT NULL,
    capacity    INT NOT NULL,
    price_per_night DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (hotel_id, room_number),
    FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id) ON DELETE CASCADE,
    CONSTRAINT ck_room_type CHECK (room_type IN ('Single','Double','Triple','Suite','Quad'))
);

CREATE TABLE vaccinations (
    vaccination_id INT AUTO_INCREMENT PRIMARY KEY,
    pilgrim_id INT NOT NULL,
    vaccine_name VARCHAR(100) NOT NULL,
    vaccination_date TIMESTAMP NOT NULL,
    expiry_date  TIMESTAMP,
    issued_by  VARCHAR(150),
    UNIQUE (pilgrim_id, vaccine_name, vaccination_date),
    FOREIGN KEY (pilgrim_id) REFERENCES hajjJatri(pilgrim_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT ck_expiry CHECK (
        expiry_date IS NULL OR expiry_date > vaccination_date
    )
);


CREATE TABLE emergency_contacts (
    contact_id INT AUTO_INCREMENT PRIMARY KEY,
    pilgrim_id INT NOT NULL,
    contact_name VARCHAR(150) NOT NULL,
    relationship VARCHAR(50)  NOT NULL,
    phone VARCHAR(20)  NOT NULL,
    email VARCHAR(120),
    FOREIGN KEY (pilgrim_id) REFERENCES hajjJatri(pilgrim_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT ck_relation CHECK (
        relationship IN ('Father','Mother','Spouse','Son','Daughter','Brother','Sister','Guardian','Other')
    )
);


-- Associative entity

CREATE TABLE registration (
    registration_id INT AUTO_INCREMENT PRIMARY KEY,
    pilgrim_id INT NOT NULL,
    package_id INT NOT NULL,
    registration_date TIMESTAMP NOT NULL,
    current_status VARCHAR(30) DEFAULT 'Pending',
    UNIQUE (pilgrim_id, package_id),   
    FOREIGN KEY (pilgrim_id) REFERENCES hajjJatri(pilgrim_id),
    FOREIGN KEY (package_id) REFERENCES hajj_packages(package_id),
    CONSTRAINT ck_status CHECK (current_status IN ('Pending','Confirmed','Cancelled','Completed'))
);

CREATE TABLE room_assignments (
    hotel_id    INT NOT NULL,
    room_number VARCHAR(10) NOT NULL,
    pilgrim_id  INT NOT NULL,
    check_in_date  TIMESTAMP NOT NULL,
    check_out_date TIMESTAMP NOT NULL,
    PRIMARY KEY (hotel_id, room_number, pilgrim_id),
    FOREIGN KEY (hotel_id, room_number) REFERENCES rooms(hotel_id, room_number),
    FOREIGN KEY (pilgrim_id) REFERENCES hajjJatri(pilgrim_id),
    CONSTRAINT ck_stay_duration CHECK (check_out_date > check_in_date)
);
 
 
CREATE TABLE group_guide (
    group_id INT AUTO_INCREMENT PRIMARY KEY,
    guide_id INT NOT NULL,
    group_name VARCHAR(100) NOT NULL,
    FOREIGN KEY (guide_id) REFERENCES guides_muallims(guide_id)
);

CREATE TABLE group_members (
    group_id   INT NOT NULL,
    pilgrim_id INT NOT NULL,
    PRIMARY KEY (group_id, pilgrim_id),
    FOREIGN KEY (group_id) REFERENCES group_guide(group_id) ON DELETE CASCADE,
    FOREIGN KEY (pilgrim_id) REFERENCES hajjJatri(pilgrim_id) ON DELETE CASCADE
);

CREATE TABLE payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    registration_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    transaction_ref VARCHAR(100) UNIQUE,
    FOREIGN KEY (registration_id) REFERENCES registration(registration_id),
    CONSTRAINT ck_payment_method CHECK (payment_method IN ('Cash','Card','Bank Transfer','Online'))
);


CREATE TABLE flight_bookings (
    flight_id  INT NOT NULL,
    pilgrim_id INT NOT NULL,
    seat_no VARCHAR(10) NOT NULL,
    ticket_class VARCHAR(30) NOT NULL,
    ticket_price DECIMAL(10,2) NOT NULL,
    booking_date TIMESTAMP NOT NULL,
    statuss VARCHAR(30) DEFAULT 'Confirmed',
    
    PRIMARY KEY (flight_id, pilgrim_id),
    UNIQUE (flight_id, seat_no),
    
    FOREIGN KEY (flight_id) REFERENCES flights(flight_id),
    FOREIGN KEY (pilgrim_id) REFERENCES hajjJatri(pilgrim_id),

    CONSTRAINT ck_class CHECK (
        ticket_class IN ('Economy','Business','First')
    ),
    CONSTRAINT ck_price CHECK (ticket_price > 0),
    CONSTRAINT ck_status1 CHECK (
        statuss IN ('Confirmed','Cancelled','Waitlisted')
    )
);
