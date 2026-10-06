-- =====================================================================
-- views.sql - ready-made summaries for analysis and the dashboard
-- =====================================================================
DROP VIEW IF EXISTS v_crime;
DROP VIEW IF EXISTS v_national_trend;
DROP VIEW IF EXISTS v_zone_trend;
DROP VIEW IF EXISTS v_state_ranking;
DROP VIEW IF EXISTS v_state_change;
DROP VIEW IF EXISTS v_bns_transition;

-- One readable row per state x category x year
CREATE VIEW v_crime AS
SELECT  s.state_name      AS state,
        s.zone,
        f.year,
        c.category_code   AS category,
        c.category_label,
        f.cases,
        f.population_lakhs,
        f.crime_rate,
        f.yoy_change_pct,
        f.is_derived
FROM fact_crime f
JOIN dim_state    s USING (state_id)
JOIN dim_category c USING (category_id);

-- All-India trend: rate = total cases / total population (not an average of rates)
CREATE VIEW v_national_trend AS
SELECT  year, category, category_label,
        SUM(cases)                                         AS cases,
        ROUND(SUM(population_lakhs), 1)                    AS population_lakhs,
        ROUND(SUM(cases) * 1.0 / SUM(population_lakhs), 2) AS crime_rate
FROM v_crime
WHERE cases IS NOT NULL
GROUP BY year, category, category_label;

CREATE VIEW v_zone_trend AS
SELECT  zone, year, category,
        SUM(cases)                                         AS cases,
        ROUND(SUM(cases) * 1.0 / SUM(population_lakhs), 2) AS crime_rate
FROM v_crime
WHERE cases IS NOT NULL
GROUP BY zone, year, category;

-- Rank states every year, by rate (fair) and by raw cases (size-driven)
CREATE VIEW v_state_ranking AS
SELECT  state, zone, year, category, cases, crime_rate,
        RANK() OVER (PARTITION BY year, category ORDER BY crime_rate DESC) AS rate_rank,
        RANK() OVER (PARTITION BY year, category ORDER BY cases DESC)      AS cases_rank
FROM v_crime
WHERE crime_rate IS NOT NULL;

-- How each state changed from the first year (2016) to the latest (2024)
CREATE VIEW v_state_change AS
SELECT  a.state, a.zone, a.category,
        a.crime_rate                                           AS rate_2016,
        b.crime_rate                                           AS rate_2024,
        ROUND(b.crime_rate - a.crime_rate, 2)                  AS rate_change,
        ROUND((b.cases - a.cases) * 100.0 / NULLIF(a.cases, 0), 1) AS cases_change_pct
FROM v_crime a
JOIN v_crime b ON a.state = b.state AND a.category = b.category
WHERE a.year = 2016 AND b.year = 2024;

-- 2024 was the IPC -> BNS switch year: how much of each crime head fell under BNS
CREATE VIEW v_bns_transition AS
SELECT  crime_head,
        ipc_cases, bns_cases,
        cases                                            AS total_cases,
        ROUND(bns_cases * 100.0 / NULLIF(cases, 0), 1)   AS bns_share_pct
FROM crime_heads
WHERE law = 'IPC/BNS' AND year = 2024 AND is_main = 1   -- top-level heads only, no double counting
  AND ipc_cases > 0 AND bns_cases > 0;   -- heads that exist in both laws