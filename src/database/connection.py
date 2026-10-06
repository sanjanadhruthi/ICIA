"""connection.py - one place to open the ICIA database."""
import sqlite3
from contextlib import closing

from sqlalchemy import create_engine

from src.utils.config import DB_PATH


def get_engine():
    """SQLAlchemy engine - used with pandas (read_sql / to_sql)."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{DB_PATH.as_posix()}")


def run_sql_file(path):
    """Execute a whole .sql file (several statements) against the database."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(DB_PATH)) as con:
        con.executescript(path.read_text(encoding="utf-8"))
        con.commit()