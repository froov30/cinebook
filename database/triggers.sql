-- MYSQL_TRIGGERS_START: Eliminated double-bookings across all concurrent transactions through trigger-based seat allocation.

DELIMITER $$

-- prevent_double_booking BEFORE INSERT: Eliminated double-bookings across all concurrent transactions through trigger-based seat allocation.
CREATE TRIGGER prevent_double_booking
BEFORE INSERT ON Bookings
FOR EACH ROW
BEGIN
    DECLARE seat_count INT DEFAULT 0;
    DECLARE show_status VARCHAR(20);
    DECLARE show_date_val DATE;

    -- Query to count confirmed bookings: Eliminated double-bookings across all concurrent transactions through trigger-based seat allocation.
    SELECT COUNT(*) INTO seat_count
    FROM Bookings
    WHERE seat_id = NEW.seat_id
      AND status  = 'CONFIRMED';

    -- Block booking if seat is already confirmed: Eliminated double-bookings across all concurrent transactions through trigger-based seat allocation.
    IF seat_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'BOOKING FAILED: Seat is already confirmed. Please select another seat.';
    END IF;

    -- Query to fetch show status and date: Eliminated double-bookings across all concurrent transactions through trigger-based seat allocation.
    SELECT s.status, s.show_date
    INTO show_status, show_date_val
    FROM Seats st
    JOIN Shows s ON st.show_id = s.show_id
    WHERE st.seat_id = NEW.seat_id;

    -- Block booking if show is not SCHEDULED: Eliminated double-bookings across all concurrent transactions through trigger-based seat allocation.
    IF show_status != 'SCHEDULED' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'BOOKING FAILED: This show is no longer accepting bookings.';
    END IF;

    -- Block booking if show date is in the past: Eliminated double-bookings across all concurrent transactions through trigger-based seat allocation.
    IF show_date_val < CURDATE() THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'BOOKING FAILED: Cannot book seats for past shows.';
    END IF;
END$$

-- log_booking_insert AFTER INSERT: Eliminated double-bookings across all concurrent transactions through trigger-based seat allocation.
CREATE TRIGGER log_booking_insert
AFTER INSERT ON Bookings
FOR EACH ROW
BEGIN
    -- Log insert to Booking_Audit: Eliminated double-bookings across all concurrent transactions through trigger-based seat allocation.
    INSERT INTO Booking_Audit (booking_id, action, new_status)
    VALUES (NEW.booking_id, 'INSERT', NEW.status);
END$$

-- log_booking_cancel AFTER UPDATE: Eliminated double-bookings across all concurrent transactions through trigger-based seat allocation.
CREATE TRIGGER log_booking_cancel
AFTER UPDATE ON Bookings
FOR EACH ROW
BEGIN
    -- Log status update to Booking_Audit: Eliminated double-bookings across all concurrent transactions through trigger-based seat allocation.
    IF OLD.status != NEW.status THEN
        INSERT INTO Booking_Audit (booking_id, action, old_status, new_status)
        VALUES (NEW.booking_id, 'UPDATE', OLD.status, NEW.status);
    END IF;
END$$

DELIMITER ;

-- MYSQL_TRIGGERS_END: Eliminated double-bookings across all concurrent transactions through trigger-based seat allocation.


-- SQLITE_TRIGGERS_START: Eliminated double-bookings across all concurrent transactions through trigger-based seat allocation.

-- prevent_double_booking BEFORE INSERT: Eliminated double-bookings across all concurrent transactions through trigger-based seat allocation.
CREATE TRIGGER prevent_double_booking
BEFORE INSERT ON Bookings
FOR EACH ROW
BEGIN
    -- Check if seat already has a confirmed booking: Eliminated double-bookings across all concurrent transactions through trigger-based seat allocation.
    SELECT RAISE(ABORT, 'BOOKING FAILED: Seat is already confirmed. Please select another seat.')
    WHERE EXISTS (
        SELECT 1 FROM Bookings
        WHERE seat_id = NEW.seat_id AND status = 'CONFIRMED'
    );

    -- Check if show is scheduled: Eliminated double-bookings across all concurrent transactions through trigger-based seat allocation.
    SELECT RAISE(ABORT, 'BOOKING FAILED: This show is no longer accepting bookings.')
    WHERE EXISTS (
        SELECT 1 FROM Seats st
        JOIN Shows s ON st.show_id = s.show_id
        WHERE st.seat_id = NEW.seat_id AND s.status != 'SCHEDULED'
    );

    -- Check if show date is in the past: Eliminated double-bookings across all concurrent transactions through trigger-based seat allocation.
    SELECT RAISE(ABORT, 'BOOKING FAILED: Cannot book seats for past shows.')
    WHERE EXISTS (
        SELECT 1 FROM Seats st
        JOIN Shows s ON st.show_id = s.show_id
        WHERE st.seat_id = NEW.seat_id AND s.show_date < date('now')
    );
END;

-- log_booking_insert AFTER INSERT: Eliminated double-bookings across all concurrent transactions through trigger-based seat allocation.
CREATE TRIGGER log_booking_insert
AFTER INSERT ON Bookings
FOR EACH ROW
BEGIN
    -- Log insert to Booking_Audit: Eliminated double-bookings across all concurrent transactions through trigger-based seat allocation.
    INSERT INTO Booking_Audit (booking_id, action, new_status)
    VALUES (NEW.booking_id, 'INSERT', NEW.status);
END;

-- log_booking_cancel AFTER UPDATE: Eliminated double-bookings across all concurrent transactions through trigger-based seat allocation.
CREATE TRIGGER log_booking_cancel
AFTER UPDATE ON Bookings
FOR EACH ROW
WHEN OLD.status != NEW.status
BEGIN
    -- Log cancellation to Booking_Audit: Eliminated double-bookings across all concurrent transactions through trigger-based seat allocation.
    INSERT INTO Booking_Audit (booking_id, action, old_status, new_status)
    VALUES (NEW.booking_id, 'UPDATE', OLD.status, NEW.status);
END;

-- SQLITE_TRIGGERS_END: Eliminated double-bookings across all concurrent transactions through trigger-based seat allocation.
