# Python + Dash Data Analytics Portfolio Projects

This package contains two independent Dash apps.

## Project 1 — E-Commerce Sales Analytics
- KPIs: revenue, completed orders, unique customers, average order value
- Filters: date range, country, product
- Charts: monthly revenue, product revenue, country revenue, top customers
- Data cleaning: duplicate IDs, missing values, invalid quantities, order status
- The default dataset is synthetic and is created automatically at `data/ecommerce_orders.csv`.

### 📸 Dashboard Preview
<p align="center">
  <img width="1900" height="927" alt="E-Commerce Dashboard" src="https://github.com/user-attachments/assets/674b3f35-bc47-4dcb-94de-9ac46ea78fc6" />
</p>

---

## Project 2 — F1 Race Performance Analytics
- KPIs: fastest filtered lap, average lap time, selected drivers, lap records
- Filters: drivers, tyre compound, lap range
- Charts: lap times, tyre compound comparisons, driver averages, stint analysis
- The app attempts to load 2024 Bahrain Grand Prix lap data using FastF1.
- If download fails, it creates clearly labelled synthetic demo data. Check the `Source` label in the app.

### 📸 Dashboard Previews
<p align="center">
  <img width="1588" height="677" alt="F1 Dashboard View 1" src="https://github.com/user-attachments/assets/718ec736-fd87-485f-9222-3d1eb4237f48" />
</p>
<p align="center">
  <img width="1632" height="577" alt="F1 Dashboard View 2" src="https://github.com/user-attachments/assets/37ed0020-5118-47b4-90d8-9d60bb335f53" />
</p>

---

## Setup (Windows / VS Code)
Open a terminal in either project folder and run:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python app.py
