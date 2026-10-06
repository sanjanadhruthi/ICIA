from pathlib import Path
import os
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
FIGURES_DIR = ROOT / "reports" / "figures"
INSIGHTS_DIR = ROOT / "reports" / "insights"
DB_PATH = ROOT / os.getenv("DB_PATH", "data/icia.db")

EDITIONS = {
    "cii_2018": (2016, 2018),
    "cii_2021": (2019, 2021),
    "cii_2024": (2022, 2024),
}