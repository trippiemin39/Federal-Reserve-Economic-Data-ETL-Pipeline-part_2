"""All data loading and calculations for the dashboard.

The functions are the same as in the notebooks (#36, #37, #38),
so the dashboard shows exactly the same results.
"""
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm, pearsonr, ttest_ind

TARGET = "CPI"
ENERGY = ["CPIE", "Electricity_price", "Gas_price", "Oil_price"]
SIGNIFICANCE = 0.05


# ---------- loading ----------

def find_database():
    """Look for FREDDY.db next to this file and one folder above it."""
    here = Path(__file__).resolve().parent
    for path in [here / "FREDDY.db", here.parent / "FREDDY.db"]:
        if path.exists():
            return path
    return None


def load_national(db_path):
    """All US values: one row per month, one column per indicator."""
    query = """
        SELECT d.full_date AS date, i.name AS indicator, f.value
        FROM facttable_observation f
        JOIN dim_indicator i USING (indicator_id)
        JOIN dim_region    r USING (region_id)
        JOIN dim_date      d USING (date_id)
        WHERE r.region_code = 'US'
    """
    with sqlite3.connect(db_path) as conn:
        long = pd.read_sql(query, conn, parse_dates=["date"])
    return long.pivot(index="date", columns="indicator", values="value")


def load_units(db_path):
    """Unit of every indicator, for example 'cents/kWh'."""
    with sqlite3.connect(db_path) as conn:
        units = pd.read_sql("SELECT name, unit FROM dim_indicator", conn)
    return units.set_index("name")["unit"]


def load_states(db_path):
    """EIA values of all states (monthly) and one table with the EPRI data per state."""
    query = """
        SELECT d.year, r.region_code AS state, r.region_name AS state_name,
               r.dc_share_2023, i.name AS indicator, f.value
        FROM facttable_observation f
        JOIN dim_indicator i USING (indicator_id)
        JOIN dim_region    r USING (region_id)
        JOIN dim_date      d USING (date_id)
        WHERE r.region_type = 'state'
          AND i.name IN ('State_electricity_price', 'Commercial_electricity_price',
                         'Commercial_electricity_sales')
    """
    with sqlite3.connect(db_path) as conn:
        monthly = pd.read_sql(query, conn)
    states = (monthly[["state", "state_name", "dc_share_2023"]]
              .drop_duplicates()
              .set_index("state"))
    return monthly, states


# ---------- general ----------

def monthly_changes(levels, columns):
    """Monthly % change. A missing month stays empty instead of becoming a fake change."""
    return levels[columns].pct_change(fill_method=None) * 100


def recession_flags(levels):
    """True for every recession month."""
    return levels["Recession_indicator"] == 1


def correlation(x, y):
    """Pearson correlation between two series, using only months where both have a value."""
    pair = pd.concat([x, y], axis=1).dropna()
    if len(pair) < 4:
        return np.nan, np.nan, len(pair)
    r, p = pearsonr(pair.iloc[:, 0], pair.iloc[:, 1])
    return r, p, len(pair)


def strength(r):
    """Simple label for the size of a correlation."""
    size = abs(r)
    if size < 0.1:
        return "none"
    if size < 0.3:
        return "weak"
    if size < 0.5:
        return "moderate"
    return "strong"


# ---------- RQ1 + RQ2 (#36) ----------

def lag_table(changes, energy_list, max_lag, target=TARGET):
    """Correlation for every energy indicator and every lag from 0 to max_lag."""
    rows = []
    for energy in energy_list:
        for lag in range(max_lag + 1):
            r, p, n = correlation(changes[energy].shift(lag), changes[target])
            rows.append({"indicator": energy, "lag": lag, "r": r, "p_value": p, "months": n})
    return pd.DataFrame(rows)


def lag_summary(lags):
    """Per indicator: correlation in the same month and the lag with the strongest correlation."""
    rows = []
    for energy, group in lags.groupby("indicator", sort=False):
        same_month = group[group["lag"] == 0].iloc[0]
        best = group.loc[group["r"].abs().idxmax()]
        rows.append({
            "indicator": energy,
            "r same month": round(same_month["r"], 2),
            "best lag (months)": int(best["lag"]),
            "r best lag": round(best["r"], 2),
            "p-value": round(best["p_value"], 4),
            "significant": "yes" if best["p_value"] < SIGNIFICANCE else "no",
            "strength": strength(best["r"]),
        })
    return pd.DataFrame(rows).set_index("indicator")


# ---------- RQ3 (#37) ----------

def fisher_z_test(r1, n1, r2, n2):
    """p-value for the difference between two independent correlations."""
    z = (np.arctanh(r1) - np.arctanh(r2)) / np.sqrt(1 / (n1 - 3) + 1 / (n2 - 3))
    return 2 * (1 - norm.cdf(abs(z)))


def compare_recessions(changes, flags, energy_list, target=TARGET):
    """Correlation with CPI in normal and recession months, and if the difference is real."""
    normal = changes[~flags]
    recession = changes[flags]
    rows = []
    for energy in energy_list:
        r_norm, _, n_norm = correlation(normal[energy], normal[target])
        r_rec, _, n_rec = correlation(recession[energy], recession[target])
        p_diff = fisher_z_test(r_rec, n_rec, r_norm, n_norm) if n_rec > 3 else np.nan
        rows.append({
            "indicator": energy,
            "r normal": round(r_norm, 2),
            "r recession": round(r_rec, 2),
            "difference": round(r_rec - r_norm, 2),
            "p-value difference": round(p_diff, 4),
            "really different": "yes" if p_diff < SIGNIFICANCE else "no",
            "months normal": n_norm,
            "months recession": n_rec,
        })
    return pd.DataFrame(rows).set_index("indicator")


def recession_periods(flags):
    """List of (start, end) dates of every recession."""
    group_id = (flags != flags.shift()).cumsum()
    return [(months.index.min(), months.index.max())
            for _, months in flags[flags].groupby(group_id[flags])]


def change_per_recession(changes, flags, columns):
    """Average monthly % change of every indicator, per recession."""
    rows = {}
    for start, end in recession_periods(flags):
        rows[f"{start:%Y-%m} to {end:%Y-%m}"] = changes.loc[start:end, columns].mean()
    return pd.DataFrame(rows).T.round(2)


# ---------- RQ4 (#38) ----------

def assign_groups(states, border):
    """High = data center share of `border`% or more. States without EPRI data are low."""
    groups = states.copy()
    groups["dc_group"] = np.where(groups["dc_share_2023"] >= border, "high", "low")
    return groups


def yearly_per_state(monthly, last_year):
    """One row per state and year: prices averaged, sales added up."""
    data = monthly[monthly["year"] <= last_year]
    is_sales = data["indicator"] == "Commercial_electricity_sales"
    prices = data[~is_sales].groupby(["state", "year", "indicator"])["value"].mean()
    sales = data[is_sales].groupby(["state", "year", "indicator"])["value"].sum()
    return pd.concat([prices, sales]).unstack("indicator")


def group_average(yearly, groups, column):
    """Average of a column per group and year (every state counts the same)."""
    data = yearly[[column]].join(groups["dc_group"], on="state")
    return data.groupby(["year", "dc_group"])[column].mean().unstack()


def group_total_index(yearly, groups, column):
    """Total of a column per group and year, with the first year = 100."""
    data = yearly[[column]].join(groups["dc_group"], on="state")
    total = data.groupby(["year", "dc_group"])[column].sum().unstack()
    return total / total.iloc[0] * 100


def growth_per_state(yearly, column, start, end):
    """% growth of a column per state between two years."""
    table = yearly[column].unstack("year")
    return (table[end] / table[start] - 1) * 100


def compare_growth(growth, groups):
    """Average growth per group and a Welch t-test between the groups."""
    data = growth.to_frame("growth").join(groups["dc_group"]).dropna()
    high = data.loc[data["dc_group"] == "high", "growth"]
    low = data.loc[data["dc_group"] == "low", "growth"]
    _, p = ttest_ind(high, low, equal_var=False)
    return {"high states (%)": round(high.mean(), 1),
            "low states (%)": round(low.mean(), 1),
            "difference (%)": round(high.mean() - low.mean(), 1),
            "p-value": round(p, 4),
            "really different": "yes" if p < SIGNIFICANCE else "no"}
