"""
database.py

Purpose: Single source of truth for how our application connects to
PostgreSQL. Every module (auth, claims, documents, etc.) will import
'SessionLocal' and 'Base' from here.

This replaces the manual psycopg2.connect() we did in test_db_connection.py
with SQLAlchemy's engine/session pattern - but underneath, it's still
talking to the SAME claimiq_db database via the SAME claimiq_app user.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ---------------------------------------------------------
# Load environment variables (same .env we've been using)
# ---------------------------------------------------------
load_dotenv()

DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")

# ---------------------------------------------------------
# Build the connection URL
# This is literally the same info you passed to psycopg2.connect()
# earlier, just assembled into one connection string format that
# SQLAlchemy expects.
# ---------------------------------------------------------
DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ---------------------------------------------------------
# The "engine" = SQLAlchemy's connection pool manager.
# This is the equivalent of psycopg2.connect(), but SQLAlchemy
# manages a POOL of connections instead of just one, and reuses
# them efficiently across many requests.
# ---------------------------------------------------------
engine = create_engine(DATABASE_URL, echo=True)
# echo=True means SQLAlchemy will PRINT every SQL command it generates
# to the console - this is intentional right now, so you can see
# exactly what SQL it's running under the hood (matches your goal of
# understanding what's happening, not just trusting a black box).

# ---------------------------------------------------------
# SessionLocal = a factory that creates a new "conversation" with
# the database. Think of each Session as one open conversation -
# you open it, do some reads/writes, then close it. This is the
# equivalent of opening a psycopg2 cursor, but SQLAlchemy adds
# extra tracking (so it knows which Python objects map to which
# database rows).
# ---------------------------------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ---------------------------------------------------------
# Base = the parent class that ALL our table models will inherit
# from. When we later write "class User(Base): ...", SQLAlchemy
# uses this Base to know "this Python class represents a database
# table."
# ---------------------------------------------------------
Base = declarative_base()


def get_db():
    """
    This function will be used by FastAPI later as a 'dependency' -
    it opens a database session, hands it to whatever endpoint needs
    it, and guarantees the session gets closed afterward (even if
    an error happens). We're not using this with FastAPI yet, but
    defining it now since every module will need this exact pattern.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()