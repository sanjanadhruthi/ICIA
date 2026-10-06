"""
main.py - runs the whole ICIA pipeline with one command:

    python main.py

raw NCRB files -> cleaning -> transformation -> database -> analysis (charts + insights)
"""
from src.analysis import (anomaly_detection, category_analysis, city_analysis,
                          crime_trends, state_analysis)
from src.database import create_tables, load_data
from src.preprocessing import cleaning, transformation
from src.utils.logger import get_logger

log = get_logger("pipeline")

ANALYSES = [crime_trends, state_analysis, category_analysis, city_analysis, anomaly_detection]

STEPS = [
    ("1/5 cleaning raw files", cleaning.run),
    ("2/5 transforming", transformation.run),
    ("3/5 creating tables", create_tables.run),
    ("4/5 loading data", load_data.run),
    ("5/5 analysis", lambda: [m.run() for m in ANALYSES]),
]


def main():
    for name, step in STEPS:
        log.info("===== %s =====", name)
        step()
    log.info("pipeline finished")


if __name__ == "__main__":
    main()