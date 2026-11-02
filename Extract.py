import requests
import pandas as pd
import json


series_id = {"CPI":"CPIAUCSL",
          "CPIE": "CPIENGSL",
          "Electricity_price":"APU000072610",
          "Gas_price":"DHHNGSP",
          "Oil_price":"DCOILWTICO",
          "Recession_indicator":"USREC"
          }


def load_api_key():
    with open('API_CODE/FRED_API.txt') as f:
        api_key = f.read().strip()
    return api_key



def fetch_series(code, api_key):
    try:
        url =  f"https://api.stlouisfed.org/fred/series/observations?series_id={code}&api_key={api_key}&file_type=json"
        response = requests.get(url)
        df = pd.DataFrame(response.json()["observations"])

    except Exception as e:
        print(f"❌ Didn't fetch {code}: {e}")
        return None
    return df


def fetch_all_series(series_id, api_key):
    dfs = {}

    for name, code in series_id.items():
        df = fetch_series(code, api_key)

        if df is None:
            print(f"{name} didn't fetch: API-error")
            continue

        dfs[name] = df
    return dfs



def save_json(dfs):
    json_dict = {name: df.to_dict(orient="records") for name, df in dfs.items()}
    with open("extract_output.json", "w") as f:
        json.dump(json_dict, f)



def main():
    api_key = load_api_key()
    json_dict = fetch_all_series(series_id, api_key)
    save_json(json_dict)

if __name__ == "__main__":
    main()
