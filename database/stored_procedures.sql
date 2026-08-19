-- Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand.
-- Stored Procedures for movie_booking_db: Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand.

DELIMITER $$

-- Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand.
DROP PROCEDURE IF EXISTS get_show_occupancy$$

-- Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand.
CREATE PROCEDURE get_show_occupancy(IN in_show_id INT)
BEGIN
    -- Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand.
    SELECT 
        s.show_id,
        m.title AS movie_title,
        c.name AS cinema_name,
        s.show_date,
        s.show_time,
        s.total_seats,
        COUNT(b.booking_id) AS booked_seats,
        ROUND(IFNULL((COUNT(b.booking_id) / NULLIF(s.total_seats, 0)) * 100, 0), 2) AS occupancy_percentage
    FROM Shows s
    JOIN Movies m ON s.movie_id = m.movie_id
    JOIN Cinemas c ON s.cinema_id = c.cinema_id
    LEFT JOIN Seats st ON s.show_id = st.show_id
    LEFT JOIN Bookings b ON st.seat_id = b.seat_id AND b.status = 'CONFIRMED'
    WHERE s.show_id = in_show_id
    GROUP BY s.show_id, m.title, c.name, s.show_date, s.show_time, s.total_seats;
END$$

-- Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand.
DROP PROCEDURE IF EXISTS get_revenue_report$$

-- Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand.
CREATE PROCEDURE get_revenue_report(IN in_start_date DATE, IN in_end_date DATE)
BEGIN
    -- Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand.
    SELECT 
        DATE(b.booking_date) AS booking_date,
        COUNT(b.booking_id) AS total_bookings,
        SUM(b.amount) AS total_revenue
    FROM Bookings b
    WHERE b.status = 'CONFIRMED'
      AND DATE(b.booking_date) BETWEEN in_start_date AND in_end_date
    GROUP BY DATE(b.booking_date)
    ORDER BY booking_date ASC;
END$$

-- Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand.
DROP PROCEDURE IF EXISTS get_movie_show_summary$$

-- Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand.
CREATE PROCEDURE get_movie_show_summary(IN in_movie_id INT)
BEGIN
    -- Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand.
    SELECT 
        m.movie_id,
        m.title,
        (SELECT COUNT(*) FROM Shows WHERE movie_id = m.movie_id) AS total_shows,
        COUNT(b.booking_id) AS total_tickets_sold,
        COALESCE(SUM(b.amount), 0.00) AS total_revenue,
        ROUND(
            IFNULL(
                (COUNT(b.booking_id) / (SELECT NULLIF(SUM(total_seats), 0) FROM Shows WHERE movie_id = m.movie_id)) * 100,
                0
            ),
            2
        ) AS average_occupancy
    FROM Movies m
    LEFT JOIN Shows s ON m.movie_id = s.movie_id
    LEFT JOIN Seats st ON s.show_id = st.show_id
    LEFT JOIN Bookings b ON st.seat_id = b.seat_id AND b.status = 'CONFIRMED'
    WHERE m.movie_id = in_movie_id
    GROUP BY m.movie_id, m.title;
END$$

-- Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand.
DROP PROCEDURE IF EXISTS get_seat_type_revenue$$

-- Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand.
CREATE PROCEDURE get_seat_type_revenue()
BEGIN
    -- Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand.
    SELECT 
        st.seat_type,
        COUNT(b.booking_id) AS tickets_sold,
        COALESCE(SUM(b.amount), 0.00) AS total_revenue,
        ROUND(
            IFNULL(
                (COALESCE(SUM(b.amount), 0.00) / (SELECT NULLIF(SUM(amount), 0) FROM Bookings WHERE status = 'CONFIRMED')) * 100,
                0
            ),
            2
        ) AS revenue_percentage
    FROM Seats st
    JOIN Bookings b ON st.seat_id = b.seat_id
    WHERE b.status = 'CONFIRMED'
    GROUP BY st.seat_type
    ORDER BY total_revenue DESC;
END$$

-- Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand.
DROP PROCEDURE IF EXISTS get_customer_history$$

-- Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand.
CREATE PROCEDURE get_customer_history(IN in_customer_id INT)
BEGIN
    -- Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand.
    SELECT 
        b.booking_id,
        m.title AS movie_title,
        c.name AS cinema_name,
        s.show_date,
        s.show_time,
        st.seat_number,
        st.seat_type,
        b.booking_date,
        b.amount,
        b.status
    FROM Bookings b
    JOIN Seats st ON b.seat_id = st.seat_id
    JOIN Shows s ON st.show_id = s.show_id
    JOIN Movies m ON s.movie_id = m.movie_id
    JOIN Cinemas c ON s.cinema_id = c.cinema_id
    WHERE b.customer_id = in_customer_id
    ORDER BY b.booking_date DESC;
END$$

-- Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand.
DROP PROCEDURE IF EXISTS get_top_shows$$

-- Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand.
CREATE PROCEDURE get_top_shows(IN in_limit_val INT)
BEGIN
    -- Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand.
    SELECT 
        s.show_id,
        m.title AS movie_title,
        c.name AS cinema_name,
        s.show_date,
        s.show_time,
        s.total_seats,
        COUNT(b.booking_id) AS booked_seats,
        ROUND(IFNULL((COUNT(b.booking_id) / NULLIF(s.total_seats, 0)) * 100, 0), 2) AS occupancy_percentage
    FROM Shows s
    JOIN Movies m ON s.movie_id = m.movie_id
    JOIN Cinemas c ON s.cinema_id = c.cinema_id
    LEFT JOIN Seats st ON s.show_id = st.show_id
    LEFT JOIN Bookings b ON st.seat_id = b.seat_id AND b.status = 'CONFIRMED'
    GROUP BY s.show_id, m.title, c.name, s.show_date, s.show_time, s.total_seats
    ORDER BY occupancy_percentage DESC, booked_seats DESC
    LIMIT in_limit_val;
END$$

DELIMITER ;

-- Example calls: Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand.
-- CALL get_show_occupancy(1); -- Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand.
-- CALL get_revenue_report('2026-06-01', '2026-06-30'); -- Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand.
-- CALL get_movie_show_summary(1); -- Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand.
-- CALL get_seat_type_revenue(); -- Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand.
-- CALL get_customer_history(1); -- Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand.
-- CALL get_top_shows(5); -- Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand.
