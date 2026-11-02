import pandas as pd
import json

def load_extract_output():
    with open("extract_output.json") as f:
        json_file = f.read()
        data = json.loads(json_file)
    return data


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



def resample_price_series(df):
    df = df.set_index("date")
    monthly = df["value"].resample("MS").mean().reset_index()
    monthly["indicator"] = df["indicator"].iloc[0]
    return monthly


def build_region_dimension():
    DIM_region = pd.DataFrame({
    "region_id" : [1],
    "region_code": ["US"],
    "region_name": ["United State of America"]
    })
    return DIM_region


def build_indicator_dimension():
    DIM_indicator = pd.DataFrame({
    "indicator_id": [1,2,3,4,5,6],
    "indicator_code": ["CPIAUCSL", "CPIENGSL", "APU000072610", "DHHNGSP","DCOILWTICO","USREC"],
    "name" : ["CPI", "CPIE", "Electricity_price", "Gas_price","Oil_price","Recession_indicator"],
    "category": ["inflation", "inflation", "energy", "energy","energy","macro"],
    "unit" : ["index", "index", "USD/kWh", "USD/MMBTU","USD/vat","0/1"]
    })
    return DIM_indicator


def build_date_dimension():
    start = "1947-01-01"
    end = "2030-12-31"
    dates = pd.date_range(start=start, end=end, freq="D")

    DIM_date = pd.DataFrame({
        "full_date": dates,
        "month": dates.month,
        "year": dates.year,
        "quarter": dates.quarter,
        "month_name": dates.month_name(locale="en_US.utf8"),
    })
    return DIM_date



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

    facttable.drop(
        ["indicator", "indicator_code", "name", "category", "unit"],
        axis=1,
        inplace=True
    )

    return facttable


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

    DIM_region = build_region_dimension()
    DIM_indicator = build_indicator_dimension()
    DIM_date = build_date_dimension()

    facttable = attach_keys(dfs, DIM_indicator)

    save_all(facttable, DIM_indicator, DIM_date, DIM_region)

if __name__ == "__main__":
    main()