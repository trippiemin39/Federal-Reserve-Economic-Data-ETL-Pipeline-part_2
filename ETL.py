import requests
import pandas as pd
import json
import sqlite3
import csv

#series_id's are the different indicators we need.
series_id = {"CPI":"CPIAUCSL",
          "CPIE": "CPIENGSL",
          "Electricity_price":"APU000072610",
          "Gas_price":"DHHNGSP",
          "Oil_price":"DCOILWTICO",
          "Recession_indicator":"USREC"
          }

# All 6 series overlap from 1997-01 (natural gas starts last).
# We cut all data before this date, so every indicator covers the same period.
START_DATE = "1997-01-01"

class Pipeline(object):
    def extract(self):
        # Opening API_CODE map to get personal API from fred i put my IPA in a txt document
        def load_api_key():
            with open('../API_CODE/FRED_API.txt') as f:
                api_key = f.read().strip()
            return api_key

        # the url needs the indicator code and a personal api
        # only taking the observation data of the api's, left out the meta data
        def fetch_series(code, api_key):
            try:
                url = f"https://api.stlouisfed.org/fred/series/observations?series_id={code}&api_key={api_key}&file_type=json"
                response = requests.get(url)
                df = pd.DataFrame(response.json()["observations"])

            except Exception as e:
                print(f"❌ Didn't fetch {code}: {e}")
                return None
            return df

        # creating dictionary to store the indicators
        def fetch_all_series(series_id, api_key):
            dfs = {}

            for name, code in series_id.items():
                df = fetch_series(code, api_key)

                if df is None:
                    print(f"{name} didn't fetch: API-error")
                    continue

                dfs[name] = df
            return dfs

        # ---------- EIA (part 2): electricity price + sales per US state ----------

        # Opening the EIA key, same way as the FRED key
        def load_eia_key():
            with open('../API_CODE/EIA_API.txt') as f:
                return f.read().strip()

        # EIA gives max 5000 rows per request, so we ask page by page.
        # price = cents per kWh, sales = million kWh
        # sectorid ALL = all customers, COM = commercial (our data center proxy)
        def fetch_eia_retail_sales(eia_key, start="2001-01"):
            url = "https://api.eia.gov/v2/electricity/retail-sales/data/"
            rows = []
            offset = 0

            while True:
                params = {
                    "api_key": eia_key,
                    "frequency": "monthly",
                    "data[0]": "price",
                    "data[1]": "sales",
                    "facets[sectorid][]": ["ALL", "COM"],
                    "start": start,
                    "sort[0][column]": "period",
                    "sort[0][direction]": "asc",
                    "offset": offset,
                    "length": 5000,
                }
                try:
                    response = requests.get(url, params=params, timeout=30)
                    response.raise_for_status()
                    page = response.json()["response"]["data"]
                except Exception as e:
                    print(f"❌ EIA fetch failed at offset {offset}: {e}")
                    break

                if not page:          # empty page = we have everything
                    break
                rows.extend(page)
                offset += 5000

            print(f"✅ EIA rows fetched: {len(rows)}")
            return rows

        # saving the EIA rows to their own json file
        def save_eia_json(rows):
            with open("eia_output.json", "w") as f:
                json.dump(rows, f)

        # ---------- FRED ----------

        # every dataframe is converted to a json file, orient=record means every record is an json object
        def save_json(dfs):
            json_dict = {name: df.to_dict(orient="records") for name, df in dfs.items()}
            with open("extract_output.json", "w") as f:
                json.dump(json_dict, f)

        def main():
            api_key = load_api_key()
            json_dict = fetch_all_series(series_id, api_key)
            save_json(json_dict)

            eia_key = load_eia_key()
            eia_rows = fetch_eia_retail_sales(eia_key)
            save_eia_json(eia_rows)
        main()


     # opening the json_file, loading the file with json.load()
    def transform(self):
        def load_extract_output():
            with open("extract_output.json") as f:
                json_file = f.read()
                data = json.loads(json_file)
            return data

        # making different dataframes of every indicator.
        # adding same ["indicator"] columns to identify the indicators
        # cleaning dataframes along the way
        def build_indicator_dataframes(data):
            dfs = {}

            for name in data:
                df = pd.DataFrame(data[name])
                df["indicator"] = name
                df["value"] = pd.to_numeric(df["value"], errors="coerce")
                df["date"] = pd.to_datetime(df["date"])
                df = df.dropna(subset=["value", "date"])
                df.drop(["realtime_start", "realtime_end"], axis="columns", inplace=True)

                dfs[name] = df
            return dfs

        #  this is for oil and gas because their datasets were daily not monthly
        def resample_price_series(df):
            df = df.set_index("date")
            monthly = df["value"].resample("MS").mean().reset_index()
            monthly["indicator"] = df["indicator"].iloc[0]
            return monthly

        # keeping only data from START_DATE, so all indicators start at the same time
        def filter_start_date(df):
            return df[df["date"] >= START_DATE].reset_index(drop=True)

        # DATA GAP CHECK: prints the months that are missing per indicator
        # known gap: October 2025 is missing in CPI (US government shutdown, no BLS data)
        def report_data_gaps(dfs):
            for name, df in dfs.items():
                all_months = pd.date_range(df["date"].min(), df["date"].max(), freq="MS")
                missing = all_months.difference(df["date"])
                if len(missing) > 0:
                    print(f"⚠️ {name} is missing {len(missing)} month(s): "
                          f"{[d.strftime('%Y-%m') for d in missing]}")

        #building dim_region, this dimension will be important in part 2.
        def build_region_dimension():
            DIM_region = pd.DataFrame({
                "region_id": [1],
                "region_code": ["US"],
                "region_name": ["United State of America"]
            })
            return DIM_region

        #builing dim_indicator, so there will be a link to fact table with the indicator_id
        def build_indicator_dimension():
            DIM_indicator = pd.DataFrame({
                "indicator_id": [1, 2, 3, 4, 5, 6],
                "indicator_code": ["CPIAUCSL", "CPIENGSL", "APU000072610", "DHHNGSP", "DCOILWTICO", "USREC"],
                "name": ["CPI", "CPIE", "Electricity_price", "Gas_price", "Oil_price", "Recession_indicator"],
                "category": ["inflation", "inflation", "energy", "energy", "energy", "macro"],
                "unit": ["index", "index", "USD/kWh", "USD/MMBTU", "USD/vat", "0/1"]
            })
            return DIM_indicator

        # making the date dimension from START_DATE until 2030
        # date_id is a number like 20240101, so the fact table can link to it
        def build_date_dimension(start=START_DATE, end="2030-12-31"):
            dates = pd.date_range(start=start, end=end, freq="D")

            DIM_date = pd.DataFrame({
                "date_id": dates.strftime("%Y%m%d").astype(int),
                "full_date": dates.strftime("%Y-%m-%d"),
                "month": dates.month,
                "year": dates.year,
                "quarter": dates.quarter,
                "month_name": dates.month_name(locale="en_US.utf8"),
            })
            return DIM_date

        # using the function concat to have one big table because the indicators have the same columns
        # left joining the dim_indicator with dff on 'indicator' and 'name' columns and creating a facttable
        # adding region id (for part 2 of this project) and observation id's
        def attach_keys(dfs, DIM_indicator):
            dff = pd.concat(dfs.values(), ignore_index=True)
            dff = dff.sort_values("date")

            facttable = (
                dff.merge(
                    DIM_indicator,
                    left_on="indicator",
                    right_on="name",
                    how="left"))

            facttable["region_id"] = 1
            facttable["observation_id"] = range(1, len(facttable) + 1)
            facttable["date_id"] = facttable["date"].dt.strftime("%Y%m%d").astype(int)

            facttable.drop(
                ["indicator", "indicator_code", "name", "category", "unit", "date"],
                axis=1,
                inplace=True
            )
            # fixed column order, because load() inserts the csv columns in this order
            facttable = facttable[["observation_id", "indicator_id", "region_id", "date_id", "value"]]
            return facttable


        # saving the 3 datasets to csv files
        def save_all(facttable, DIM_indicator, DIM_date, DIM_region):
            DIM_indicator.to_csv("DIM_indicator.csv", index=False)
            DIM_date.to_csv("DIM_date.csv", index=False)
            facttable.to_csv("facttable.csv", index=False)
            DIM_region.to_csv("DIM_region.csv", index=False)


        def main():
            data = load_extract_output()
            dfs = build_indicator_dataframes(data)

            for name in ["Gas_price", "Oil_price"]:
                dfs[name] = resample_price_series(dfs[name])

            for name in dfs:
                dfs[name] = filter_start_date(dfs[name])

            report_data_gaps(dfs)

            DIM_region = build_region_dimension()
            DIM_indicator = build_indicator_dimension()
            DIM_date = build_date_dimension()

            facttable = attach_keys(dfs, DIM_indicator)

            save_all(facttable, DIM_indicator, DIM_date, DIM_region)
        main()






    def load(self):

            #connect to the database
        def connect_db(datawarehouse):
            conn = sqlite3.connect(datawarehouse)
            conn.execute("PRAGMA foreign_keys = ON;")  # SQLite checks foreign keys only when this is on
            return conn

        #creating 4 tables with hand written CREATE table statements including primary and forein keys
        def create_tables(conn):
            cur = conn.cursor()

            # drop the fact table first, because it points to the dimensions
            cur.execute("""DROP TABLE IF EXISTS facttable_observation;""")
            cur.execute("""DROP TABLE IF EXISTS dim_indicator;""")
            cur.execute("""DROP TABLE IF EXISTS dim_region;""")
            cur.execute("""DROP TABLE IF EXISTS dim_date;""")

            cur.execute("""CREATE TABLE IF NOT EXISTS dim_indicator(
                            indicator_id INTEGER primary key,
                            indicator_code TEXT,
                            name TEXT,
                            category TEXT,
                            unit TEXT);""")

            cur.execute("""CREATE TABLE IF NOT EXISTS dim_region(
                            region_id INTEGER primary key,
                            region_code TEXT,
                            region_name TEXT);""")

            cur.execute("""CREATE TABLE IF NOT EXISTS dim_date(
                            date_id INTEGER PRIMARY KEY,
                            full_date TEXT,
                            month INTEGER,
                            year INTEGER,
                            quarter INTEGER,
                            month_name TEXT);""")

            cur.execute("""CREATE TABLE IF NOT EXISTS facttable_observation(
                        observation_id INTEGER primary key,
                        indicator_id INTEGER REFERENCES dim_indicator(indicator_id),
                        region_id INTEGER REFERENCES dim_region(region_id),
                        date_id INTEGER REFERENCES dim_date(date_id),
                        value FLOAT);""")
            conn.commit()

        #loading the tables with in correct order
        def load_table(conn, csv_path, table_name, columns):
            cur = conn.cursor()
            with open(csv_path) as f:
                reader = csv.reader(f)
                next(reader)  # skip header

                placeholders = ", ".join(["?"] * len(columns))
                colnames = ", ".join(columns)

                sql = f"INSERT INTO {table_name} ({colnames}) VALUES ({placeholders})"
                cur.executemany(sql, reader)
            conn.commit()


        def main():
            conn = connect_db("FREDDY.db")

            create_tables(conn)

            load_table(conn, "DIM_indicator.csv", "dim_indicator",
                       ["indicator_id", "indicator_code", "name", "category", "unit"])
            load_table(conn, "DIM_date.csv", "dim_date",
                       ["date_id", "full_date", "month", "year", "quarter", "month_name"])
            load_table(conn, "DIM_region.csv", "dim_region",
                       ["region_id", "region_code", "region_name"])

            load_table(conn, "facttable.csv", "facttable_observation",
                       ["observation_id", "indicator_id", "region_id", "date_id", "value"])
        main()


if __name__ == "__main__":
    pipeline = Pipeline()
    pipeline.extract()
    pipeline.transform()
    pipeline.load()













