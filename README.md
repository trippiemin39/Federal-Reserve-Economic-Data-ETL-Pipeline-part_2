# Federal Reserve Economic Data ETL Pipeline – Part 2

An ETL pipeline that combines national economic data (FRED), electricity data per US state (EIA) and data center data per state (EPRI) in one star-schema data warehouse (SQLite), to research the link between energy prices, inflation and data centers.

This project builds on [Part 1](https://github.com/trippiemin39/Federal-Reserve-Economic-Data-ETL-Pipeline-part_1-), which created the pipeline for 6 national indicators.

## Research question

**How strongly are energy prices and inflation connected, and do data centers make electricity more expensive?**

## What is new in Part 2

- **Electricity prices and sales per US state** from a second API (EIA).
- **Data center share per state** from the EPRI 2024 report.
- **dim_region** grows from 1 region (US) to 52 (US + 50 states + DC).
- **dim_date** is now linked to the fact table with `date_id`.
- All data starts at **1997-01**, the first month where all FRED series overlap.
- A **data gap check** prints missing months when the pipeline runs.

## Architecture

<img width="1774" height="887" alt="image" src="https://github.com/user-attachments/assets/7f1f79e5-c753-4fb6-a9ed-90abbb282f15" />

**Extract**
- FRED API → 6 national indicators → `extract_output.json`
- EIA API v2 → electricity price and sales per state, monthly from 2001 (fetched page by page, max 5,000 rows per request) → `eia_output.json`

**Transform**
- Cleans the data (numbers, dates, missing values) and resamples daily gas and oil prices to monthly averages.
- Cuts all data before `START_DATE` (1997-01-01).
- Turns the EIA data into the same shape as the FRED data (date, value, indicator, region).
- Builds the dimensions and adds the EPRI data center data to `dim_region`.
- Builds the fact table and links it to all dimensions.

**Load**
- Creates the tables with primary and foreign keys and loads them into `FREDDY.db` (dimensions first, fact table last).

## Data model
<img width="1774" height="887" alt="image" src="https://github.com/user-attachments/assets/55818d8a-ba0b-4005-a9af-68f96fa5fc00" />

A star schema with one fact table and three dimensions.

| Table | What it holds |
|---|---|
| `facttable_observation` | Every measured value, with `indicator_id`, `region_id` and `date_id` (~66,000 rows) |
| `dim_indicator` | What is measured: 10 indicators (6 FRED + 4 EIA), with category and unit |
| `dim_region` | Where it is measured: US + 50 states + DC, with data center share and group (high/low) |
| `dim_date` | When it is measured: 1997-01-01 to 2030-12-31, key `date_id` (e.g. 20240101) |

## Data sources

| Source | Data | Period | Access |
|---|---|---|---|
| FRED | CPI, CPI energy, electricity price, natural gas, oil, recession indicator (US) | 1997 – 2026 | API (FRED key) |
| EIA | Electricity price (cents/kWh) and sales (million kWh) per state, all sectors and commercial | 2001-01 – 2026-08 | API (EIA key) |
| EPRI | Data center electricity use and share of state electricity use, 2023 | 2023 | Report (hand-made CSV) |

**EPRI data:** the EPRI report has no API or download. The data comes from Table A1 (Appendix A, pages 28–29) and was copied by hand into `data/data_center_share.csv`. We selected the 2023 load (MWh) and the 2023 share (%), added a state code for the join, and removed commas and % signs. The values were not changed. The 2030 projections in the table were not used.

## Design decisions

| Decision | Reason |
|---|---|
| All data starts at 1997-01 | First month where all 6 FRED series overlap (natural gas starts last) |
| Data is cut in transform, not extract | Raw data stays complete in the JSON files |
| EIA for state data | FRED has no electricity prices per state |
| EIA commercial sales as data center proxy | Data centers count as commercial customers |
| Data center share in `dim_region` | Only one year (2023) is available, so it acts as a property of a state |
| "High" = data center share of 4% or more | About the US average in 2023; set with `DC_HIGH_THRESHOLD` |
| EIA census regions removed | The research compares states only |

## Limitations

- **October 2025 is missing** in CPI, CPI energy and the FRED electricity price, because of the US government shutdown.
- **1 missing EIA value:** Rhode Island commercial sales, November 2024.
- **The state analysis starts in 2001**, because the monthly EIA data starts in 2001.
- **The data center data covers one year only (2023).** A state with many data centers in 2023 may have had few in earlier years.
- **6 states + DC are not in the EPRI table** (no significant data center load). They are counted as "low".
- **Commercial sales are not only data centers.** They also include shops, offices and hospitals.
- **The EPRI data was copied by hand**, so small typing mistakes are possible. The values were checked twice.
- **Correlation is not causation.** Electricity prices also depend on fuel costs, weather, regulation and the power grid.

## How to run

**1. Clone the repository**

```bash
git clone https://github.com/trippiemin39/Federal-Reserve-Economic-Data-ETL-Pipeline-part_2.git
cd Federal-Reserve-Economic-Data-ETL-Pipeline-part_2
```

**2. Install the dependencies**

```bash
pip install -r requirements.txt
```

**3. Get two free API keys**

- FRED: [fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html)
- EIA: [eia.gov/opendata](https://www.eia.gov/opendata/)

**4. Add your API keys**

Create a folder `API_CODE` with two text files. Put only the key in each file.

```
API_CODE/
├── FRED_API.txt   <-- your FRED key
└── EIA_API.txt    <-- your EIA key
```

This folder is in `.gitignore`, so your keys are never uploaded.

**5. Run the pipeline**

```bash
python ETL.py
```

This creates `FREDDY.db` with the full star schema.

## Project management

- Tasks are planned on a **GitHub Projects** board with 5 epics, user stories and sprints.
- We use **Git Flow**: `main` → `Develop` → `feature/<issue-number>-<name>`.
- Every change goes through a **pull request** and a review by a teammate.
- Team rules are in [CONTRIBUTING.md](CONTRIBUTING.md), the big picture is in [PROJECT_PLAN.md](PROJECT_PLAN.md).

## Status

- ✅ Epic 1 – Project setup
- ✅ Epic 2 – Pipeline expansion (data validation checks in progress)
- ⏳ Epic 3 – Correlation analysis
- ⏳ Epic 4 – Dashboard
- ⏳ Epic 5 – Documentation & delivery

## References

Electric Power Research Institute. (2024). *Powering intelligence: Analyzing artificial intelligence and data center energy consumption* (Report No. 3002028905). https://www.epri.com/research/products/3002028905

Federal Reserve Bank of St. Louis. (n.d.). *NBER based recession indicators for the United States from the period following the peak through the trough* [Data set, USREC]. FRED. Retrieved November 4, 2026, from https://fred.stlouisfed.org/series/USREC

U.S. Bureau of Labor Statistics. (n.d.-a). *Average price: Electricity per kilowatt-hour in U.S. city average* [Data set, APU000072610]. FRED, Federal Reserve Bank of St. Louis. Retrieved November 4, 2026, from https://fred.stlouisfed.org/series/APU000072610

U.S. Bureau of Labor Statistics. (n.d.-b). *Consumer price index for all urban consumers: All items in U.S. city average* [Data set, CPIAUCSL]. FRED, Federal Reserve Bank of St. Louis. Retrieved November 4, 2026, from https://fred.stlouisfed.org/series/CPIAUCSL

U.S. Bureau of Labor Statistics. (n.d.-c). *Consumer price index for all urban consumers: Energy in U.S. city average* [Data set, CPIENGSL]. FRED, Federal Reserve Bank of St. Louis. Retrieved November 4, 2026, from https://fred.stlouisfed.org/series/CPIENGSL

U.S. Energy Information Administration. (n.d.-a). *Crude oil prices: West Texas Intermediate (WTI) – Cushing, Oklahoma* [Data set, DCOILWTICO]. FRED, Federal Reserve Bank of St. Louis. Retrieved November 4, 2026, from https://fred.stlouisfed.org/series/DCOILWTICO

U.S. Energy Information Administration. (n.d.-b). *Electricity sales to ultimate customers* [Data set, electricity/retail-sales]. EIA Open Data API v2. Retrieved November 4, 2026, from https://www.eia.gov/opendata/browser/electricity/retail-sales

U.S. Energy Information Administration. (n.d.-c). *Henry Hub natural gas spot price* [Data set, DHHNGSP]. FRED, Federal Reserve Bank of St. Louis. Retrieved November 4, 2026, from https://fred.stlouisfed.org/series/DHHNGSP







