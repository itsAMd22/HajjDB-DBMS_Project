import os
import mysql.connector
from mysql.connector import Error
from tabulate import tabulate
from dotenv import load_dotenv

# ─────────────────────────────────────────────
# DB CONNECTION
# ─────────────────────────────────────────────

load_dotenv()

def get_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
    except Error as e:
        print(f"❌ Database Connection Error: {e}")
        print("Please check if your local .env file is configured correctly.")
        return None

def execute_query(conn, query, params=None, fetch=False):
    cursor = conn.cursor()
    try:
        cursor.execute(query, params or ())
        if fetch:
            rows = cursor.fetchall()
            cols = [d[0] for d in cursor.description]
            return cols, rows
        else:
            conn.commit()
            return cursor.rowcount
    except Error as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()

def call_proc(conn, proc_name, args=()):
    cursor = conn.cursor()
    try:
        cursor.callproc(proc_name, args)
        conn.commit()
        print(f"  ✔ {proc_name} executed successfully.")
    except Error as e:
        conn.rollback()
        print(f"  ✘ Error: {e.msg}")
    finally:
        cursor.close()

def call_proc_return_id(conn, proc_name, args=()):
    """Call a procedure and return the last inserted ID."""
    cursor = conn.cursor()
    try:
        cursor.callproc(proc_name, args)
        conn.commit()
        last_id = cursor.lastrowid
        return last_id
    except Error as e:
        conn.rollback()
        print(f"  ✘ Error: {e.msg}")
        return None
    finally:
        cursor.close()

def print_table(cols, rows):
    if not rows:
        print("  (no results)")
    else:
        print(tabulate(rows, headers=cols, tablefmt="rounded_outline"))

def separator():
    print("\n" + "─" * 55)

# ─────────────────────────────────────────────
# SHARED HELPERS
# ─────────────────────────────────────────────

def input_int(prompt):
    while True:
        val = input(prompt).strip()
        if val.lstrip('-').isdigit():
            return int(val)
        print("  Please enter a valid integer.")

def input_decimal(prompt):
    while True:
        val = input(prompt).strip()
        try:
            return float(val)
        except ValueError:
            print("  Please enter a valid number.")

# ─────────────────────────────────────────────
# ADMIN FUNCTIONS
# ─────────────────────────────────────────────

def admin_add_pilgrim(conn):
    separator()
    print("  ADD NEW PILGRIM")
    separator()
    full_name   = input("  Full Name         : ").strip()
    passport_no = input("  Passport No       : ").strip()
    nationality = input("  Nationality       : ").strip()
    dob         = input("  Date of Birth (YYYY-MM-DD): ").strip()
    gender      = input("  Gender (M/F)      : ").strip().upper()
    phone       = input("  Phone             : ").strip()
    email       = input("  Email             : ").strip()
    address     = input("  Address           : ").strip()

    cursor = conn.cursor()
    try:
        cursor.callproc("sp_add_pilgrim",
                        (full_name, passport_no, nationality, dob,
                         gender, phone, email, address))
        conn.commit()
        # fetch the new pilgrim_id
        cursor.execute("SELECT pilgrim_id FROM hajjJatri WHERE passport_no = %s", (passport_no,))
        row = cursor.fetchone()
        if row:
            print(f"  ✔ Pilgrim added successfully. Assigned Pilgrim ID: {row[0]}")
            print(f"  ℹ  Give this ID to the pilgrim so they can log in.")
        else:
            print("  ✔ Pilgrim added (could not retrieve ID).")
    except Error as e:
        conn.rollback()
        print(f"  ✘ Error: {e.msg}")
    finally:
        cursor.close()

def admin_show_available_flights(conn):
    separator()
    print("  AVAILABLE FLIGHTS (seats remaining > 0)")
    separator()
    cols, rows = execute_query(conn, """
        SELECT f.flight_id, f.airline_name, f.flight_no, f.origin,
               fn_flight_available_seats(f.flight_id) AS available_seats
        FROM   flights f
        HAVING available_seats > 0
    """, fetch=True)
    print_table(cols, rows)

def admin_show_available_packages(conn):
    separator()
    print("  AVAILABLE PACKAGES (not full)")
    separator()
    cols, rows = execute_query(conn, """
        SELECT p.package_id, p.package_name, p.package_type,
               p.price, p.duration_days, p.max_capacity,
               fn_package_registered_count(p.package_id) AS registered,
               p.max_capacity - fn_package_registered_count(p.package_id) AS remaining
        FROM   hajj_packages p
        HAVING remaining > 0
    """, fetch=True)
    print_table(cols, rows)

def admin_show_available_rooms(conn):
    separator()
    print("  AVAILABLE ROOMS")
    check_in  = input("  Check-in date  (YYYY-MM-DD): ").strip()
    check_out = input("  Check-out date (YYYY-MM-DD): ").strip()
    separator()
    cols, rows = execute_query(conn, """
        SELECT r.hotel_id, h.hotel_name, h.location_city,
               r.room_number, r.room_type, r.capacity, r.price_per_night,
               r.capacity - COALESCE((
                   SELECT COUNT(*) FROM room_assignments ra
                   WHERE  ra.hotel_id    = r.hotel_id
                   AND    ra.room_number = r.room_number
                   AND    ra.check_in_date  < %s
                   AND    ra.check_out_date > %s
               ), 0) AS available_spots
        FROM   rooms r
        JOIN   hotels h ON h.hotel_id = r.hotel_id
        HAVING available_spots > 0
        ORDER  BY h.location_city, r.hotel_id, r.room_number
    """, (check_out, check_in), fetch=True)
    print_table(cols, rows)

def admin_register_pilgrim(conn):
    separator()
    print("  REGISTER PILGRIM TO PACKAGE")
    admin_show_available_packages(conn)
    separator()
    pilgrim_id = input_int("  Pilgrim ID   : ")
    package_id = input_int("  Package ID   : ")
    call_proc(conn, "sp_register_pilgrim", (pilgrim_id, package_id))

def admin_book_flight(conn):
    separator()
    print("  BOOK FLIGHT FOR PILGRIM")
    admin_show_available_flights(conn)
    separator()
    flight_id  = input_int("  Flight ID    : ")
    pilgrim_id = input_int("  Pilgrim ID   : ")
    seat_no    = input("  Seat No      : ").strip()
    cls        = input("  Class (Economy/Business/First): ").strip()
    price      = input_decimal("  Ticket Price : ")
    call_proc(conn, "sp_book_flight", (flight_id, pilgrim_id, seat_no, cls, price))

def admin_assign_room(conn):
    separator()
    print("  ASSIGN HOTEL ROOM TO PILGRIM")
    admin_show_available_rooms(conn)
    separator()
    hotel_id   = input_int("  Hotel ID     : ")
    room_no    = input("  Room Number  : ").strip()
    pilgrim_id = input_int("  Pilgrim ID   : ")
    check_in   = input("  Check-in  (YYYY-MM-DD): ").strip()
    check_out  = input("  Check-out (YYYY-MM-DD): ").strip()
    call_proc(conn, "sp_assign_room", (hotel_id, room_no, pilgrim_id, check_in, check_out))

def admin_record_payment(conn):
    separator()
    print("  RECORD PAYMENT")
    reg_id  = input_int("  Registration ID  : ")
    amount  = input_decimal("  Amount           : ")
    method  = input("  Method (Cash/Card/Bank Transfer/Online): ").strip()
    txn_ref = input("  Transaction Ref  : ").strip()
    call_proc(conn, "sp_make_payment", (reg_id, amount, method, txn_ref))

def admin_add_guide_group(conn):
    separator()
    print("  ADD GUIDE GROUP")
    guide_id   = input_int("  Guide ID     : ")
    group_name = input("  Group Name   : ").strip()
    try:
        execute_query(conn,
            "INSERT INTO group_guide (guide_id, group_name) VALUES (%s, %s)",
            (guide_id, group_name))
        print("  ✔ Group created.")
    except Error as e:
        print(f"  ✘ Error: {e.msg}")

def admin_assign_pilgrim_group(conn):
    separator()
    print("  ASSIGN PILGRIM TO GROUP")
    separator()
    cols, rows = execute_query(conn,
        "SELECT group_id, group_name, guide_id FROM group_guide", fetch=True)
    print_table(cols, rows)
    separator()
    group_id   = input_int("  Group ID     : ")
    pilgrim_id = input_int("  Pilgrim ID   : ")
    call_proc(conn, "sp_join_group", (group_id, pilgrim_id))

def admin_view_pilgrim(conn):
    separator()
    print("  VIEW PILGRIM INFO")
    pilgrim_id = input_int("  Pilgrim ID   : ")
    separator()
    cols, rows = execute_query(conn,
        "SELECT * FROM hajjJatri WHERE pilgrim_id = %s", (pilgrim_id,), fetch=True)
    print("  Personal Info:")
    print_table(cols, rows)

    cols, rows = execute_query(conn,
        "SELECT * FROM medical_records WHERE pilgrim_id = %s", (pilgrim_id,), fetch=True)
    print("\n  Medical Record:")
    print_table(cols, rows)

    cols, rows = execute_query(conn, """
        SELECT r.registration_id, p.package_name, r.current_status,
               r.registration_date,
               fn_outstanding_balance(r.registration_id) AS outstanding_balance
        FROM   registration r
        JOIN   hajj_packages p USING (package_id)
        WHERE  r.pilgrim_id = %s
    """, (pilgrim_id,), fetch=True)
    print("\n  Registrations:")
    print_table(cols, rows)

def admin_menu(conn):
    options = {
        "1":  ("Add new pilgrim",                admin_add_pilgrim),
        "2":  ("Register pilgrim to package",    admin_register_pilgrim),
        "3":  ("Book flight for pilgrim",         admin_book_flight),
        "4":  ("Assign hotel room to pilgrim",    admin_assign_room),
        "5":  ("Record payment",                  admin_record_payment),
        "6":  ("Add guide group",                 admin_add_guide_group),
        "7":  ("Assign pilgrim to group",         admin_assign_pilgrim_group),
        "8":  ("View pilgrim info",               admin_view_pilgrim),
        "9":  ("Show all available flights",      admin_show_available_flights),
        "10": ("Show all available packages",     admin_show_available_packages),
        "11": ("Show all available rooms",        admin_show_available_rooms),
    }

    while True:
        separator()
        print("  ADMIN PANEL")
        separator()
        for k, (label, _) in options.items():
            print(f"  [{k:>2}] {label}")
        print("  [ 0] Back to main menu")
        separator()
        choice = input("  Choice: ").strip()

        if choice == "0":
            break
        elif choice in options:
            try:
                options[choice][1](conn)
            except Error as e:
                print(f"  ✘ Unexpected error: {e.msg}")
        else:
            print("  Invalid option.")

# ─────────────────────────────────────────────
# PILGRIM FUNCTIONS
# ─────────────────────────────────────────────

def pilgrim_update_personal_info(conn, pilgrim_id):
    separator()
    print("  UPDATE PERSONAL INFO")
    separator()
    print("  (leave blank to keep existing value)")
    separator()

    cols, rows = execute_query(conn,
        "SELECT * FROM hajjJatri WHERE pilgrim_id = %s", (pilgrim_id,), fetch=True)
    print("  Current Info:")
    print_table(cols, rows)
    separator()

    phone   = input("  New Phone   (or blank): ").strip()
    email   = input("  New Email   (or blank): ").strip()
    address = input("  New Address (or blank): ").strip()

    fields, vals = [], []
    if phone:
        fields.append("phone = %s");   vals.append(phone)
    if email:
        fields.append("email = %s");   vals.append(email)
    if address:
        fields.append("address = %s"); vals.append(address)

    if not fields:
        print("  Nothing to update.")
        return

    vals.append(pilgrim_id)
    try:
        execute_query(conn,
            f"UPDATE hajjJatri SET {', '.join(fields)} WHERE pilgrim_id = %s", vals)
        print("  ✔ Personal info updated.")
    except Error as e:
        print(f"  ✘ Error: {e.msg}")

def pilgrim_add_medical(conn, pilgrim_id):
    separator()
    print("  ADD / UPDATE MEDICAL RECORD")
    blood_type = input("  Blood Type (A+/A-/B+/B-/AB+/AB-/O+/O-): ").strip()
    allergies  = input("  Allergies  : ").strip()
    call_proc(conn, "sp_add_medical_record", (pilgrim_id, blood_type, allergies))

def pilgrim_add_vaccination(conn, pilgrim_id):
    separator()
    print("  ADD VACCINATION")
    vaccine_name = input("  Vaccine Name        : ").strip()
    vacc_date    = input("  Vaccination Date (YYYY-MM-DD): ").strip()
    expiry       = input("  Expiry Date  (YYYY-MM-DD or blank): ").strip() or None
    issued_by    = input("  Issued By           : ").strip()
    call_proc(conn, "sp_add_vaccination",
              (pilgrim_id, vaccine_name, vacc_date, expiry, issued_by))

def pilgrim_add_emergency_contact(conn, pilgrim_id):
    separator()
    print("  ADD EMERGENCY CONTACT")
    name     = input("  Contact Name : ").strip()
    relation = input("  Relationship (Father/Mother/Spouse/Son/Daughter/Brother/Sister/Guardian/Other): ").strip()
    phone    = input("  Phone        : ").strip()
    email    = input("  Email        : ").strip()
    call_proc(conn, "sp_add_emergency_contact",
              (pilgrim_id, name, relation, phone, email))

def pilgrim_view_status(conn, pilgrim_id):
    separator()
    print("  YOUR REGISTRATION STATUS & BALANCE")
    cols, rows = execute_query(conn, """
        SELECT r.registration_id, p.package_name, p.price,
               r.current_status, r.registration_date,
               fn_total_paid(r.registration_id)          AS total_paid,
               fn_outstanding_balance(r.registration_id) AS outstanding
        FROM   registration r
        JOIN   hajj_packages p USING (package_id)
        WHERE  r.pilgrim_id = %s
    """, (pilgrim_id,), fetch=True)
    print_table(cols, rows)

def pilgrim_view_vaccinations(conn, pilgrim_id):
    separator()
    print("  YOUR VACCINATIONS")
    cols, rows = execute_query(conn,
        "SELECT * FROM vaccinations WHERE pilgrim_id = %s", (pilgrim_id,), fetch=True)
    print_table(cols, rows)

def pilgrim_view_emergency_contacts(conn, pilgrim_id):
    separator()
    print("  YOUR EMERGENCY CONTACTS")
    cols, rows = execute_query(conn,
        "SELECT * FROM emergency_contacts WHERE pilgrim_id = %s", (pilgrim_id,), fetch=True)
    print_table(cols, rows)

def pilgrim_view_flight(conn, pilgrim_id):
    separator()
    print("  YOUR FLIGHT BOOKINGS")
    cols, rows = execute_query(conn, """
        SELECT f.airline_name, f.flight_no, f.origin,
               fb.seat_no, fb.ticket_class, fb.ticket_price, fb.statuss
        FROM   flight_bookings fb
        JOIN   flights f USING (flight_id)
        WHERE  fb.pilgrim_id = %s
    """, (pilgrim_id,), fetch=True)
    print_table(cols, rows)

def pilgrim_menu(conn):
    pilgrim_id = input_int("  Enter your Pilgrim ID: ")

    cols, rows = execute_query(conn,
        "SELECT full_name FROM hajjJatri WHERE pilgrim_id = %s",
        (pilgrim_id,), fetch=True)
    if not rows:
        print(f"  ✘ No pilgrim found with ID {pilgrim_id}.")
        print(f"  ℹ  Ask your admin to register you first.")
        return

    name = rows[0][0]

    options = {
        "1": ("Update personal info",               lambda c: pilgrim_update_personal_info(c, pilgrim_id)),
        "2": ("Add / update medical record",         lambda c: pilgrim_add_medical(c, pilgrim_id)),
        "3": ("Add vaccination record",              lambda c: pilgrim_add_vaccination(c, pilgrim_id)),
        "4": ("Add emergency contact",               lambda c: pilgrim_add_emergency_contact(c, pilgrim_id)),
        "5": ("View registration status & balance",  lambda c: pilgrim_view_status(c, pilgrim_id)),
        "6": ("View vaccinations",                   lambda c: pilgrim_view_vaccinations(c, pilgrim_id)),
        "7": ("View emergency contacts",             lambda c: pilgrim_view_emergency_contacts(c, pilgrim_id)),
        "8": ("View flight bookings",                lambda c: pilgrim_view_flight(c, pilgrim_id)),
    }

    while True:
        separator()
        print(f"  PILGRIM PANEL  —  Welcome, {name}  (ID: {pilgrim_id})")
        separator()
        for k, (label, _) in options.items():
            print(f"  [{k}] {label}")
        print("  [0] Back to main menu")
        separator()
        choice = input("  Choice: ").strip()

        if choice == "0":
            break
        elif choice in options:
            try:
                options[choice][1](conn)
            except Error as e:
                print(f"  ✘ Unexpected error: {e.msg}")
        else:
            print("  Invalid option.")

# ─────────────────────────────────────────────
# RAW SQL  —  accessible by anyone
# ─────────────────────────────────────────────

def raw_sql_menu(conn):
    while True:
        separator()
        print("  RAW SQL CONSOLE")
        print("  Enter your query (end with ';' or a blank line).")
        print("  Type '0' on an empty line to go back to main menu.")
        separator()

        lines = []
        while True:
            line = input("  sql> ")
            if line.strip() == "0" and not lines:
                return
            lines.append(line)
            if line.strip().endswith(";") or line.strip() == "":
                break

        query = " ".join(lines).strip().rstrip(";").strip()
        if not query:
            continue

        try:
            result = execute_query(conn, query, fetch=True)
            if isinstance(result, tuple):
                cols, rows = result
                print_table(cols, rows)
            else:
                print(f"  ✔ Query OK. Rows affected: {result}")
        except Error as e:
            print(f"  ✘ SQL Error: {e.msg}")

# ─────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────

def main():
    print("\n" + "═" * 55)
    print("   HAJJ MANAGEMENT SYSTEM")
    print("═" * 55)

    try:
        conn = get_connection()
        print("  ✔ Connected to hajj_db\n")
    except Error as e:
        print(f"  ✘ Could not connect to database: {e.msg}")
        return

    while True:
        separator()
        print("  MAIN MENU")
        separator()
        print("  [ 1]  Admin")
        print("  [ 2]  Pilgrim")
        print("  [ 3]  Raw SQL")
        print("  [-1]  Exit")
        separator()
        choice = input("  Enter choice: ").strip()

        if choice == "-1":
            print("\n  Goodbye!\n")
            break
        elif choice == "1":
            admin_menu(conn)
        elif choice == "2":
            pilgrim_menu(conn)
        elif choice == "3":
            raw_sql_menu(conn)
        else:
            print("  Invalid choice. Please enter 1, 2, 3, or -1.")

    conn.close()

if __name__ == "__main__":
    main()
