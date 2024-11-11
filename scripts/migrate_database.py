"""
Database Migration Script

This script handles the migration of the database schema using Alembic.
It can be used to apply migrations or generate new migration scripts.
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alembic import command
from alembic.config import Config

# Set the path to the configuration file
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Import your database models here
# from your_app.models import Base

def get_database_url() -> str:
    """
    Get the database URL from environment variables or configuration.
    """
    db_user = os.getenv("DB_USER", "your_user")
    db_password = os.getenv("DB_PASSWORD", "your_password")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "your_database")

    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

def run_migrations():
    """
    Run database migrations using Alembic.
    """
    # Set up the Alembic configuration
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", get_database_url())

    # Create a new database engine
    engine = create_engine(get_database_url())
    Session = sessionmaker(bind=engine)
    session = Session()

    # Run migrations
    with engine.begin() as connection:
        alembic_cfg.attributes['connection'] = connection
        command.upgrade(alembic_cfg, "head")  # Upgrade to the latest migration

    session.close()
    print("Database migration completed successfully.")

def main():
    """
    Main entry point for the migration script.
    """
    try:
        run_migrations()
    except Exception as e:
        print(f"An error occurred during migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
