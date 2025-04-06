import os
import requests
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

# ---------------- CONFIG ----------------
DATA_URL = "https://covid.ourworldindata.org/data/owid-covid-data.csv"
DATA_FOLDER = "covid_data"
LOG_FILE = "download_log.txt"
DEFAULT_COUNTRIES = ["United States"]
METRIC = "total_cases"
# ----------------------------------------

# Ensure folder exists
os.makedirs(DATA_FOLDER, exist_ok=True)

# Today's filename
today = datetime.today().strftime("%Y-%m-%d")
filename = f"owid-covid-data_{today}.csv"
filepath = os.path.join(DATA_FOLDER, filename)

# Download if not already today
def download_if_needed():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as log:
            if today in log.read():
                return
    print("[INFO] Downloading COVID dataset...")
    r = requests.get(DATA_URL)
    r.raise_for_status()
    with open(filepath, "wb") as f:
        f.write(r.content)
    with open(LOG_FILE, "a") as log:
        log.write(f"{today} - Downloaded\n")

download_if_needed()

# Load and prepare data
df = pd.read_csv(filepath)
df["date"] = pd.to_datetime(df["date"])
df = df[df[METRIC].notna()]
countries = sorted(df["location"].unique())

# ---------------- DASH APP ----------------
app = Dash(__name__)
app.title = "COVID-19 Multi-Country Dashboard"

app.layout = html.Div(
    style={"backgroundColor": "#121212", "height": "100vh", "padding": "20px"},
    children=[
        html.H1(
            "COVID-19 Dashboard (Total Cases)",
            style={"textAlign": "center", "color": "#81d4fa"}
        ),
        html.Div([
            html.Label("Select Country/Countries:", style={"color": "#e0f7fa"}),
            dcc.Dropdown(
                id="country-selector",
                options=[{"label": c, "value": c} for c in countries],
                value=DEFAULT_COUNTRIES,
                multi=True,
                style={"color": "#000", "width": "100%"}
            ),
        ], style={"marginBottom": "20px"}),
        dcc.Graph(id="line-chart", style={"height": "80vh"})
    ]
)

# ---------------- CALLBACK ----------------
@app.callback(
    Output("line-chart", "figure"),
    Input("country-selector", "value")
)
def update_chart(selected_countries):
    if not selected_countries:
        return go.Figure()

    fig = go.Figure()
    global_min_date = df["date"].min().strftime("%b %d, %Y")
    global_max_date = df["date"].max().strftime("%b %d, %Y")

    for country in selected_countries:
        country_df = df[df["location"] == country].sort_values("date")
        country_df["delta"] = country_df[METRIC].diff()

        # Main line
        fig.add_trace(go.Scatter(
            x=country_df["date"],
            y=country_df[METRIC],
            mode="lines",
            name=country,
            line=dict(width=2)
        ))

        # Last increase
        last_increase_idx = country_df[country_df["delta"] > 0].last_valid_index()
        if last_increase_idx:
            last_date = country_df.loc[last_increase_idx, "date"]
            last_value = country_df.loc[last_increase_idx, METRIC]

            # Red dot without legend entry
            fig.add_trace(go.Scatter(
                x=[last_date],
                y=[last_value],
                mode="markers",
                marker=dict(color="red", size=10),
                showlegend=False  # Do not include in legend
            ))

            # Annotation
            fig.add_annotation(
                x=last_date,
                y=last_value,
                text=f"Reporting stopped for {country}",
                showarrow=True,
                arrowhead=2,
                ax=0,
                ay=-40,
                font=dict(color="red"),
                bgcolor="#222",
                bordercolor="red",
                borderwidth=1
            )

    fig.update_layout(
        title=f"Total COVID-19 Cases ({global_min_date} – {global_max_date})",
        xaxis_title="Date",
        yaxis_title="Total Cases",
        plot_bgcolor="#0d0d0d",
        paper_bgcolor="#0d0d0d",
        font=dict(color="#ffffff"),
        xaxis=dict(gridcolor="#333333"),
        yaxis=dict(gridcolor="#333333"),
        margin=dict(l=60, r=30, t=60, b=50)
    )

    return fig

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
