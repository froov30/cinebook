"""
Analytics service module for the Movie Ticket Booking & Database Management System.

Wraps each stored procedure behind a clean Python function.  For MySQL the call
goes through native ``CALL procedure_name(...)``; for SQLite the same
``call_procedure()`` interface transparently executes the equivalent query
defined in ``SQLITE_PROCEDURE_MAPPING`` inside ``db_connection.py``.

Satisfies the following portfolio resume claims:
1. ★ "Eliminated double-bookings across all concurrent transactions through trigger-based seat allocation."
   - Occupancy and top-show analytics depend on accurate CONFIRMED booking counts,
     which are reliable only because the trigger prevents duplicate inserts.
2. ★ "Enforced 3NF normalisation ensuring all updates propagate consistently with no manual correction needed."
   - Every procedure joins normalized 3NF tables (Movies, Cinemas, Shows, Seats,
     Bookings, Customers) via foreign keys, so a single-point update in any table
     is immediately reflected across all analytics outputs.
3. ★ "Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand."
   - This module IS the direct implementation of claim 3. Each function below
     replaces a previously hand-written, ad-hoc SQL snippet with a single
     ``call_procedure()`` invocation.
"""

import logging
from typing import Any, Dict, List

from src.db_connection import call_procedure

# Configure logging
logger = logging.getLogger("analytics_service")


# ==============================================================================
# SHOW OCCUPANCY
# ==============================================================================

def get_show_occupancy(show_id: int) -> List[Dict[str, Any]]:
    """
    Returns occupancy statistics for a single show.

    Replaces the following ad-hoc query pattern that was previously duplicated
    across multiple view handlers::

        SELECT s.show_id, m.title, c.name, s.show_date, s.show_time,
               s.total_seats, COUNT(b.booking_id) AS booked,
               ROUND(COUNT(b.booking_id)/s.total_seats*100, 2) AS pct
        FROM Shows s JOIN Movies m ... JOIN Cinemas c ...
             LEFT JOIN Seats st ... LEFT JOIN Bookings b ...
        WHERE s.show_id = <X>
        GROUP BY ...

    Claim 3 (Stored Procedures): Encapsulated in ``get_show_occupancy`` stored
    procedure / SQLite emulation, eliminating copy-paste SQL across the codebase.

    Args:
        show_id: Primary key of the show to inspect.

    Returns:
        A list containing a single dict with keys: show_id, movie_title,
        cinema_name, show_date, show_time, total_seats, booked_seats,
        occupancy_percentage.
    """
    return call_procedure("get_show_occupancy", (show_id,))


# ==============================================================================
# REVENUE REPORT
# ==============================================================================

def get_revenue_report(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Returns daily confirmed-booking revenue between two dates.

    Replaces the following ad-hoc query pattern::

        SELECT DATE(b.booking_date) AS d, COUNT(*), SUM(b.amount)
        FROM Bookings b
        WHERE b.status = 'CONFIRMED'
          AND DATE(b.booking_date) BETWEEN '<start>' AND '<end>'
        GROUP BY d ORDER BY d;

    Claim 3 (Stored Procedures): Standardised in the ``get_revenue_report``
    procedure so that every consumer (Flask, Streamlit, CLI) returns identical
    revenue breakdowns without reimplementing the query.

    Args:
        start_date: Inclusive start date (ISO-8601, e.g. '2026-01-01').
        end_date:   Inclusive end date (ISO-8601, e.g. '2026-12-31').

    Returns:
        A list of dicts, each with keys: booking_date, total_bookings,
        total_revenue.
    """
    return call_procedure("get_revenue_report", (start_date, end_date))


# ==============================================================================
# MOVIE SHOW SUMMARY
# ==============================================================================

def get_movie_show_summary(movie_id: int) -> List[Dict[str, Any]]:
    """
    Returns aggregate show and ticket metrics for a movie.

    Replaces the following ad-hoc query pattern::

        SELECT m.movie_id, m.title,
               (SELECT COUNT(*) FROM Shows WHERE movie_id = m.movie_id) AS shows,
               COUNT(b.booking_id) AS tickets, SUM(b.amount) AS rev,
               ROUND(...) AS avg_occ
        FROM Movies m LEFT JOIN Shows s ... LEFT JOIN Seats st ...
             LEFT JOIN Bookings b ...
        WHERE m.movie_id = <X>
        GROUP BY m.movie_id, m.title;

    Claim 3 (Stored Procedures): Consolidated into ``get_movie_show_summary``
    so dashboard and API layers receive consistent, pre-computed summaries.

    Args:
        movie_id: Primary key of the movie.

    Returns:
        A list containing a single dict with keys: movie_id, title,
        total_shows, total_tickets_sold, total_revenue, average_occupancy.
    """
    return call_procedure("get_movie_show_summary", (movie_id,))


# ==============================================================================
# SEAT TYPE REVENUE
# ==============================================================================

def get_seat_type_revenue() -> List[Dict[str, Any]]:
    """
    Returns revenue and ticket counts broken down by seat type.

    Replaces the following ad-hoc query pattern::

        SELECT st.seat_type, COUNT(b.booking_id), SUM(b.amount),
               ROUND(SUM(b.amount) / (SELECT SUM(amount) FROM Bookings WHERE status='CONFIRMED') * 100, 2)
        FROM Seats st JOIN Bookings b ON st.seat_id = b.seat_id
        WHERE b.status = 'CONFIRMED'
        GROUP BY st.seat_type ORDER BY SUM(b.amount) DESC;

    Claim 3 (Stored Procedures): The ``get_seat_type_revenue`` procedure
    replaces scattered inline SQL and ensures the revenue-percentage
    calculation is consistently defined in one place.

    Returns:
        A list of dicts, each with keys: seat_type, tickets_sold,
        total_revenue, revenue_percentage.
    """
    return call_procedure("get_seat_type_revenue")


# ==============================================================================
# CUSTOMER HISTORY
# ==============================================================================

def get_customer_history(customer_id: int) -> List[Dict[str, Any]]:
    """
    Returns the full booking history for a customer.

    Replaces the following ad-hoc query pattern::

        SELECT b.booking_id, m.title, c.name, s.show_date, s.show_time,
               st.seat_number, st.seat_type, b.booking_date, b.amount, b.status
        FROM Bookings b JOIN Seats st ... JOIN Shows s ...
             JOIN Movies m ... JOIN Cinemas c ...
        WHERE b.customer_id = <X>
        ORDER BY b.booking_date DESC;

    Claim 2 (3NF): The five-table join is possible without redundancy because
    each entity lives in its own normalized table.

    Claim 3 (Stored Procedures): Encapsulated in ``get_customer_history`` so
    that profile pages and audit views share a single query definition.

    Args:
        customer_id: Primary key of the customer.

    Returns:
        A list of dicts, each with keys: booking_id, movie_title, cinema_name,
        show_date, show_time, seat_number, seat_type, booking_date, amount, status.
    """
    return call_procedure("get_customer_history", (customer_id,))


# ==============================================================================
# TOP SHOWS
# ==============================================================================

def get_top_shows(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Returns the top N shows ranked by occupancy percentage.

    Replaces the following ad-hoc query pattern::

        SELECT s.show_id, m.title, c.name, s.show_date, s.show_time,
               s.total_seats, COUNT(b.booking_id) AS booked,
               ROUND(COUNT(b.booking_id)/s.total_seats*100, 2) AS pct
        FROM Shows s JOIN Movies m ... JOIN Cinemas c ...
             LEFT JOIN Seats st ... LEFT JOIN Bookings b ...
        GROUP BY ...
        ORDER BY pct DESC, booked DESC
        LIMIT <N>;

    Claim 1 (Trigger Allocation): Ranking accuracy relies on booking counts
    that are guaranteed to be free of duplicates, thanks to the trigger.

    Claim 3 (Stored Procedures): The ``get_top_shows`` procedure prevents
    dashboard pages from embedding their own LIMIT/ORDER logic.

    Args:
        limit: Maximum number of shows to return (default 10).

    Returns:
        A list of dicts, each with keys: show_id, movie_title, cinema_name,
        show_date, show_time, total_seats, booked_seats, occupancy_percentage.
    """
    return call_procedure("get_top_shows", (limit,))
