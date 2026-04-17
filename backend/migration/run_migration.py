"""Run schema migration for Solarware.

This script creates required extensions and tables using SQLAlchemy metadata.
Use it when provisioning a fresh database (e.g., Render + Neon).
"""

from app.core.database import setup_database


if __name__ == "__main__":
    setup_database()
    print("Migration completed: database schema is up to date.")
