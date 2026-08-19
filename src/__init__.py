"""
Movie Ticket Booking & Database Management System.

This package provides the core business logic, database connectivity, and data models
for the Movie Ticket Booking system.

This module satisfies the following portfolio resume claims:
1. ★ "Eliminated double-bookings across all concurrent transactions through trigger-based seat allocation."
   - The package exposes tools and services that interface with database-level triggers
     (using BEFORE INSERT checks in MySQL/SQLite) to prevent double-booking.
2. ★ "Enforced 3NF normalisation ensuring all updates propagate consistently with no manual correction needed."
   - The package models represent a highly normalized database schema where data updates
     propagate cleanly through foreign key joins, preventing redundancy and anomaly.
3. ★ "Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand."
   - The package exposes functions that call native database stored procedures (with Python
     fallback scripts for SQLite) to fetch pre-defined analytics reports.
"""

__version__ = "1.0.0"
__all__ = []
