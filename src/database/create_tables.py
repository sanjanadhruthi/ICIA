"""
create_tables.py - (re)creates all tables from sql/schema.sql.

Run from the project root:
    python -m src.database.create_tables
"""
from src.database.connection import run_sql_file
from src.utils.config import DB_PATH, ROOT
from src.utils.logger import get_logger

log = get_logger("create_tables")


def run():
    run_sql_file(ROOT / "sql" / "schema.sql")
    log.info("tables created in %s", DB_PATH)


if __name__ == "__main__":
    run()