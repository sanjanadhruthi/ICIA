"""
main.py - runs the whole ICIA pipeline with one command:

    python main.py

raw NCRB files -> cleaning -> transformation -> database tables -> data + views
"""
from src.database import create_tables, load_data
from src.preprocessing import cleaning, transformation
from src.utils.logger import get_logger

log = get_logger("pipeline")

STEPS = [
    ("1/4 cleaning raw files", cleaning.run),
    ("2/4 transforming", transformation.run),
    ("3/4 creating tables", create_tables.run),
    ("4/4 loading data", load_data.run),
]


def main():
    for name, step in STEPS:
        log.info("===== %s =====", name)
        step()
    log.info("pipeline finished")


if __name__ == "__main__":
    main()