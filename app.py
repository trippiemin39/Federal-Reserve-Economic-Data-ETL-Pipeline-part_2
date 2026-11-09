"""Streamlit dashboard – FRED project part 2.

Run with:  streamlit run app.py
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import analysis as an

st.set_page_config(page_title="FRED Energy Dashboard", page_icon="⚡", layout="wide")

BLUE = "#2a78d6"     # high data center states / normal months / first series
ORANGE = "#eb6834"   # low data center states / recession months
COLORS = {"CPI": "#6250d6", "CPIE": "#2a78d6", "Electricity_price": "#eb6834",
          "Gas_price": "#1baf7a", "Oil_price": "#eda100",
          "State_electricity_price": "#e87ba4", "Commercial_electricity_price": "#008300",
          "State_electricity_sales": "#e34948", "Commercial_electricity_sales": "#898781"}
SHADE = "rgba(137, 135, 129, 0.18)"
FIRST_YEAR, BOOM_YEAR, LAST_YEAR = 2001, 2019, 2025


# ---------- data (loaded once) ----------

DB_PATH = an.find_database()
if DB_PATH is None:
    st.error("FREDDY.db not found. Run `python ETL.py` first, next to this app.")
    st.stop()


@st.cache_data
def get_data(db_path):
    national = an.load_national(db_path)
    units = an.load_units(db_path)
    monthly, states = an.load_states(db_path)
    return national, units, monthly, states


national, units, state_monthly, states = get_data(str(DB_PATH))


# ---------- chart helpers ----------

def show(fig, title, height=380, caption=None):
    """Same look for every chart: title above it, legend on top, hover on."""
    st.markdown(f"**{title}**")
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10),
                      legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0),
                      hovermode=fig.layout.hovermode or "x unified")
    fig.update_xaxes(showgrid=False)
    st.plotly_chart(fig, width="stretch")
    if caption:
        st.caption(caption)


def add_recessions(fig, flags, start, end, row=None, col=None):
    """Grey areas for every recession inside the chosen period."""
    for rec_start, rec_end in an.recession_periods(flags):
        if rec_end < start or rec_start > end:
            continue
        fig.add_vrect(x0=rec_start, x1=rec_end + pd.offsets.MonthEnd(1), fillcolor=SHADE,
                      line_width=0, layer="below", row=row, col=col)


# ---------- sidebar ----------

with st.sidebar:
    st.markdown("## ⚡ FRED Energy Dashboard")
    years = national.index.year
    period = st.slider("Period (Overview, RQ1–RQ3)", int(years.min()), int(years.max()),
                       (int(years.min()), int(years.max())))
    show_recessions = st.checkbox("Show recessions (grey areas)", value=True)
    border = st.slider("Data center border for RQ4 (%)", 3.0, 6.0, 4.0, 0.1,
                       help="A state is 'high' when data centers use this share of its electricity or more.")
    st.divider()
    st.markdown("**About the data**")
    st.caption("FRED: 6 national indicators (1997–2026) · EIA: electricity price and sales per state "
               "(2001–2026) · EPRI 2024: data center share per state (2023).")

start, end = pd.Timestamp(f"{period[0]}-01-01"), pd.Timestamp(f"{period[1]}-12-31")
levels = national.loc[start:end]
flags = an.recession_flags(national)
changes = an.monthly_changes(levels, [an.TARGET] + an.ENERGY)
period_flags = flags.loc[changes.index]
groups = an.assign_groups(states, border)
yearly = an.yearly_per_state(state_monthly, LAST_YEAR)

# results used on several tabs
lags = an.lag_table(changes, an.ENERGY, 12)
lag_summary = an.lag_summary(lags)
recession_table = an.compare_recessions(changes, period_flags, an.ENERGY)
price_groups = an.group_average(yearly, groups, "State_electricity_price")


# ---------- header + tabs ----------

st.title("Energy prices, inflation and data centers")
st.caption(f"Period {period[0]}–{period[1]} · data center border {border:.1f}%")

tab_overview, tab_rq12, tab_rq3, tab_rq4, tab_limits = st.tabs(
    ["Overview", "RQ1 + RQ2 · Energy & inflation", "RQ3 · Recessions",
     "RQ4 · Data centers", "Limitations"])


# ---------- tab 1: overview ----------

with tab_overview:
    left, right = st.columns([3, 2])
    with left:
        st.markdown("#### Main question")
        st.markdown("How strongly are energy prices and inflation connected, "
                    "and do data centers make electricity more expensive?")
    with right:
        st.markdown("#### Short answer")
        st.markdown("Energy prices and inflation are clearly connected, mainly through **oil**, and the effect "
                    "is almost **immediate**. The link is much **stronger in recessions**. States with many "
                    "data centers use much more electricity, but their prices are **lower and grew slower**.")

    oil = lag_summary.loc["Oil_price"]
    oil_rec = recession_table.loc["Oil_price"]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("RQ1 · Oil vs CPI", f"r = {oil['r same month']:.2f}", border=True,
              help=f"Strength: {oil['strength']}. Correlation of the monthly % change, same month.")
    m2.metric("RQ2 · Delay of oil effect", f"{oil['best lag (months)']} month(s)", border=True,
              help="The lag (0–12 months) with the strongest correlation.")
    m3.metric("RQ3 · Oil vs CPI: normal → recession",
              f"{oil_rec['r normal']:.2f} → {oil_rec['r recession']:.2f}", border=True,
              help=f"Really different (Fisher z-test): {oil_rec['really different']}.")
    m4.metric(f"RQ4 · Price {LAST_YEAR}: high vs low DC states",
              f"{price_groups.loc[LAST_YEAR, 'high']:.1f} vs {price_groups.loc[LAST_YEAR, 'low']:.1f}",
              border=True, help="Average electricity price in cents/kWh.")

    options = [c for c in national.columns if c != "Recession_indicator"]
    chosen = st.multiselect("Indicators", options, default=["CPI", "CPIE", "Oil_price", "Electricity_price"])

    fig = go.Figure()
    for name in chosen:
        series = levels[name].dropna()
        if series.empty:
            continue
        fig.add_trace(go.Scatter(x=series.index, y=series / series.iloc[0] * 100, name=name,
                                 line=dict(color=COLORS.get(name), width=2)))
    if show_recessions:
        add_recessions(fig, flags, start, end)
    fig.update_yaxes(title="index (first month = 100)")
    show(fig, "National indicators over time (indexed, first month = 100)", 420,
         caption="Indexed so all indicators share one scale. EIA indicators start in 2001. Grey = recession.")


# ---------- tab 2: RQ1 + RQ2 ----------

with tab_rq12:
    st.markdown("**RQ1:** How strongly are energy prices connected to inflation (CPI)?  \n"
                "**RQ2:** Do energy prices change before CPI changes (time lag)?")
    c1, c2 = st.columns([3, 1])
    energy_choice = c1.multiselect("Energy indicators", an.ENERGY, default=an.ENERGY)
    max_lag = c2.slider("Max lag (months)", 1, 12, 12)

    if not energy_choice:
        st.info("Choose at least one energy indicator.")
    else:
        chosen_lags = lags[lags["indicator"].isin(energy_choice) & (lags["lag"] <= max_lag)]
        chosen_summary = an.lag_summary(chosen_lags)

        left, right = st.columns([3, 2])
        with left:
            fig = go.Figure()
            for energy in energy_choice:
                line = chosen_lags[chosen_lags["indicator"] == energy]
                fig.add_trace(go.Scatter(x=line["lag"], y=line["r"], name=energy, mode="lines+markers",
                                         line=dict(color=COLORS[energy], width=2), marker=dict(size=7)))
                best = chosen_summary.loc[energy]
                fig.add_trace(go.Scatter(x=[best["best lag (months)"]], y=[best["r best lag"]], mode="markers",
                                         marker=dict(size=16, color="rgba(0,0,0,0)",
                                                     line=dict(color=COLORS[energy], width=2)),
                                         showlegend=False, hoverinfo="skip"))
            fig.add_hline(y=0, line_color="#c3c2b7")
            fig.update_xaxes(title="lag (months that CPI comes after the energy change)", dtick=1)
            fig.update_yaxes(title="correlation (r)")
            show(fig, "Correlation per lag (circle = best lag)", 400)
        with right:
            st.markdown("##### Result table")
            st.dataframe(chosen_summary, width="stretch")
            st.markdown("##### Answer")
            st.markdown("- **RQ1:** oil has the strongest link of the real energy prices (CPIE is partly "
                        "built in, because CPI includes energy).\n"
                        "- **RQ2:** the effect is almost immediate: same month or 1 month later.")

        fig = make_subplots(rows=1, cols=len(energy_choice), shared_yaxes=True,
                            subplot_titles=[f"{e} (r = {chosen_summary.loc[e, 'r same month']:.2f})"
                                            for e in energy_choice])
        for i, energy in enumerate(energy_choice, start=1):
            pair = changes[[energy, an.TARGET]].dropna()
            fig.add_trace(go.Scatter(x=pair[energy], y=pair[an.TARGET], mode="markers", name=energy,
                                     marker=dict(size=6, color=COLORS[energy], opacity=0.55),
                                     customdata=pair.index.strftime("%Y-%m"),
                                     hovertemplate="%{customdata}<br>energy %{x:.1f}%<br>CPI %{y:.2f}%"),
                          row=1, col=i)
            fig.update_xaxes(title=f"{energy} % change", row=1, col=i)
        fig.update_yaxes(title="CPI % change", row=1, col=1)
        fig.update_layout(showlegend=False, hovermode="closest")
        show(fig, "Same month: energy % change vs CPI % change (one dot = one month)", 330)


# ---------- tab 3: RQ3 ----------

with tab_rq3:
    st.markdown("**RQ3:** Is the link between energy prices and inflation different during recessions?")
    n_recession = int(period_flags.sum())
    if n_recession < 4:
        st.info("The chosen period has (almost) no recession months. Make the period wider in the sidebar.")
    else:
        left, right = st.columns([3, 2])
        with left:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=recession_table.index, y=recession_table["r normal"], name="Normal months",
                                 marker_color=BLUE, text=recession_table["r normal"], textposition="outside"))
            fig.add_trace(go.Bar(x=recession_table.index, y=recession_table["r recession"], name="Recession months",
                                 marker_color=ORANGE, text=recession_table["r recession"], textposition="outside"))
            labels = [f"{i}<br>{'✓ really different' if d == 'yes' else 'not different'}"
                      for i, d in zip(recession_table.index, recession_table["really different"])]
            fig.update_xaxes(tickvals=list(recession_table.index), ticktext=labels, tickangle=0)
            fig.update_yaxes(title="correlation with CPI (r)")
            fig.update_layout(barmode="group", bargap=0.25, bargroupgap=0.05, hovermode="x")
            show(fig, f"Normal ({len(changes) - n_recession} months) "
                                            f"vs recession ({n_recession} months)", 400)
        with right:
            st.markdown("##### What happened in each recession")
            st.caption("Average monthly % change")
            st.dataframe(an.change_per_recession(changes, period_flags, [an.TARGET] + an.ENERGY),
                         width="stretch")
            st.markdown("##### Answer")
            st.markdown("Yes. In recessions the link is much **stronger** for CPIE, oil and electricity "
                        "(Fisher z-test). Big energy price moves dominate inflation during a crisis. "
                        "Not for gas.")

        indicator = st.selectbox("Indicator for the time chart", an.ENERGY, index=3)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=changes.index, y=changes[indicator], name=indicator,
                                 line=dict(color=COLORS[indicator], width=1.5)))
        fig.add_trace(go.Scatter(x=changes.index, y=changes[an.TARGET], name="CPI",
                                 line=dict(color=COLORS["CPI"], width=1.5)))
        if show_recessions:
            add_recessions(fig, flags, start, end)
        fig.add_hline(y=0, line_color="#c3c2b7")
        fig.update_yaxes(title="% change per month")
        show(fig, f"Monthly % change of CPI and {indicator}", 340)
        with st.expander("Full table"):
            st.dataframe(recession_table, width="stretch")


# ---------- tab 4: RQ4 ----------

with tab_rq4:
    st.markdown("**RQ4:** Do states with many data centers have different electricity prices, "
                "and did their prices rise faster?")
    n_high = int((groups["dc_group"] == "high").sum())
    st.caption(f"Border {border:.1f}% → {n_high} high and {len(groups) - n_high} low data center states. "
               "Change the border in the sidebar.")

    measures = {"Electricity price (all sectors)": "State_electricity_price",
                "Commercial electricity price": "Commercial_electricity_price",
                "Commercial electricity use": "Commercial_electricity_sales"}
    periods = {f"{BOOM_YEAR}–{LAST_YEAR} (data center boom)": (BOOM_YEAR, LAST_YEAR),
               f"{FIRST_YEAR}–{BOOM_YEAR} (before the boom)": (FIRST_YEAR, BOOM_YEAR)}
    state_names = groups.sort_values("state_name")
    c1, c2, c3 = st.columns(3)
    measure_label = c1.selectbox("Measure", list(measures))
    period_label = c2.selectbox("Period for growth", list(periods))
    highlight = c3.selectbox("Highlight state", state_names.index,
                             index=list(state_names.index).index("VA"),
                             format_func=lambda s: f"{s} – {groups.loc[s, 'state_name']}")
    measure = measures[measure_label]
    growth_start, growth_end = periods[period_label]
    is_sales = measure == "Commercial_electricity_sales"

    left, right = st.columns(2)
    with left:
        if is_sales:
            by_group = an.group_total_index(yearly, groups, measure)
            state_line = yearly.loc[highlight, measure] / yearly.loc[highlight, measure].iloc[0] * 100
            y_title = f"total use ({FIRST_YEAR} = 100)"
        else:
            by_group = an.group_average(yearly, groups, measure)
            state_line = yearly.loc[highlight, measure]
            y_title = units.get(measure, "")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=by_group.index, y=by_group["high"], name="High DC states",
                                 line=dict(color=BLUE, width=2.5)))
        fig.add_trace(go.Scatter(x=by_group.index, y=by_group["low"], name="Low DC states",
                                 line=dict(color=ORANGE, width=2.5)))
        fig.add_trace(go.Scatter(x=state_line.index, y=state_line, name=highlight,
                                 line=dict(color="#52514e", width=1.5, dash="dot")))
        fig.add_vline(x=BOOM_YEAR, line_dash="dash", line_color="#c3c2b7")
        fig.update_yaxes(title=y_title)
        show(fig, f"{measure_label} per group (yearly)", 380)

    with right:
        tests = [("Price", "State_electricity_price", FIRST_YEAR, BOOM_YEAR),
                 ("Price", "State_electricity_price", BOOM_YEAR, LAST_YEAR),
                 ("Comm. use", "Commercial_electricity_sales", FIRST_YEAR, BOOM_YEAR),
                 ("Comm. use", "Commercial_electricity_sales", BOOM_YEAR, LAST_YEAR)]
        growth_table = pd.DataFrame({
            f"{label}<br>{s}–{str(e)[2:]}": an.compare_growth(an.growth_per_state(yearly, column, s, e), groups)
            for label, column, s, e in tests}).T
        fig = go.Figure()
        for group, color, column in [("high", BLUE, "high states (%)"), ("low", ORANGE, "low states (%)")]:
            values = growth_table[column].astype(float)
            fig.add_trace(go.Bar(x=growth_table.index, y=values, name=f"{group.capitalize()} DC states",
                                 marker_color=color, text=[f"{v:.0f}%" for v in values], textposition="outside"))
        labels = [f"{i}<br>{'✓ different' if d == 'yes' else 'not different'}"
                  for i, d in zip(growth_table.index, growth_table["really different"])]
        fig.update_xaxes(tickvals=list(growth_table.index), ticktext=labels, tickangle=0)
        fig.update_yaxes(title="average growth per state (%)")
        fig.update_layout(barmode="group", bargap=0.25, bargroupgap=0.05, hovermode="x")
        show(fig, "Growth per group (Welch t-test)", 380)

    left, right = st.columns(2)
    with left:
        growth = an.growth_per_state(yearly, measure, growth_start, growth_end)
        dots = growth.to_frame("growth").join(groups).dropna(subset=["growth", "dc_share_2023"])
        r, p, n = an.correlation(dots["dc_share_2023"], dots["growth"])
        fig = go.Figure()
        for group, color in [("high", BLUE), ("low", ORANGE)]:
            part = dots[dots["dc_group"] == group]
            fig.add_trace(go.Scatter(x=part["dc_share_2023"], y=part["growth"], mode="markers",
                                     name=f"{group.capitalize()} DC states",
                                     marker=dict(size=10, color=color, line=dict(color="white", width=1.5)),
                                     customdata=part["state_name"],
                                     hovertemplate="%{customdata}<br>share %{x:.1f}%<br>growth %{y:.1f}%"))
        if highlight in dots.index:
            point = dots.loc[highlight]
            fig.add_trace(go.Scatter(x=[point["dc_share_2023"]], y=[point["growth"]], mode="markers+text",
                                     text=[highlight], textposition="top right", showlegend=False,
                                     marker=dict(size=16, color="rgba(0,0,0,0)",
                                                 line=dict(color="#52514e", width=2)), hoverinfo="skip"))
        fig.update_xaxes(title="data center share of state electricity use, 2023 (%)")
        fig.update_yaxes(title=f"growth {growth_start}–{growth_end} (%)")
        fig.update_layout(hovermode="closest")
        show(fig, f"Data center share vs growth · r = {r:.2f}, p = {p:.3f}, {n} states", 400)

    with right:
        fig = go.Figure(go.Choropleth(
            locations=groups.index, z=groups["dc_share_2023"].fillna(0), locationmode="USA-states",
            colorscale=[[0, "#e6f0fb"], [0.2, "#86b6ef"], [1, "#184f95"]],
            customdata=groups["state_name"], colorbar=dict(title="%"),
            hovertemplate="%{customdata}: %{z:.1f}%<extra></extra>"))
        fig.update_layout(geo=dict(scope="usa", bgcolor="rgba(0,0,0,0)"))
        show(fig, "Data center share of state electricity use, 2023 (EPRI)", 400)
        st.caption("States without EPRI data are shown as 0%.")

    st.markdown("##### Answer")
    st.markdown("High data center states are **cheaper**, and their commercial electricity use grew **much "
                "faster**. But their prices grew **slower**, not faster. At state level we find no proof that "
                "data centers make electricity more expensive. Try other borders: the result stays the same.")
    with st.expander("Full t-test table"):
        st.dataframe(growth_table.rename(index=lambda i: i.replace("<br>", " ")), width="stretch")


# ---------- tab 5: limitations ----------

with tab_limits:
    left, right = st.columns(2)
    with left:
        st.markdown("#### Correlation is not causation")
        st.markdown("- All results show links, not causes. A third thing (a crisis, the weather) can move both.\n"
                    "- RQ4: data centers may choose cheap states. Then cheap power attracts data centers, "
                    "not the other way around.")
        st.markdown("#### Method")
        st.markdown("- 13 lags were tested per indicator, so a weak 'best lag' can be luck.\n"
                    "- Every state counts the same; a small state counts as much as Texas.\n"
                    "- State averages can hide effects on households, regions or the wholesale market.\n"
                    "- Prices also depend on fuel, weather, regulation and the power grid.")
    with right:
        st.markdown("#### Data")
        st.markdown("- CPI includes energy prices, so part of the link (especially CPIE) is built in.\n"
                    "- October 2025 is missing (US government shutdown).\n"
                    "- Only 28 recession months (3 recessions); 2020 is only 2 months but extreme.\n"
                    "- The data center share is from one year (2023).\n"
                    "- Commercial use is not only data centers (also shops, offices, hospitals).\n"
                    "- EPRI data was copied by hand; 6 states + DC are missing (counted as 'low').")
        st.markdown("#### Sources")
        st.markdown("- Electric Power Research Institute. (2024). *Powering intelligence: Analyzing artificial "
                    "intelligence and data center energy consumption* (Report No. 3002028905).\n"
                    "- Federal Reserve Bank of St. Louis. (n.d.). *FRED economic data* [Data sets: CPIAUCSL, "
                    "CPIENGSL, APU000072610, DHHNGSP, DCOILWTICO, USREC].\n"
                    "- U.S. Energy Information Administration. (n.d.). *Electricity sales to ultimate customers* "
                    "[Data set]. EIA Open Data API v2.\n\n"
                    "Full APA references: see the README.")
