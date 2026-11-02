# Federal-Reserve-Economic-Data-ETL-Pipeline-part_1
An ETL pipeline that extracts economic indicators from the FRED API and loads them into a star-schema data warehouse (implemented in SQLite), to research the relationship between energy prices and inflation. The whole project is built with Python and its libraries only, so the pipeline is easy to read, understand, and run from start to finish with a single command. 

Energy prices are rising tremendously, and we use more energy now than ever. With inflation also increasing, I wanted to research the correlation between the two. In part two of this project I will analyze that correlation in depth and extend the pipeline for deeper research into the impact of data centers on energy prices.

<img width="2070" height="705" alt="image" src="https://github.com/user-attachments/assets/3a199292-5064-447b-b5f2-c8468f7051f5" />

The architecture of this pipeline extracts the needed data, transforms it, and loads it into a star schema, going from raw API calls to a populated, linked database.

**Extract** - Fetches six economic indicators from the FRED API (CPI, CPI energy, electricity, gas, oil, recession indicator). The API key is kept outside the code for safety. The logic is split into a reusable fetch_series (one series) and fetch_all_series (all series), with error handling so that one failed series does not break the whole pipeline.

**Transform** - Combines the six series into one long-format table, converts text to numbers, handles missing values, parses dates, and resamples the daily gas and oil prices into monthly averages. It builds three dimension tables (indicator, region, date) and attaches the correct ids to the fact table with a merge.

**Load** - Creates the tables with hand-written CREATE TABLE statements including primary and foreign keys, and loads the four tables in the correct order (dimensions first, facts last) into SQLite.

<img width="861" height="657" alt="image" src="https://github.com/user-attachments/assets/786df5b2-eb90-46bb-9e4a-e5240b5d4f8e" />

The data model is a star schema with one fact table and three dimensions.

fact table - the observations (the measured values + foreign keys)

dim_indicator - what is measured (linked)

dim_region - where it is measured (linked)

dim_date - when it is measured
	
I kept the date dimension unconnected for now because I join on the date column directly; adding a date_id link is a planned improvement.
I chose the star-schema model because I wanted it to stay simple — this research needed efficiency, not complexity.

What I have learned throughout this project is that the first lines of code are easy, but after 40 lines you start to regret what you wrote in the beginning. I learned that decisions and design choices matter before writing code: you have to think about what the final main() is going to look like, about the extensibility of the pipeline, and about whether it should run in one go or be split into separate stages.
On the technical side I learned to work with an API, clean data with Pandas, resample time series, model data dimensionally (Kimball: facts vs. dimensions, and when something deserves its own dimension versus being a row), and write SQL with foreign keys.
But the most important lesson was learning to design before coding splitting code into functions that each do one thing, treating main() as a readable plan, and building part 1 so that part 2 can be added on top without reworking the foundation.

Part 1 is functionally complete: a working, reproducible pipeline with a correct star schema, verified with a JOIN test showing plausible economic figures from 1947 to 2026. Part 2 — the deeper correlation analysis, the regional data-center angle, and a dashboard will be built on top of this foundation.

Sources — National series

**Indicator ==	URL**

General_CPI 	== fred.stlouisfed.org/series/CPIAUCSL  

CPI_energy ==	fred.stlouisfed.org/series/CPIENGSL 

Electricity_price_per_kWh == fred.stlouisfed.org/series/APU000072610 

Natural_gas_(Henry_Hub_spot) == fred.stlouisfed.org/series/DHHNGSP 

WTI_crude_oil	==	fred.stlouisfed.org/series/DC01LWTICO

Recession_indicator ==	fred.stlouisfed.org/series/USREC 

Note: gas and oil are fetched as daily series and resampled to monthly averages in the transform step, instead of using FRED's ready-made monthly series. This was a deliberate choice to practice time-series resampling.







