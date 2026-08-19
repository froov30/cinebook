"""
Flask REST API for the Movie Ticket Booking & Database Management System.

Provides a complete set of HTTP endpoints for movie show discovery, seat availability,
ticket booking (with trigger-based double-booking prevention), booking management,
and analytical reporting via stored procedures.

Resume claims satisfied:
1. ★ "Eliminated double-bookings across all concurrent transactions through trigger-based seat allocation."
   - POST /bookings performs an INSERT that fires the prevent_double_booking BEFORE INSERT trigger.
2. ★ "Enforced 3NF normalisation ensuring all updates propagate consistently with no manual correction needed."
   - All responses join normalized tables via foreign keys; no denormalized data is returned.
3. ★ "Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand."
   - GET /analytics/* endpoints call stored procedures (or SQLite emulations) directly.

Sample curl commands:
# Health check
#   curl http://localhost:5050/health

# List available shows (optional filters: date, city, movie_id)
#   curl "http://localhost:5050/shows?date=2026-06-15&city=Mumbai"

# Get available seats for a show
#   curl http://localhost:5050/shows/1/seats

# Create a booking (trigger fires on INSERT)
#   curl -X POST http://localhost:5050/bookings \
#        -H "Content-Type: application/json" \
#        -d '{"seat_id":1,"customer_name":"Alice","email":"alice@example.com","phone":"9876543210","amount":250.00}'

# Get booking details
#   curl http://localhost:5050/bookings/1

# Cancel a booking
#   curl -X PUT http://localhost:5050/bookings/1/cancel \
#        -H "Content-Type: application/json" \
#        -d '{"customer_id":1}'

# Show occupancy analytics
#   curl http://localhost:5050/analytics/occupancy/1

# Revenue report for a date range
#   curl "http://localhost:5050/analytics/revenue?start=2026-01-01&end=2026-12-31"

# Top shows by occupancy
#   curl "http://localhost:5050/analytics/top-shows?limit=5"

# Seat-type revenue breakdown
#   curl http://localhost:5050/analytics/seat-types
"""

import sys
import os
import logging

# Ensure project root is importable regardless of where the script is run from
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, request
from flask_cors import CORS

from src.config import FLASK_PORT, USE_MYSQL
from src.db_connection import execute_query
from src.booking_service import (
    get_available_shows,
    get_available_seats,
    create_booking,
    cancel_booking,
    get_or_create_customer,
)
from src.analytics_service import (
    get_show_occupancy,
    get_revenue_report,
    get_top_shows,
    get_seat_type_revenue,
)

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("flask_api")

app = Flask(__name__)
CORS(app)


# ===========================================================================
# Helper: consistent JSON envelope
# ===========================================================================

def _success(data):
    """Return a success envelope: {success: true, data: ..., error: null}."""
    return jsonify({"success": True, "data": data, "error": None})


def _error(message, status_code=400):
    """Return an error envelope: {success: false, data: null, error: ...}."""
    return jsonify({"success": False, "data": None, "error": str(message)}), status_code


# ===========================================================================
# Endpoints — Show discovery
# ===========================================================================

@app.route("/shows", methods=["GET"])
def list_shows():
    """
    GET /shows — list available shows with optional query-parameter filters.

    Query params (all optional):
        date     — filter by show date (ISO format, e.g. 2026-06-15)
        city     — filter by cinema city
        movie_id — filter by movie ID

    ★ "Enforced 3NF normalisation ensuring all updates propagate consistently
       with no manual correction needed." — response is assembled from FK joins.
    """
    try:
        filters = {}
        if request.args.get("date"):
            filters["date"] = request.args["date"]
        if request.args.get("city"):
            filters["city"] = request.args["city"]
        if request.args.get("movie_id"):
            filters["movie_id"] = int(request.args["movie_id"])
        shows = get_available_shows(**filters) if filters else get_available_shows()
        return _success(shows)
    except Exception as exc:
        logger.exception("Error listing shows")
        return _error(str(exc), 500)


@app.route("/shows/<int:show_id>/seats", methods=["GET"])
def list_seats(show_id):
    """
    GET /shows/<show_id>/seats — list available (un-booked) seats for a show.

    ★ "Enforced 3NF normalisation ensuring all updates propagate consistently
       with no manual correction needed." — seat data lives in its own table.
    """
    try:
        seats = get_available_seats(show_id)
        return _success(seats)
    except Exception as exc:
        logger.exception("Error listing seats")
        return _error(str(exc), 500)


# ===========================================================================
# Endpoints — Booking management
# ===========================================================================

@app.route("/bookings", methods=["POST"])
def make_booking():
    """
    POST /bookings — create a new ticket booking.

    JSON body:
        seat_id       (int)    — required
        customer_name (str)    — required
        email         (str)    — required
        phone         (str)    — optional
        amount        (float)  — required

    The INSERT fires the prevent_double_booking BEFORE INSERT trigger.

    ★ "Eliminated double-bookings across all concurrent transactions through
       trigger-based seat allocation." — the trigger fires during this INSERT.
    """
    try:
        body = request.get_json(force=True)
        required = ("seat_id", "customer_name", "email", "amount")
        missing = [f for f in required if f not in body]
        if missing:
            return _error(f"Missing required fields: {', '.join(missing)}")

        customer = get_or_create_customer(
            name=body["customer_name"],
            email=body["email"],
            phone=body.get("phone"),
        )
        customer_id = customer["customer_id"] if isinstance(customer, dict) else customer

        result = create_booking(
            seat_id=int(body["seat_id"]),
            customer_id=int(customer_id),
            amount=float(body["amount"]),
        )
        return _success(result), 201
    except Exception as exc:
        msg = str(exc)
        logger.exception("Booking creation failed")
        if "already" in msg.lower() or "booking failed" in msg.lower():
            return _error(msg, 409)
        return _error(msg, 500)


@app.route("/bookings/<int:booking_id>", methods=["GET"])
def get_booking(booking_id):
    """
    GET /bookings/<booking_id> — retrieve booking details from the database.

    ★ "Enforced 3NF normalisation ensuring all updates propagate consistently
       with no manual correction needed." — booking row references seat_id and
       customer_id via FKs; display names are joined at query time.
    """
    try:
        query = """
            SELECT b.booking_id, b.seat_id, b.customer_id, b.booking_date,
                   b.amount, b.status, b.payment_ref,
                   st.seat_number, st.seat_type,
                   cu.name AS customer_name, cu.email,
                   m.title AS movie_title, s.show_date, s.show_time,
                   c.name AS cinema_name
            FROM Bookings b
            JOIN Seats st ON b.seat_id = st.seat_id
            JOIN Customers cu ON b.customer_id = cu.customer_id
            JOIN Shows s ON st.show_id = s.show_id
            JOIN Movies m ON s.movie_id = m.movie_id
            JOIN Cinemas c ON s.cinema_id = c.cinema_id
            WHERE b.booking_id = %s
        """
        rows = execute_query(query, (booking_id,), is_select=True)
        if not rows:
            return _error("Booking not found", 404)

        row = rows[0]
        # Normalize types for JSON serialization
        for key, val in row.items():
            if hasattr(val, "isoformat"):
                row[key] = val.isoformat()
            elif hasattr(val, "__float__"):
                row[key] = float(val)
        return _success(row)
    except Exception as exc:
        logger.exception("Error fetching booking")
        return _error(str(exc), 500)


@app.route("/bookings/<int:booking_id>/cancel", methods=["PUT"])
def cancel(booking_id):
    """
    PUT /bookings/<booking_id>/cancel — cancel an existing booking.

    JSON body:
        customer_id (int) — required for ownership verification

    ★ "Eliminated double-bookings across all concurrent transactions through
       trigger-based seat allocation." — cancellation updates seat status so the
       trigger will allow a new booking for the freed seat.
    """
    try:
        body = request.get_json(force=True)
        if "customer_id" not in body:
            return _error("Missing required field: customer_id")
        result = cancel_booking(booking_id, int(body["customer_id"]))
        return _success(result)
    except Exception as exc:
        logger.exception("Cancellation failed")
        return _error(str(exc), 500)


# ===========================================================================
# Endpoints — Analytics (stored procedures)
# ===========================================================================

@app.route("/analytics/occupancy/<int:show_id>", methods=["GET"])
def occupancy(show_id):
    """
    GET /analytics/occupancy/<show_id> — show occupancy report.

    ★ "Replaced ad-hoc reporting with stored procedures delivering occupancy
       and revenue analytics on demand."
    """
    try:
        data = get_show_occupancy(show_id)
        return _success(data)
    except Exception as exc:
        logger.exception("Occupancy report failed")
        return _error(str(exc), 500)


@app.route("/analytics/revenue", methods=["GET"])
def revenue():
    """
    GET /analytics/revenue — revenue report for a date range.

    Query params:
        start — start date (ISO format)
        end   — end date   (ISO format)

    ★ "Replaced ad-hoc reporting with stored procedures delivering occupancy
       and revenue analytics on demand."
    """
    try:
        start = request.args.get("start")
        end = request.args.get("end")
        if not start or not end:
            return _error("Missing required query params: start, end")
        data = get_revenue_report(start, end)
        return _success(data)
    except Exception as exc:
        logger.exception("Revenue report failed")
        return _error(str(exc), 500)


@app.route("/analytics/top-shows", methods=["GET"])
def top_shows():
    """
    GET /analytics/top-shows — top shows by occupancy.

    Query params:
        limit — maximum number of shows to return (default 10)

    ★ "Replaced ad-hoc reporting with stored procedures delivering occupancy
       and revenue analytics on demand."
    """
    try:
        limit = int(request.args.get("limit", 10))
        data = get_top_shows(limit)
        return _success(data)
    except Exception as exc:
        logger.exception("Top-shows report failed")
        return _error(str(exc), 500)


@app.route("/analytics/seat-types", methods=["GET"])
def seat_types():
    """
    GET /analytics/seat-types — revenue breakdown by seat type.

    ★ "Replaced ad-hoc reporting with stored procedures delivering occupancy
       and revenue analytics on demand."
    """
    try:
        data = get_seat_type_revenue()
        return _success(data)
    except Exception as exc:
        logger.exception("Seat-type revenue report failed")
        return _error(str(exc), 500)


# ===========================================================================
# Endpoint — Health check
# ===========================================================================

@app.route("/health", methods=["GET"])
def health():
    """
    GET /health — lightweight health check.

    Returns the running database engine so deployment scripts can verify
    which backend is active.
    """
    db_engine = "MySQL" if USE_MYSQL else "SQLite"
    return _success({"status": "ok", "db": db_engine})


# ===========================================================================
# Entry point
# ===========================================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=False)
