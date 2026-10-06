-- =====================================================================
-- schema.sql - ICIA database (SQLite)
-- Rebuilt from scratch on every pipeline run, so it is always in sync
-- with data/processed/.
--
-- Core model (star schema):
--   dim_state ──┐
--               ├── fact_crime   one row per state x category x year
--   dim_category┘
-- Supporting tables keep NCRB's own state names (not harmonised),
-- because they contain rates/percentages that cannot simply be summed.
-- =====================================================================
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS fact_crime;
DROP TABLE IF EXISTS dim_state;
DROP TABLE IF EXISTS dim_category;
DROP TABLE IF EXISTS population;
DROP TABLE IF EXISTS ncrb_indicators;
DROP TABLE IF EXISTS police_disposal;
DROP TABLE IF EXISTS metro_city_crimes;
DROP TABLE IF EXISTS crime_heads;
DROP TABLE IF EXISTS property_stolen;

-- ---------------------------------------------------------------- core
CREATE TABLE dim_state (
    state_id    INTEGER PRIMARY KEY,
    state_name  TEXT    NOT NULL UNIQUE,
    zone        TEXT    NOT NULL
);

CREATE TABLE dim_category (
    category_id       INTEGER PRIMARY KEY,
    category_code     TEXT NOT NULL UNIQUE,
    category_label    TEXT NOT NULL,
    population_basis  TEXT NOT NULL      -- general / female / children
);

CREATE TABLE fact_crime (
    state_id          INTEGER NOT NULL REFERENCES dim_state(state_id),
    category_id       INTEGER NOT NULL REFERENCES dim_category(category_id),
    year              INTEGER NOT NULL CHECK (year BETWEEN 2016 AND 2030),
    cases             INTEGER,
    population_lakhs  REAL,
    crime_rate        REAL,              -- cases per lakh population
    yoy_change_pct    REAL,
    is_derived        INTEGER NOT NULL DEFAULT 0,   -- 1 = computed by us (IPC + SLL)
    PRIMARY KEY (state_id, category_id, year)
);
CREATE INDEX idx_fact_year ON fact_crime(year);

-- ---------------------------------------------------------------- supporting
CREATE TABLE population (
    state             TEXT    NOT NULL,
    year              INTEGER NOT NULL,
    population_group  TEXT    NOT NULL,
    population_lakhs  REAL,
    is_interpolated   INTEGER NOT NULL,
    PRIMARY KEY (state, year, population_group)
);

CREATE TABLE ncrb_indicators (       -- rates exactly as printed by NCRB
    state             TEXT    NOT NULL,
    year              INTEGER NOT NULL,
    category          TEXT    NOT NULL,
    population_lakhs  REAL,
    crime_rate        REAL,
    chargesheet_rate  REAL
);

CREATE TABLE police_disposal (
    state   TEXT    NOT NULL,
    year    INTEGER NOT NULL,
    metric  TEXT    NOT NULL,
    value   REAL,
    PRIMARY KEY (state, year, metric)
);

CREATE TABLE metro_city_crimes (
    city              TEXT    NOT NULL,
    state             TEXT,
    year              INTEGER NOT NULL,
    cases             INTEGER,
    population_lakhs  REAL,
    crime_rate        REAL,
    chargesheet_rate  REAL,
    PRIMARY KEY (city, year)
);

CREATE TABLE crime_heads (
    law          TEXT    NOT NULL,       -- IPC/BNS or SLL
    crime_head   TEXT    NOT NULL,
    serial       TEXT,
    is_main      INTEGER NOT NULL DEFAULT 0,   -- 1 = top-level head; sub-heads are already inside it
    year         INTEGER NOT NULL,
    cases        INTEGER,
    crime_rate   REAL,
    ipc_cases    INTEGER,                -- 2024 only
    bns_cases    INTEGER                 -- 2024 only
);

CREATE TABLE property_stolen (
    state            TEXT    NOT NULL,
    year             INTEGER NOT NULL,
    value_stolen     REAL,
    value_recovered  REAL,
    recovery_pct     REAL,
    PRIMARY KEY (state, year)
);