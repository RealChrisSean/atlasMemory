# atlas_memory/db.py
import os
from contextlib import contextmanager
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Load .env variables into os.getenv()
load_dotenv()

def get_db_url():
    """
    Build a TiDB SQLAlchemy connection string.
    Password is URL-encoded so special characters don't break the URL.
    """
    user = os.getenv("TIDB_USER")
    password = quote_plus(os.getenv("TIDB_PASSWORD", ""))
    host = os.getenv("TIDB_HOST")
    port = os.getenv("TIDB_PORT", "4000")
    db = os.getenv("TIDB_DB_NAME")

    return (
        f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}"
        "?ssl_verify_cert=true&ssl_verify_identity=true"
    )

# Engine = factory that creates pooled DB connections
engine = create_engine(get_db_url(), pool_recycle=3600)

# SessionLocal = factory that gives you a session for queries/inserts
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_session():
    """
    Safe session wrapper.

    Usage:
        with get_session() as db:
            db.query(...)
    Ensures the session closes even if errors happen.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()