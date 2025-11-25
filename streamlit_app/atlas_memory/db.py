# atlas_memory/db.py
# Modified for Streamlit Cloud - uses st.secrets instead of .env

import os
from contextlib import contextmanager
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Try Streamlit secrets first, fall back to env vars for local dev
def get_db_url():
    try:
        import streamlit as st
        tidb = st.secrets["tidb"]
        user = tidb["user"]
        password = quote_plus(tidb["password"])
        host = tidb["host"]
        port = tidb.get("port", "4000")
        db = tidb["database"]
        ca_path = tidb.get("ca_path", "/etc/ssl/certs/ca-certificates.crt")
    except Exception:
        # Fallback for local development
        from dotenv import load_dotenv
        load_dotenv()
        user = os.getenv("TIDB_USER")
        password = quote_plus(os.getenv("TIDB_PASSWORD", ""))
        host = os.getenv("TIDB_HOST")
        port = os.getenv("TIDB_PORT", "4000")
        db = os.getenv("TIDB_DB_NAME")
        ca_path = os.getenv("TIDB_CA_PATH", "/etc/ssl/cert.pem")

    return (
        f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}"
        f"?ssl_ca={ca_path}&ssl_verify_cert=true&ssl_verify_identity=true"
    )


engine = create_engine(get_db_url(), pool_recycle=3600)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
