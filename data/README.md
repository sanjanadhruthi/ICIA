# Data sources

All raw data comes from the **National Crime Records Bureau (NCRB)**, *Crime in India* reports,
downloaded from [data.gov.in](https://data.gov.in) and [ncrb.gov.in](https://ncrb.gov.in).
Each edition covers three years, so three editions give an unbroken series from **2016 to 2024**.

Files are kept exactly as downloaded; all cleaning happens in code (`src/preprocessing/cleaning.py`).

## Raw files (`data/raw/`)

### `cii_2018/`: Crime in India 2018 edition (covers 2016–2018)

| File | Contents | Level |
|---|---|---|
| Crime Against Children (IPC + SLL) - 2016-2018.xlsx | Crimes against children, rate per lakh children | State/UT |
| Crime against Women (IPC + SLL) - 2016-2018.xlsx | Crimes against women, rate per lakh women | State/UT |
| Cyber Crimes (StateUT-wise) – 2016-2018.xlsx | Cyber crimes | State/UT |
| IPC Crimes (StateUT-wise) - 2016-2018.xlsx | Indian Penal Code crimes, population, rate, chargesheeting | State/UT |
| SLL Crimes (StateUT-wise) - 2016-2018.xlsx | Special & Local Laws crimes | State/UT |
| Violent Crimes (Incidence & Crime Rate) – 2018.xlsx | Violent crimes, 2016–2018 | State/UT |

### `cii_2021/`: Crime in India 2021 edition (covers 2019–2021)

| File | Contents | Level |
|---|---|---|
| Crime against Children (IPC+SLL) - 2019-2021.xlsx | Crimes against children | State/UT |
| Crime against Women (IPC+SLL) - 2019-2021.xlsx | Crimes against women | State/UT |
| Cyber Crimes (StateUT-wise) - 2019-2021.xlsx | Cyber crimes | State/UT |
| IPC Crimes (StateUT-wise) - 2019-2021.xlsx | IPC crimes | State/UT |
| Police Disposal of IPC Crime Cases (StateUT-wise) - 2021.xlsx | Investigation outcomes: chargesheets, final reports, pendency (2021 only) | State/UT |
| SLL Crimes (StateUT-wise) - 2019-2021.xlsx | SLL crimes | State/UT |
| Violent Crimes (Incidence & Crime Rate) - 2019-2021.xlsx | Violent crimes | State/UT |

### `cii_2024/`: Crime in India 2024 edition (covers 2022–2024)

| File | Contents | Level |
|---|---|---|
| Crime against Children (IPCBNS+SLL Crimes) - 2022-2024.xlsx | Crimes against children | State/UT |
| Crime against Women (IPC+SLL) - 2022-2024.xlsx | Crimes against women | State/UT |
| Cyber Crimes (StateUT-wise) - 2022-2024.xlsx | Cyber crimes | State/UT |
| IPCBNS Crimes (StateUT-wise) - 2022-2024.xlsx | IPC + BNS crimes (2024 split into IPC / BNS / Total) | State/UT |
| Police Disposal of IPCBNS Crime Cases (StateUT-wise)-2024.xlsx | Investigation outcomes (2024 only) | State/UT |
| SLL Crimes (StateUT-wise) - 2022-2024.xlsx | SLL crimes | State/UT |
| Total IPCBNS & SLL Crimes (StateUT-wise) - 2022-2024.xlsx | Total cognizable crimes, used to verify IPC + SLL | State/UT |
| Violent Crimes (Incidence & Crime Rate) - 2022-2024.xlsx | Violent crimes | State/UT |

### `supplementary/`

| File | Contents | Years |
|---|---|---|
| IPCBNS Crimes (Crime-head wise) 2022-24.xlsx | National cases per individual offence (theft, hurt…) with IPC/BNS split for 2024 | 2022–2024 |
| SLL Crimes (Crime head-wise) 2022-24.xlsx | National cases per Special & Local Law | 2022–2024 |
| Metropolitan Cities - Total IPC+BNS+SLL Crimes 2022-24.xlsx | 19 cities with over 20 lakh population | 2022–2024 |
| StateUT-wise Value of Property Stolen and Recovered … 2021 to 2023.csv | Value of property stolen and recovered | 2021–2023 |
| Total Cases Registered 2022-2024.xlsx | Complaints received and cases registered (not yet used) | 2022–2024 |

## Processed files (`data/processed/`)

Created by `python main.py`. Do not edit by hand.

| File | One row per | Key columns |
|---|---|---|
| `crime_state_year.csv` | state × category × year | cases, population_lakhs, crime_rate, yoy_change_pct, zone |
| `state_crime_cases.csv` | state × category × year (before harmonising) | cases, edition, source_file |
| `state_indicators.csv` | state × category × year | NCRB's printed population, crime rate, chargesheeting rate |
| `population.csv` | state × year × group | population (general / female / children), interpolated flag |
| `police_disposal.csv` | state × year × measure | value |
| `crime_heads.csv` | offence × year | cases, crime_rate, ipc_cases, bns_cases, is_main |
| `metro_city_crimes.csv` | city × year | cases, crime_rate, chargesheet_rate |
| `property_stolen.csv` | state × year | value_stolen, value_recovered, recovery_pct |

## Adjustments made

- **Jammu & Kashmir** includes **Ladakh** in every year (they were split in 2019).
- **Dadra & Nagar Haveli** and **Daman & Diu** are combined in every year (merged in 2020).
- Result: **35 consistent states/UTs** across all nine years.
- Total cognizable crime for **2016–2021 = IPC + SLL** (verified against NCRB's own totals for 2022–2024).
- Population for years without an NCRB figure is **linearly interpolated**.