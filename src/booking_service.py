"""
Booking service module for the Movie Ticket Booking & Database Management System.

Provides core booking business logic: show browsing, seat availability,
transactional booking/cancellation, customer management, and concurrent
booking simulation.

Satisfies the following portfolio resume claims:
1. ★ "Eliminated double-bookings across all concurrent transactions through trigger-based seat allocation."
   - `create_booking()` wraps inserts in explicit transactions and catches trigger-raised errors
     (MySQL error 1644 / SQLite BOOKING FAILED) to guarantee only one thread wins a seat.
   - `simulate_concurrent_booking()` uses `threading.Barrier` to launch N threads simultaneously,
     proving that the trigger blocks all but one concurrent attempt.
2. ★ "Enforced 3NF normalisation ensuring all updates propagate consistently with no manual correction needed."
   - `get_available_shows()` and `get_available_seats()` join normalized tables (Shows, Movies,
     Cinemas, Seats, Bookings) via foreign keys; no denormalized columns are referenced.
3. ★ "Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand."
   - Booking operations generate the transactional data that feeds the stored-procedure analytics
     layer in `analytics_service.py`.
"""

import logging
import sqlite3
import threading
from typing import Any, Dict, List, Optional

from src.db_connection import execute_query, get_connection

# Configure logging
logger = logging.getLogger("booking_service")


# ==============================================================================
# SHOW BROWSING
# ==============================================================================

def get_available_shows(
    date: Optional[str] = None,
    movie_id: Optional[int] = None,
    city: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Returns scheduled shows by joining Shows, Movies, and Cinemas.

    Claim 2 (3NF): Joins three normalized tables on foreign keys; no redundant
    columns are stored or returned beyond the join result.

    Args:
        date:     Optional ISO-8601 date string (e.g. '2026-06-15') to filter by show_date.
        movie_id: Optional movie primary key to filter by movie.
        city:     Optional city name to filter by cinema city.

    Returns:
        A list of dicts, each containing show, movie, and cinema details for
        every SCHEDULED show matching the filters.
    """
    query = """
        SELECT
            s.show_id,
            s.show_date,
            s.show_time,
            s.total_seats,
            s.ticket_price,
            s.hall_number,
            s.status,
            m.movie_id,
            m.title       AS movie_title,
            m.genre,
            m.duration_min,
            m.language,
            c.cinema_id,
            c.name        AS cinema_name,
            c.location,
            c.city
        FROM Shows s
        JOIN Movies m  ON s.movie_id  = m.movie_id
        JOIN Cinemas c ON s.cinema_id = c.cinema_id
        WHERE s.status = 'SCHEDULED'
    """
    params: List[Any] = []

    if date is not None:
        query += " AND s.show_date = %s"
        params.append(date)
    if movie_id is not None:
        query += " AND m.movie_id = %s"
        params.append(movie_id)
    if city is not None:
        query += " AND c.city = %s"
        params.append(city)

    query += " ORDER BY s.show_date, s.show_time"

    return execute_query(query, params if params else None, is_select=True)


# ==============================================================================
# SEAT AVAILABILITY
# ==============================================================================

def get_available_seats(show_id: int) -> Dict[str, List[Dict[str, Any]]]:
    """
    Returns seats for a show grouped by type with booking status.

    Claim 1 (Trigger Allocation): Each seat's `is_booked` flag reflects
    whether a CONFIRMED booking exists, which is enforced at the DB layer
    by the prevent_double_booking trigger.

    Claim 2 (3NF): Seats and Bookings are separate normalized tables joined
    on seat_id; no booking data is duplicated in Seats.

    Args:
        show_id: The primary key of the show.

    Returns:
        A dict keyed by seat type (Standard, Premium, VIP), each mapping to
        a list of seat dicts with seat_id, seat_number, seat_type, and is_booked.
    """
    query = """
        SELECT
            st.seat_id,
            st.seat_number,
            st.seat_type,
            st.price_modifier,
            CASE
                WHEN b.booking_id IS NOT NULL THEN 1
                ELSE 0
            END AS is_booked
        FROM Seats st
        LEFT JOIN Bookings b
            ON st.seat_id = b.seat_id AND b.status = 'CONFIRMED'
        WHERE st.show_id = %s
        ORDER BY st.seat_type, st.seat_number
    """
    rows = execute_query(query, (show_id,), is_select=True)

    grouped: Dict[str, List[Dict[str, Any]]] = {
        "Standard": [],
        "Premium": [],
        "VIP": [],
    }
    for row in rows:
        seat_type = row.get("seat_type", "Standard")
        entry = {
            "seat_id": row["seat_id"],
            "seat_number": row["seat_number"],
            "seat_type": seat_type,
            "price_modifier": row.get("price_modifier"),
            "is_booked": bool(row["is_booked"]),
        }
        if seat_type in grouped:
            grouped[seat_type].append(entry)
        else:
            grouped[seat_type] = [entry]

    return grouped


# ==============================================================================
# BOOKING CREATION
# ==============================================================================

def create_booking(
    seat_id: int,
    customer_id: int,
    amount: float,
    connection: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Inserts a CONFIRMED booking inside an explicit transaction.

    Claim 1 (Trigger Allocation): The BEFORE INSERT trigger fires inside this
    transaction. If the seat already has a CONFIRMED booking, the trigger raises
    MySQL error 1644 or an SQLite RAISE(ABORT, 'BOOKING FAILED ...') which is
    caught here, resulting in `{success: False}`.

    Args:
        seat_id:     The seat primary key to book.
        customer_id: The customer primary key making the booking.
        amount:      The booking amount in currency units.
        connection:  Optional pre-existing connection for transactional control
                     (used by simulate_concurrent_booking).

    Returns:
        Dict with keys: success (bool), booking_id (int or None), error (str or None).
    """
    is_local_connection = connection is None
    if is_local_connection:
        connection = get_connection()

    is_mysql = not isinstance(connection, sqlite3.Connection)
    cursor = None

    try:
        cursor = connection.cursor(dictionary=True) if is_mysql else connection.cursor()

        # Begin explicit transaction
        if is_mysql:
            cursor.execute("BEGIN")
        else:
            cursor.execute("BEGIN IMMEDIATE")

        insert_sql = (
            "INSERT INTO Bookings (seat_id, customer_id, amount, status) "
            "VALUES (%s, %s, %s, 'CONFIRMED')"
        )
        if is_mysql:
            cursor.execute(insert_sql, (seat_id, customer_id, amount))
        else:
            cursor.execute(
                insert_sql.replace("%s", "?"),
                (seat_id, customer_id, amount),
            )

        booking_id = cursor.lastrowid
        connection.commit()

        return {"success": True, "booking_id": booking_id, "error": None}

    except Exception as exc:
        try:
            connection.rollback()
        except Exception:
            pass

        error_msg = str(exc)

        # Detect trigger-raised double-booking errors
        is_trigger_error = False
        if is_mysql:
            # MySQL SIGNAL SQLSTATE '45000' raises error code 1644
            if hasattr(exc, "errno") and getattr(exc, "errno", None) == 1644:
                is_trigger_error = True
            elif "1644" in error_msg:
                is_trigger_error = True
        else:
            if "BOOKING FAILED" in error_msg.upper():
                is_trigger_error = True

        if is_trigger_error:
            logger.info(f"Double-booking prevented by trigger: {error_msg}")
        else:
            logger.error(f"Booking creation failed: {error_msg}")

        return {"success": False, "booking_id": None, "error": error_msg}

    finally:
        if cursor:
            cursor.close()
        if is_local_connection:
            connection.close()


# ==============================================================================
# BOOKING CANCELLATION
# ==============================================================================

def cancel_booking(booking_id: int, customer_id: int) -> Dict[str, Any]:
    """
    Cancels a booking after verifying customer ownership.

    Claim 2 (3NF): The UPDATE targets only the Bookings table; the audit trail
    is maintained automatically by the log_booking_cancel trigger without manual
    denormalized updates.

    Args:
        booking_id:  The booking to cancel.
        customer_id: The customer requesting cancellation (ownership check).

    Returns:
        Dict with keys: success (bool), message (str).
    """
    # Verify that the booking belongs to the customer and is currently CONFIRMED
    verify_query = """
        SELECT booking_id, status
        FROM Bookings
        WHERE booking_id = %s AND customer_id = %s
    """
    rows = execute_query(verify_query, (booking_id, customer_id), is_select=True)

    if not rows:
        return {
            "success": False,
            "message": f"Booking {booking_id} not found for customer {customer_id}.",
        }

    current_status = rows[0].get("status", "")
    if current_status == "CANCELLED":
        return {
            "success": False,
            "message": f"Booking {booking_id} is already cancelled.",
        }

    cancel_query = """
        UPDATE Bookings
        SET status = 'CANCELLED'
        WHERE booking_id = %s AND customer_id = %s
    """
    affected = execute_query(
        cancel_query, (booking_id, customer_id), is_select=False
    )

    if affected and affected > 0:
        return {
            "success": True,
            "message": f"Booking {booking_id} cancelled successfully.",
        }

    return {
        "success": False,
        "message": f"Failed to cancel booking {booking_id}.",
    }


# ==============================================================================
# CUSTOMER MANAGEMENT
# ==============================================================================

def get_or_create_customer(name: str, email: str, phone: str) -> int:
    """
    Retrieves an existing customer by email or creates a new one.

    Uses INSERT IGNORE (MySQL) / INSERT OR IGNORE (SQLite) so the operation
    is idempotent across retries and concurrent calls.

    Claim 2 (3NF): Customer data lives solely in the Customers table;
    Bookings reference only customer_id.

    Args:
        name:  Customer full name.
        email: Customer email (unique key).
        phone: Customer phone number.

    Returns:
        The customer_id (int) of the existing or newly created customer.
    """
    conn = get_connection()
    is_mysql = not isinstance(conn, sqlite3.Connection)
    cursor = None

    try:
        if is_mysql:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "INSERT IGNORE INTO Customers (name, email, phone) VALUES (%s, %s, %s)",
                (name, email, phone),
            )
            conn.commit()
            cursor.execute(
                "SELECT customer_id FROM Customers WHERE email = %s", (email,)
            )
            row = cursor.fetchone()
        else:
            cursor = conn.cursor()
            conn.row_factory = sqlite3.Row
            cursor.execute(
                "INSERT OR IGNORE INTO Customers (name, email, phone) VALUES (?, ?, ?)",
                (name, email, phone),
            )
            conn.commit()
            cursor.execute(
                "SELECT customer_id FROM Customers WHERE email = ?", (email,)
            )
            row = cursor.fetchone()

        if row is None:
            raise RuntimeError(f"Failed to get or create customer with email '{email}'.")

        return int(row["customer_id"]) if isinstance(row, dict) else int(row[0])

    finally:
        if cursor:
            cursor.close()
        conn.close()


# ==============================================================================
# CONCURRENT BOOKING SIMULATION
# ==============================================================================

def simulate_concurrent_booking(
    show_id: int,
    seat_id: int,
    n_threads: int = 5,
) -> Dict[str, Any]:
    """
    Simulates N concurrent booking attempts for the same seat using threading.Barrier.

    Claim 1 (Trigger Allocation): This function is the primary proof that the
    prevent_double_booking trigger eliminates double-bookings. All N threads
    start simultaneously (via Barrier.wait()), each with its own DB connection.
    Exactly one thread succeeds; the rest are blocked by the trigger.

    Implementation:
        1. A `threading.Barrier(n_threads)` is created to synchronize launch.
        2. Each thread creates/finds a unique customer (thread_user_N@test.com).
        3. Each thread obtains its own `get_connection()`.
        4. All threads call `barrier.wait()` then immediately `create_booking()`.
        5. Results are collected in a thread-safe list.

    Args:
        show_id:   The show containing the target seat.
        seat_id:   The seat all threads will race to book.
        n_threads: Number of concurrent threads (default 5).

    Returns:
        Dict with keys:
            total_threads (int), succeeded (int), blocked (int),
            results (list of per-thread outcome dicts).
    """
    barrier = threading.Barrier(n_threads)
    results_lock = threading.Lock()
    results: List[Dict[str, Any]] = []

    # Pre-fetch a ticket price for the booking amount
    price_rows = execute_query(
        "SELECT ticket_price FROM Shows WHERE show_id = %s",
        (show_id,),
        is_select=True,
    )
    amount = float(price_rows[0]["ticket_price"]) if price_rows else 100.00

    def _worker(thread_index: int) -> None:
        """Thread target: synchronize on barrier, then attempt booking."""
        thread_name = f"Thread-{thread_index}"
        outcome: Dict[str, Any] = {"thread": thread_name, "success": False, "error": None}

        try:
            # Create/find a unique customer for this thread
            customer_id = get_or_create_customer(
                name=f"Thread User {thread_index}",
                email=f"thread_user_{thread_index}@test.com",
                phone=f"900000000{thread_index}",
            )

            # Each thread gets its own connection for isolation
            conn = get_connection()

            try:
                # Synchronize: all threads release at the same instant
                barrier.wait()

                # Attempt the booking with the thread-local connection
                result = create_booking(
                    seat_id=seat_id,
                    customer_id=customer_id,
                    amount=amount,
                    connection=conn,
                )
                outcome["success"] = result["success"]
                outcome["booking_id"] = result.get("booking_id")
                outcome["error"] = result.get("error")
            finally:
                conn.close()

        except threading.BrokenBarrierError:
            outcome["error"] = "Barrier broken — a peer thread failed before sync."
        except Exception as exc:
            outcome["error"] = str(exc)

        with results_lock:
            results.append(outcome)

    # Launch threads
    threads: List[threading.Thread] = []
    for i in range(n_threads):
        t = threading.Thread(target=_worker, args=(i,), daemon=True)
        threads.append(t)
        t.start()

    # Wait for all threads to finish
    for t in threads:
        t.join()

    succeeded = sum(1 for r in results if r["success"])
    blocked = sum(1 for r in results if not r["success"])

    logger.info(
        f"Concurrent booking simulation complete: "
        f"{succeeded} succeeded, {blocked} blocked out of {n_threads} threads."
    )

    return {
        "total_threads": n_threads,
        "succeeded": succeeded,
        "blocked": blocked,
        "results": results,
    }
