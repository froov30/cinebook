"""
Seed data script for the Movie Ticket Booking & Database Management System.

Reads and executes the SQL seed files in sequence to initialise the database
schema, register triggers, and populate sample data.

Satisfies the following portfolio resume claims:
1. ★ "Eliminated double-bookings across all concurrent transactions through trigger-based seat allocation."
   - Step 2 loads ``triggers.sql`` which registers the ``prevent_double_booking``
     BEFORE INSERT trigger, the foundation of the concurrency-safety guarantee.
2. ★ "Enforced 3NF normalisation ensuring all updates propagate consistently with no manual correction needed."
   - Step 1 loads ``schema.sql`` which defines all tables in strict 3NF with
     foreign-key constraints, ensuring structural normalisation from first boot.
3. ★ "Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand."
   - The sample data inserted in step 3 provides a realistic dataset for the
     stored-procedure analytics layer to query immediately after seeding.
"""

import os
import sys
import logging

from src.db_connection import execute_script

# Configure logging
logger = logging.getLogger("seed_data")

# Resolve project root (one level above src/)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ordered list of SQL scripts to execute
_SEED_SCRIPTS = [
    {
        "step": 1,
        "label": "Database Schema (tables, constraints, indexes)",
        "path": os.path.join(_PROJECT_ROOT, "database", "schema.sql"),
    },
    {
        "step": 2,
        "label": "Triggers (prevent_double_booking, audit logging)",
        "path": os.path.join(_PROJECT_ROOT, "database", "triggers.sql"),
    },
    {
        "step": 3,
        "label": "Sample Data (movies, cinemas, shows, seats, customers, bookings)",
        "path": os.path.join(_PROJECT_ROOT, "database", "sample_data.sql"),
    },
]


def seed_database() -> bool:
    """
    Executes all SQL seed scripts in order, printing step-level progress.

    Claim 1 (Trigger Allocation): Ensures triggers are loaded before any
    sample bookings are inserted so double-booking protection is active
    from the very first INSERT.

    Claim 2 (3NF): Loads the normalized schema first, guaranteeing FK
    constraints are in place before dependent data arrives.

    Returns:
        True if all steps completed successfully, False otherwise.
    """
    total_steps = len(_SEED_SCRIPTS)
    print(f"\n{'='*60}")
    print(f"  Movie Ticket Booking — Database Seeding")
    print(f"  {total_steps} steps to execute")
    print(f"{'='*60}\n")

    for script_info in _SEED_SCRIPTS:
        step = script_info["step"]
        label = script_info["label"]
        filepath = script_info["path"]

        print(f"[STEP {step}/{total_steps}] {label}")
        print(f"  File: {filepath}")

        if not os.path.isfile(filepath):
            print(f"  ✗ ERROR: File not found — {filepath}")
            logger.error(f"Seed file not found: {filepath}")
            return False

        try:
            execute_script(filepath)
            print(f"  ✓ Completed successfully.\n")
            logger.info(f"[STEP {step}/{total_steps}] {label} — success")
        except Exception as exc:
            print(f"  ✗ FAILED: {exc}\n")
            logger.error(
                f"[STEP {step}/{total_steps}] {label} — failed: {exc}"
            )
            return False

    print(f"{'='*60}")
    print(f"  All {total_steps} steps completed. Database is ready.")
    print(f"{'='*60}\n")
    return True


if __name__ == "__main__":
    success = seed_database()
    sys.exit(0 if success else 1)
