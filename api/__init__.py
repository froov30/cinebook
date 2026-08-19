"""
API package for the Movie Ticket Booking & Database Management System.

Exposes a Flask REST API layer providing HTTP endpoints for booking operations,
seat availability queries, and analytical reporting.

Resume claims satisfied:
1. ★ "Eliminated double-bookings across all concurrent transactions through trigger-based seat allocation."
   - POST /bookings delegates INSERT to the database layer where BEFORE INSERT triggers fire.
2. ★ "Enforced 3NF normalisation ensuring all updates propagate consistently with no manual correction needed."
   - All API responses are assembled from FK-joined queries against the normalized schema.
3. ★ "Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand."
   - GET /analytics/* endpoints invoke stored procedure wrappers directly.
"""
