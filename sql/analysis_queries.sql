-- =====================================================================
-- analysis_queries.sql - business questions answered with SQL
--
-- Run against data/icia.db (built by `python main.py`), e.g. in the
-- VS Code SQLite extension, DB Browser for SQLite, or:
--     python -m src.database.run_queries
--
-- Each query lists the question it answers and the SQL skill it shows.
-- =====================================================================


-- Q1. What is the overall crime trend in India, year by year?
-- Skills: JOIN, GROUP BY, aggregate functions, ratio of sums
SELECT  f.year,
        SUM(f.cases)                                             AS total_cases,
        ROUND(SUM(f.cases) * 1.0 / SUM(f.population_lakhs), 1)  AS crime_rate_per_lakh
FROM fact_crime f
JOIN dim_category c ON c.category_id = f.category_id
WHERE c.category_code = 'total_cognizable'
GROUP BY f.year
ORDER BY f.year;


-- Q2. Which 5 states had the highest crime rate in 2024?
-- Skills: filtering on a view, ORDER BY, LIMIT
SELECT  state, zone, cases, crime_rate
FROM v_crime
WHERE category = 'total_cognizable' AND year = 2024
ORDER BY crime_rate DESC
LIMIT 5;


-- Q3. How did each category change from the previous year?
-- Skills: window function LAG(), year-on-year % change
WITH national AS (
    SELECT category, year, SUM(cases) AS cases
    FROM v_crime
    GROUP BY category, year
)
SELECT  category, year, cases,
        LAG(cases) OVER (PARTITION BY category ORDER BY year)           AS prev_year_cases,
        ROUND((cases - LAG(cases) OVER (PARTITION BY category ORDER BY year)) * 100.0
              / LAG(cases) OVER (PARTITION BY category ORDER BY year), 1) AS yoy_change_pct
FROM national
ORDER BY category, year;


-- Q4. Which state ranks highest for each crime category in 2024?
-- Skills: CTE, window function ROW_NUMBER() with PARTITION BY ("top-N per group")
WITH ranked AS (
    SELECT  category, state, crime_rate,
            ROW_NUMBER() OVER (PARTITION BY category ORDER BY crime_rate DESC) AS rn
    FROM v_crime
    WHERE year = 2024 AND crime_rate IS NOT NULL
)
SELECT category, state, crime_rate
FROM ranked
WHERE rn = 1
ORDER BY crime_rate DESC;


-- Q5. Which states stayed above the national crime rate in EVERY year 2016-2024?
-- Skills: JOIN on two levels of aggregation, HAVING
SELECT  s.state
FROM v_crime s
JOIN v_national_trend n
  ON n.year = s.year AND n.category = s.category
WHERE s.category = 'total_cognizable'
GROUP BY s.state
HAVING SUM(CASE WHEN s.crime_rate > n.crime_rate THEN 1 ELSE 0 END) = COUNT(*)
ORDER BY s.state;


-- Q6. Which 10 states saw cyber crime grow the most (2016 to 2024)?
-- Skills: self-join, NULLIF to avoid division by zero, minimum-size filter
SELECT  a.state,
        a.cases AS cases_2016,
        b.cases AS cases_2024,
        ROUND((b.cases - a.cases) * 100.0 / NULLIF(a.cases, 0), 0) AS growth_pct
FROM v_crime a
JOIN v_crime b ON b.state = a.state AND b.category = a.category
WHERE a.category = 'cyber_crime' AND a.year = 2016 AND b.year = 2024
  AND a.cases >= 50                        -- ignore tiny bases (e.g. 1 -> 20 = +1900%)
ORDER BY growth_pct DESC
LIMIT 10;


-- Q7. What share of India's cases does each zone register, and is it fair to its population?
-- Skills: window function SUM() OVER () for "share of total"
SELECT  zone,
        SUM(cases)                                                        AS cases,
        ROUND(SUM(cases) * 100.0 / SUM(SUM(cases)) OVER (), 1)            AS share_of_cases_pct,
        ROUND(SUM(population_lakhs) * 100.0 / SUM(SUM(population_lakhs)) OVER (), 1)
                                                                          AS share_of_population_pct
FROM v_crime
WHERE category = 'total_cognizable' AND year = 2024
GROUP BY zone
ORDER BY cases DESC;


-- Q8. Classify each state's 2024 crime rate as High / Medium / Low.
-- Skills: CASE WHEN, NTILE() to split into thirds
WITH thirds AS (
    SELECT state, crime_rate,
           NTILE(3) OVER (ORDER BY crime_rate DESC) AS band
    FROM v_crime
    WHERE category = 'total_cognizable' AND year = 2024
)
SELECT  state, crime_rate,
        CASE band WHEN 1 THEN 'High' WHEN 2 THEN 'Medium' ELSE 'Low' END AS rate_band
FROM thirds
ORDER BY crime_rate DESC;


-- Q9. Do states that register more crime also chargesheet less?
-- Skills: joining a fact view with a supporting table, multi-condition filter
SELECT  v.state,
        v.crime_rate,
        i.chargesheet_rate
FROM v_crime v
JOIN ncrb_indicators i
  ON i.state = v.state AND i.year = v.year AND i.category = v.category
WHERE v.category = 'ipc_bns_crime' AND v.year = 2024
  AND i.chargesheet_rate IS NOT NULL
ORDER BY v.crime_rate DESC;


-- Q10. In 2024, which major offences were registered mostly under the new BNS?
-- Skills: subquery, percentage of total, filtering out hierarchy duplicates (is_main)
SELECT  crime_head,
        ipc_cases,
        bns_cases,
        ROUND(bns_cases * 100.0 / cases, 1) AS bns_share_pct
FROM crime_heads
WHERE law = 'IPC/BNS' AND year = 2024 AND is_main = 1
  AND cases >= (SELECT AVG(cases) FROM crime_heads
                WHERE law = 'IPC/BNS' AND year = 2024 AND is_main = 1)
  AND crime_head NOT LIKE 'Other%'
ORDER BY bns_share_pct DESC;


-- Q11. Which metro cities improved the most from 2022 to 2024?
-- Skills: conditional aggregation (pivot rows to columns with CASE inside SUM)
SELECT  city,
        SUM(CASE WHEN year = 2022 THEN cases END) AS cases_2022,
        SUM(CASE WHEN year = 2024 THEN cases END) AS cases_2024,
        ROUND((SUM(CASE WHEN year = 2024 THEN cases END)
             - SUM(CASE WHEN year = 2022 THEN cases END)) * 100.0
             / SUM(CASE WHEN year = 2022 THEN cases END), 1) AS change_pct
FROM metro_city_crimes
GROUP BY city
ORDER BY change_pct;


-- Q12. Data-quality check: are there any duplicate or missing rows?
-- Skills: validating data with GROUP BY / HAVING (every analyst should do this)
SELECT  'duplicate rows' AS check_name, COUNT(*) AS problems
FROM (SELECT state_id, category_id, year FROM fact_crime
      GROUP BY state_id, category_id, year HAVING COUNT(*) > 1)
UNION ALL
SELECT  'missing cases', COUNT(*) FROM fact_crime WHERE cases IS NULL
UNION ALL
SELECT  'state-years per category (should be 315 = 35 x 9)', MIN(n)
FROM (SELECT category_id, COUNT(*) AS n FROM fact_crime GROUP BY category_id);