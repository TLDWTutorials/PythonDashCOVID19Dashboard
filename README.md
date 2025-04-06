# COVID-19 Total Cases Dashboard (Dash + Plotly)

This dashboard is a Python Dash app that visualizes **total COVID-19 cases** over time for any selected country (or countries) using data from the Our World in Data COVID-19 Dataset.  Data are automatically downloaded in the script (and there's a log to denote when data were downloaded so they aren't downloaded twice in a day). Source: [Our World in Data](https://ourworldindata.org/coronavirus-source-data).

It features:

-  Total cases line chart for selected countries
-  A red marker showing the **last increase in reported total cases**
-  A helpful annotation for when reporting appears to stop
-  High-contrast dark mode interface
-  Prevents re-downloading the dataset more than once per day (due to the time it may take to download data - and data are only updated daily anyway)

---

NOTE: Many countries have discountinue COVID-19 data reporting. In the code, I have added a red line to denote the cut-off point. 

## 1. Installation

### Clone the repository

```bash
git clone https://github.com/yourusername/covid-total-cases-dashboard.git
cd covid-total-cases-dashboard
```

### Install Python packages

Make sure Python 3.7+ is installed, then run:

```bash
pip install dash pandas plotly requests
```
## 2. The Code

### A. Configuration Settings
This sets the data URL, file paths, and defaults like which metric and country to load
```
# ---------------- CONFIG ----------------
DATA_URL = "https://covid.ourworldindata.org/data/owid-covid-data.csv"
DATA_FOLDER = "covid_data"
LOG_FILE = "download_log.txt"
DEFAULT_COUNTRIES = ["United States"]
METRIC = "total_cases"
# ----------------------------------------
```

### B. Download the dataset (once per day)
This function checks if the data has already been downloaded today, and if not, downloads and logs it.
```
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
```
### C. Load and clean the data
We load the CSV, convert dates, and filter out rows with missing values in our metric.
```
# Load and prepare data
df = pd.read_csv(filepath)
df["date"] = pd.to_datetime(df["date"])
df = df[df[METRIC].notna()]
countries = sorted(df["location"].unique())
```

### D. Create the Dash app layout
This defines the user interface: a header, a country selector dropdown, and a big graph below it.
```
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
```
### E. Define the callback to update the chart
This runs every time the dropdown changes. It:
- Filters data by country
- Adds the line trace
- Adds a red dot + annotation at the last increase point
- Updates layout styling
```
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

            # Red dot without legend
            fig.add_trace(go.Scatter(
                x=[last_date],
                y=[last_value],
                mode="markers",
                marker=dict(color="red", size=10),
                showlegend=False
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
```
### F. Run the app
This starts the Dash server when you run the script.
```
# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
```

## Data Source 
Shoutout to Our World in Data for hosting and maintaining the COVID-19 dataset

- COVID-19 data sourced from [Our World in Data](https://ourworldindata.org/coronavirus).
- Built with [Dash](https://dash.plotly.com/) and [Plotly](https://plotly.com/).


## License

This project is licensed under the MIT License. 



