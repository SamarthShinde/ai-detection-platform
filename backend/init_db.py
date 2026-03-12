#!/usr/bin/env python3
"""
Database initialization script.
Usage:
    python init_db.py           # create tables
    python init_db.py --reset   # drop all tables then recreate
"""
import argparse
import logging
import sys

from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def init_db(reset: bool = False) -> None:
    from app.models.database import Base
    from app.utils.db import engine

    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("Connected to PostgreSQL")

    if reset:
        logger.warning("Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        logger.info("All tables dropped")

    Base.metadata.create_all(bind=engine)
    logger.info("All tables created successfully")
    logger.info("Tables: %s", list(Base.metadata.tables.keys()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize the database")
    parser.add_argument("--reset", action="store_true", help="Drop all tables before recreating")
    args = parser.parse_args()

    try:
        init_db(reset=args.reset)
        logger.info("Database initialization complete")
    except Exception as exc:
        logger.error("Database initialization failed: %s", exc)
        sys.exit(1)
