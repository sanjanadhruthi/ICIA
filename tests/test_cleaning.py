"""
Tests for the ICIA pipeline.

Run from the project root:
    python -m pytest -v

The first group tests small cleaning functions on made-up inputs.
The second group checks the real processed data (run `python main.py` first;
these tests are skipped if the data has not been built yet).
"""
import math

import pandas as pd
import pytest

from src.preprocessing.cleaning import category_from_name, clean_state, to_number
from src.utils.config import PROCESSED_DIR


# ---------------------------------------------------------------- unit tests
@pytest.mark.parametrize("raw, expected", [
    ("1,234", 1234.0),      # thousands separator
    (" 56 ", 56.0),         # stray spaces
    (78, 78.0),             # already a number
])
def test_to_number_parses_numbers(raw, expected):
    assert to_number(raw) == expected


@pytest.mark.parametrize("raw", ["-", "NA", "", None])
def test_to_number_treats_dashes_and_blanks_as_missing(raw):
    assert math.isnan(to_number(raw))


@pytest.mark.parametrize("raw, expected", [
    ("Delhi UT", "Delhi"),
    ("Jammu & Kashmir*", "Jammu & Kashmir"),       # footnote mark removed
    ("D&N Haveli and Daman & Diu+", "DNH & Daman & Diu"),
    ("A & N Islands", "Andaman & Nicobar Islands"),
    ("Kerala", "Kerala"),                          # normal names unchanged
])
def test_clean_state_standardises_names(raw, expected):
    assert clean_state(raw) == expected


@pytest.mark.parametrize("filename, expected", [
    ("Crime against Women (IPC+SLL) - 2019-2021.xlsx", "crime_against_women"),
    ("Crime Against Children (IPC + SLL) - 2016-2018.xlsx", "crime_against_children"),
    ("Total IPCBNS & SLL Crimes  (StateUT-wise) - 2022-2024.xlsx", "total_cognizable"),
    ("SLL Crimes (StateUT-wise) - 2022-2024.xlsx", "sll_crime"),
    ("IPCBNS Crimes (StateUT-wise) - 2022-2024.xlsx", "ipc_bns_crime"),
])
def test_category_from_filename(filename, expected):
    assert category_from_name(filename) == expected


# ---------------------------------------------------------------- data tests
CRIME_FILE = PROCESSED_DIR / "crime_state_year.csv"
needs_data = pytest.mark.skipif(not CRIME_FILE.exists(),
                                reason="run `python main.py` first")


@pytest.fixture(scope="module")
def crime():
    return pd.read_csv(CRIME_FILE)


@needs_data
def test_every_category_has_35_states_every_year(crime):
    counts = crime.groupby(["category", "year"]).state.nunique()
    assert (counts == 35).all(), counts[counts != 35]


@needs_data
def test_no_duplicate_rows(crime):
    assert not crime.duplicated(["state", "category", "year"]).any()


@needs_data
def test_cases_are_never_negative(crime):
    assert (crime.cases.dropna() >= 0).all()


@needs_data
def test_2024_total_matches_ncrb_published_figure(crime):
    total = crime.query("category == 'total_cognizable' and year == 2024").cases.sum()
    assert total == 5_885_867   # NCRB, Crime in India 2024


@needs_data
def test_main_crime_heads_do_not_double_count():
    heads = pd.read_csv(PROCESSED_DIR / "crime_heads.csv")
    ipc_2024 = heads.query("law == 'IPC/BNS' and year == 2024")
    total = ipc_2024[ipc_2024.crime_head.str.startswith("Total")].cases.iat[0]
    main_sum = ipc_2024[ipc_2024.is_main].cases.sum()
    assert main_sum == pytest.approx(total, rel=0.001)