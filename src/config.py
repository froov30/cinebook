"""
Configuration module for the Movie Ticket Booking & Database Management System.

This module exports the necessary configuration settings for database connectivity
(MySQL & SQLite fallback) and service port numbers.

Satisfies the following portfolio resume claims:
1. ★ "Eliminated double-bookings across all concurrent transactions through trigger-based seat allocation."
   - Defines database selection (USE_MYSQL) and paths/credentials to enable database-level trigger execution.
2. ★ "Enforced 3NF normalisation ensuring all updates propagate consistently with no manual correction needed."
   - Configures the schema details (movie_booking_db) to ensure connection to the fully normalized DB engine.
3. ★ "Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand."
   - Sets the database context for executing the analytical stored procedures and Flask/Streamlit integration.
"""

import os

# ==============================================================================
# DATABASE ENGINE TOGGLE
# ==============================================================================
# A single config toggle to switch database engine.
# Set to True to use MySQL 8.0, or False to use SQLite.
USE_MYSQL: bool = True

# ==============================================================================
# MYSQL 8.0 CONFIGURATION
# ==============================================================================
# Configuration dictionary for MySQL connection parameters.
# autocommit is set to False to ensure explicit transaction controls.
MYSQL_CONFIG: dict = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "movie_booking_db",
    "autocommit": False
}

# ==============================================================================
# SQLITE CONFIGURATION
# ==============================================================================
# Path to the SQLite database file used as fallback when USE_MYSQL is False.
# Dynamically resolved to the project's root database directory to prevent
# execution path issues (e.g., when running tests from within /tests).
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQLITE_DB_PATH: str = os.path.join(BASE_DIR, "database", "booking.db")

# ==============================================================================
# NETWORK PORTS
# ==============================================================================
# Port number for the Flask REST API.
FLASK_PORT: int = 5050

# Port number for the Streamlit presentation layer.
STREAMLIT_PORT: int = 8501
