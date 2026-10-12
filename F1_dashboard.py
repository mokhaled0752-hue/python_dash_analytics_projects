"""
F1 Race Performance Analytics Dashboard
Uses FastF1 race data when available. If downloading fails, it creates clearly
labelled synthetic demo data so the dashboard can still run.
Run: python app.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

DATA_DIR = Path(__file__).parent / "data"
CACHE_DIR = DATA_DIR / "fastf1_cache"
DATA_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)
CSV_PATH = DATA_DIR / "f1_laps.csv"

def make_demo_laps(seed=11):
    rng = np.random.default_rng(seed)
    drivers = ["VER", "NOR", "LEC", "HAM", "PIA", "RUS", "SAI", "ALO"]
    teams = {"VER":"Red Bull", "NOR":"McLaren", "LEC":"Ferrari", "HAM":"Mercedes",
             "PIA":"McLaren", "RUS":"Mercedes", "SAI":"Ferrari", "ALO":"Aston Martin"}
    base = {"VER":91.2, "NOR":91.4, "LEC":91.7, "HAM":92.0,
            "PIA":91.8, "RUS":91.9, "SAI":92.1, "ALO":92.8}
    rows = []
    for driver in drivers:
        for lap in range(1, 57):
            compound = "SOFT" if lap <= 12 else ("MEDIUM" if lap <= 34 else "HARD")
            age = lap if lap <= 12 else (lap - 12 if lap <= 34 else lap - 34)
            time = base[driver] + age * (0.035 if compound == "SOFT" else 0.018) + rng.normal(0, .22)
            rows.append({"Driver": driver, "Team": teams[driver], "LapNumber": lap,
                         "LapTimeSeconds": round(time, 3), "Compound": compound,
                         "TyreLife": age, "Stint": 1 if lap <= 12 else (2 if lap <= 34 else 3),
                         "Source": "Synthetic demo data"})
    return pd.DataFrame(rows)

def load_laps():
    if CSV_PATH.exists():
        return pd.read_csv(CSV_PATH)
    try:
        import fastf1
        fastf1.Cache.enable_cache(str(CACHE_DIR))
        session = fastf1.get_session(2024, "Bahrain", "R")
        session.load( laps=True, telemetry=False, weather=False, messages=False)
        laps = session.laps.copy()
        laps["LapTimeSeconds"] = laps["LapTime"].dt.total_seconds()
        laps["Driver"] = laps["Driver"].astype(str)
        laps["Team"] = laps["Team"].fillna("Unknown")
        laps["LapNumber"] = pd.to_numeric(laps["LapNumber"], errors="coerce")
        laps["Compound"] = laps["Compound"].fillna("UNKNOWN")
        laps["TyreLife"] = pd.to_numeric(laps["TyreLife"], errors="coerce")
        laps["Stint"] = pd.to_numeric(laps["Stint"], errors="coerce")
        out = laps[["Driver", "Team", "LapNumber", "LapTimeSeconds",
                    "Compound", "TyreLife", "Stint"]].dropna(subset=["LapTimeSeconds", "LapNumber"])
        out["Source"] = "FastF1: 2024 Bahrain GP"
        out.to_csv(CSV_PATH, index=False)
        return out
    except Exception as exc:
        print(f"Could not download FastF1 data ({exc}). Loading synthetic demo data instead.")
        demo = make_demo_laps()
        demo.to_csv(CSV_PATH, index=False)
        return demo

df = load_laps()
df["LapNumber"] = pd.to_numeric(df["LapNumber"], errors="coerce")
df["LapTimeSeconds"] = pd.to_numeric(df["LapTimeSeconds"], errors="coerce")
df = df.dropna(subset=["Driver", "LapNumber", "LapTimeSeconds"])
app = Dash(__name__)
app.title = "F1 Performance Analytics"

def kpi(label, value):
    return html.Div([html.Div(label, style={"fontSize": "13px", "color": "#667085"}),
                     html.Div(value, style={"fontSize": "24px", "fontWeight": "700", "marginTop": "7px"})],
                    style={"background":"white", "padding":"18px", "borderRadius":"12px",
                           "boxShadow":"0 1px 5px #00000010", "flex":"1", "minWidth":"150px"})

app.layout = html.Div([
    html.H1("F1 Race Performance Analytics", style={"marginBottom":"4px"}),
    html.Div(f"Data source: {df['Source'].iloc[0]}",
             style={"color":"#667085", "marginBottom":"20px"}),
    html.Div([
        html.Div([html.Label("Driver"), dcc.Dropdown(id="drivers",
            options=[{"label": d, "value": d} for d in sorted(df["Driver"].unique())],
            value=sorted(df["Driver"].unique())[:4], multi=True, placeholder="Choose drivers")],
            style={"minWidth":"260px", "flex":"1"}),
        html.Div([html.Label("Tyre compound"), dcc.Dropdown(id="compound",
            options=[{"label": c, "value": c} for c in sorted(df["Compound"].dropna().unique())],
            multi=True, placeholder="All compounds")], style={"minWidth":"220px", "flex":"1"}),
        html.Div([html.Label("Lap range"), dcc.RangeSlider(id="lap-range",
            min=int(df["LapNumber"].min()), max=int(df["LapNumber"].max()),
            value=[int(df["LapNumber"].min()), int(df["LapNumber"].max())],
            marks=None, tooltip={"placement":"bottom", "always_visible":True})],
            style={"minWidth":"260px", "flex":"2"})
    ], style={"display":"flex", "gap":"18px", "flexWrap":"wrap", "alignItems":"end",
              "background":"white", "padding":"16px", "borderRadius":"12px", "marginBottom":"18px"}),
    html.Div(id="kpis", style={"display":"flex","gap":"14px","flexWrap":"wrap","marginBottom":"18px"}),
    html.Div([dcc.Graph(id="lap-chart"), dcc.Graph(id="compound-chart")],
             style={"display":"grid","gridTemplateColumns":"repeat(auto-fit, minmax(330px, 1fr))","gap":"14px"}),
    html.Div([dcc.Graph(id="driver-chart"), dcc.Graph(id="stint-chart")],
             style={"display":"grid","gridTemplateColumns":"repeat(auto-fit, minmax(330px, 1fr))","gap":"14px"}),
    html.Div("Note: lap-time analysis is not the same as final race classification. Pit-stop and finishing-position analysis can be added using session results.",
             style={"color":"#667085","fontSize":"12px","marginTop":"16px"})
], style={"fontFamily":"Arial, sans-serif","background":"#f4f6fa","minHeight":"100vh",
          "padding":"26px","color":"#182230"})

@app.callback(Output("kpis","children"), Output("lap-chart","figure"),
              Output("compound-chart","figure"), Output("driver-chart","figure"),
              Output("stint-chart","figure"),
              Input("drivers","value"), Input("compound","value"), Input("lap-range","value"))
def update(drivers, compounds, lap_range):
    d = df.copy()
    if drivers:
        d = d[d["Driver"].isin(drivers)]
    if compounds:
        d = d[d["Compound"].isin(compounds)]
    if lap_range:
        d = d[d["LapNumber"].between(lap_range[0], lap_range[1])]
    best = d["LapTimeSeconds"].min() if not d.empty else np.nan
    avg = d["LapTimeSeconds"].mean() if not d.empty else np.nan
    drivers_n = d["Driver"].nunique()
    laps_n = len(d)
    cards = [kpi("Fastest filtered lap", f"{best:.3f} s" if pd.notna(best) else "—"),
             kpi("Average lap time", f"{avg:.3f} s" if pd.notna(avg) else "—"),
             kpi("Drivers selected", str(drivers_n)), kpi("Lap records", f"{laps_n:,}")]

    line_data = d.groupby(["LapNumber","Driver"], as_index=False)["LapTimeSeconds"].mean()
    lap_fig = px.line(line_data, x="LapNumber", y="LapTimeSeconds", color="Driver",
                      markers=True, title="Lap time by lap and driver",
                      labels={"LapNumber":"Lap", "LapTimeSeconds":"Lap time (seconds)"})
    compound_data = d.groupby(["Compound","Driver"], as_index=False)["LapTimeSeconds"].mean()
    compound_fig = px.bar(compound_data, x="Compound", y="LapTimeSeconds", color="Driver",
                          barmode="group", title="Average lap time by tyre compound",
                          labels={"LapTimeSeconds":"Average seconds"})
    driver_data = d.groupby(["Driver","Team"], as_index=False).agg(
        AvgLap=("LapTimeSeconds","mean"), BestLap=("LapTimeSeconds","min"), Laps=("LapTimeSeconds","size"))
    driver_fig = px.bar(driver_data.sort_values("AvgLap"), x="Driver", y="AvgLap", color="Team",
                        hover_data=["BestLap","Laps"], title="Average lap time by driver",
                        labels={"AvgLap":"Average seconds"})
    stint_data = d.groupby(["Driver","Stint"], as_index=False).agg(
        AvgLap=("LapTimeSeconds","mean"), Laps=("LapTimeSeconds","size"))
    stint_fig = px.line(stint_data, x="Stint", y="AvgLap", color="Driver", markers=True,
                        title="Average lap time by stint",
                        labels={"Stint":"Stint number","AvgLap":"Average seconds"})
    for fig in [lap_fig, compound_fig, driver_fig, stint_fig]:
        fig.update_layout(template="plotly_white", margin=dict(l=25,r=20,t=60,b=35))
    return cards, lap_fig, compound_fig, driver_fig, stint_fig

if __name__ == "__main__":
    app.run(debug=True)
