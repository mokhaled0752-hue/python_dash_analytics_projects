"""
E-Commerce Sales Analytics Dashboard
Demo data is synthetically generated for portfolio practice.
Run: python app.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
CSV_PATH = DATA_DIR / "ecommerce_orders.csv"

def make_data(n=5000, seed=42):
    rng = np.random.default_rng(seed)
    dates = pd.to_datetime(rng.choice(pd.date_range("2024-01-01", "2025-12-31", freq="D"), n))
    products = ["Laptop Stand", "Wireless Mouse", "Keyboard", "Monitor", "USB Hub",
                "Headphones", "Webcam", "Desk Lamp", "SSD Drive", "Phone Holder"]
    prices = {"Laptop Stand": 28, "Wireless Mouse": 19, "Keyboard": 45, "Monitor": 220,
              "USB Hub": 24, "Headphones": 65, "Webcam": 55, "Desk Lamp": 32,
              "SSD Drive": 89, "Phone Holder": 14}
    product = rng.choice(products, n)
    quantity = rng.integers(1, 5, n)
    unit_price = np.array([prices[p] for p in product]) * rng.uniform(0.85, 1.15, n)
    discount = rng.choice([0, .05, .10, .15, .20], n, p=[.48, .15, .20, .12, .05])
    countries = rng.choice(["United Kingdom", "Germany", "France", "Netherlands", "Spain", "Italy"], n)
    customers = rng.integers(10000, 11000, n)
    status = rng.choice(["Completed", "Completed", "Completed", "Returned", "Cancelled"], n)
    df = pd.DataFrame({
        "OrderID": [f"ORD{i:06d}" for i in range(1, n + 1)],
        "OrderDate": dates, "CustomerID": [f"C{c}" for c in customers],
        "Country": countries, "Product": product, "Quantity": quantity,
        "UnitPrice": unit_price.round(2), "Discount": discount,
        "Status": status
    })
    df["Revenue"] = (df["Quantity"] * df["UnitPrice"] * (1 - df["Discount"])).round(2)
    # Add a few deliberately imperfect rows to demonstrate cleaning.
    df.loc[12, "Country"] = None
    df.loc[28, "Quantity"] = -1
    return df

def load_data():
    if CSV_PATH.exists():
        df = pd.read_csv(CSV_PATH, parse_dates=["OrderDate"])
    else:
        df = make_data()
        df.to_csv(CSV_PATH, index=False)
    df["OrderDate"] = pd.to_datetime(df["OrderDate"], errors="coerce")
    df = df.drop_duplicates(subset=["OrderID"])
    df = df.dropna(subset=["OrderDate", "Product", "Country"])
    df = df[df["Quantity"] > 0]
    df = df[df["Status"] == "Completed"].copy()
    df["Revenue"] = df["Quantity"] * df["UnitPrice"] * (1 - df["Discount"])
    df["Month"] = df["OrderDate"].dt.to_period("M").astype(str)
    df["OrderMonth"] = df["OrderDate"].dt.to_period("M").dt.to_timestamp()
    return df

df = load_data()
app = Dash(__name__)
app.title = "E-Commerce Analytics"

def card(label, value):
    return html.Div([
        html.Div(label, style={"fontSize": "13px", "color": "#667085"}),
        html.Div(value, style={"fontSize": "25px", "fontWeight": "700", "marginTop": "7px"})
    ], style={"background": "white", "padding": "18px", "borderRadius": "12px",
              "boxShadow": "0 1px 5px #00000010", "flex": "1", "minWidth": "150px"})

app.layout = html.Div([
    html.Div([
        html.H1("E-Commerce Sales Analytics", style={"marginBottom": "5px"}),
        html.Div("Interactive sales and customer performance dashboard",
                 style={"color": "#667085"})
    ], style={"marginBottom": "22px"}),
    html.Div([
        html.Div([html.Label("Date range"),
                  dcc.DatePickerRange(id="dates",
                      min_date_allowed=df["OrderDate"].min().date(),
                      max_date_allowed=df["OrderDate"].max().date(),
                      start_date=df["OrderDate"].min().date(),
                      end_date=df["OrderDate"].max().date())]),
        html.Div([html.Label("Country"),
                  dcc.Dropdown(id="country", options=[{"label": c, "value": c}
                      for c in sorted(df["Country"].unique())], multi=True,
                      placeholder="All countries")], style={"minWidth": "230px", "flex": "1"}),
        html.Div([html.Label("Product"),
                  dcc.Dropdown(id="product", options=[{"label": p, "value": p}
                      for p in sorted(df["Product"].unique())], multi=True,
                      placeholder="All products")], style={"minWidth": "230px", "flex": "1"}),
    ], style={"display": "flex", "gap": "18px", "flexWrap": "wrap",
              "alignItems": "end", "background": "white", "padding": "16px",
              "borderRadius": "12px", "marginBottom": "18px"}),
    html.Div(id="kpis", style={"display": "flex", "gap": "14px", "flexWrap": "wrap",
                               "marginBottom": "18px"}),
    html.Div([
        dcc.Graph(id="sales-trend"),
        dcc.Graph(id="product-chart")
    ], style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(330px, 1fr))",
              "gap": "14px"}),
    html.Div([
        dcc.Graph(id="country-chart"),
        dcc.Graph(id="customer-chart")
    ], style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(330px, 1fr))",
              "gap": "14px"}),
    html.H3("Filtered order data"),
    html.Div(id="data-table", style={"overflowX": "auto"}),
    html.Div("Portfolio demo: the included dataset is synthetic, not real company data.",
             style={"color": "#667085", "fontSize": "12px", "marginTop": "20px"})
], style={"fontFamily": "Arial, sans-serif", "background": "#f4f6fa",
          "minHeight": "100vh", "padding": "26px", "color": "#182230"})

@app.callback(
    Output("kpis", "children"), Output("sales-trend", "figure"),
    Output("product-chart", "figure"), Output("country-chart", "figure"),
    Output("customer-chart", "figure"), Output("data-table", "children"),
    Input("dates", "start_date"), Input("dates", "end_date"),
    Input("country", "value"), Input("product", "value")
)
def update_dashboard(start, end, countries, products):
    d = df.copy()
    if start:
        d = d[d["OrderDate"] >= pd.to_datetime(start)]
    if end:
        d = d[d["OrderDate"] < pd.to_datetime(end) + pd.Timedelta(days=1)]
    if countries:
        d = d[d["Country"].isin(countries)]
    if products:
        d = d[d["Product"].isin(products)]

    revenue = d["Revenue"].sum()
    orders = d["OrderID"].nunique()
    customers = d["CustomerID"].nunique()
    aov = revenue / orders if orders else 0
    kpis = [card("Revenue", f"£{revenue:,.0f}"), card("Completed orders", f"{orders:,}"),
            card("Unique customers", f"{customers:,}"), card("Average order value", f"£{aov:,.2f}")]

    monthly = d.groupby("OrderMonth", as_index=False)["Revenue"].sum()
    trend = px.line(monthly, x="OrderMonth", y="Revenue", markers=True,
                    title="Monthly revenue", labels={"OrderMonth": "Month", "Revenue": "Revenue (£)"})
    by_product = d.groupby("Product", as_index=False)["Revenue"].sum().sort_values("Revenue", ascending=False)
    prod_fig = px.bar(by_product, x="Product", y="Revenue", title="Revenue by product",
                      labels={"Revenue": "Revenue (£)"})
    by_country = d.groupby("Country", as_index=False)["Revenue"].sum().sort_values("Revenue", ascending=False)
    country_fig = px.bar(by_country, x="Country", y="Revenue", title="Revenue by country",
                         labels={"Revenue": "Revenue (£)"})
    by_customer = d.groupby("CustomerID", as_index=False).agg(Revenue=("Revenue", "sum"),
                                                              Orders=("OrderID", "nunique"))
    by_customer = by_customer.nlargest(10, "Revenue")
    cust_fig = px.bar(by_customer, x="CustomerID", y="Revenue", title="Top 10 customers by revenue",
                      hover_data=["Orders"], labels={"Revenue": "Revenue (£)"})
    preview = d.sort_values("OrderDate", ascending=False).head(20)
    table = html.Table([
        html.Thead(html.Tr([html.Th(c, style={"textAlign": "left", "padding": "9px",
                                              "borderBottom": "1px solid #ddd"}) for c in
                            ["OrderID", "OrderDate", "Country", "Product", "Quantity", "Revenue"]])),
        html.Tbody([html.Tr([
            html.Td(str(row[c])[:19] if c == "OrderDate" else
                    (f"£{row[c]:,.2f}" if c == "Revenue" else str(row[c])),
                    style={"padding": "9px", "borderBottom": "1px solid #eee"})
            for c in ["OrderID", "OrderDate", "Country", "Product", "Quantity", "Revenue"]])
            for _, row in preview.iterrows()])
    ], style={"width": "100%", "background": "white", "borderCollapse": "collapse",
              "borderRadius": "8px"})
    for fig in [trend, prod_fig, country_fig, cust_fig]:
        fig.update_layout(template="plotly_white", margin=dict(l=25, r=20, t=60, b=35))
    return kpis, trend, prod_fig, country_fig, cust_fig, table

if __name__ == "__main__":
    app.run(debug=True)
