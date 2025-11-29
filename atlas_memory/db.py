import os
from contextlib import contextmanager
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

load_dotenv()


class TiDBConnectionError(Exception):
    pass


def get_db_url():
    user = os.getenv("TIDB_USER")
    password = quote_plus(os.getenv("TIDB_PASSWORD", ""))
    host = os.getenv("TIDB_HOST")
    port = os.getenv("TIDB_PORT", "4000")
    db = os.getenv("TIDB_DB_NAME")
    ca_path = os.getenv("TIDB_CA_PATH", "/etc/ssl/cert.pem")

    missing = []
    if not user:
        missing.append("TIDB_USER")
    if not host:
        missing.append("TIDB_HOST")
    if not db:
        missing.append("TIDB_DB_NAME")

    if missing:
        raise TiDBConnectionError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Copy .env.example to .env and fill in your TiDB credentials."
        )

    return (
        f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}"
        f"?ssl_ca={ca_path}&ssl_verify_cert=true&ssl_verify_identity=true"
    )


def create_db_engine():
    try:
        url = get_db_url()
        return create_engine(url, pool_recycle=3600)
    except TiDBConnectionError:
        raise
    except Exception as e:
        raise TiDBConnectionError(f"Failed to create database engine: {e}")


def test_connection(eng):
    try:
        with eng.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except OperationalError as e:
        raise TiDBConnectionError(
            f"Failed to connect to TiDB: {e}. "
            "Check your credentials and network connection."
        )


engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
