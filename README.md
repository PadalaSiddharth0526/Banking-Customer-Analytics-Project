# 🏦 Banking Customer Analytics Project

An end-to-end customer analytics project for the retail banking sector,
built entirely in **Python and SQL** (no Power BI / Tableau). Covers data
cleaning, EDA, SQL analysis, customer segmentation, churn analysis, revenue
estimation, and an interactive Streamlit dashboard - modeled on the kind of
analysis a Data Analyst would deliver at a global bank (UBS, JPMorgan,
Goldman Sachs, Wells Fargo).

---

## Business Problem

A retail bank operating across France, Germany, and Spain wants to understand:

- Who are our customers, and how do they differ across markets?
- Which customers are most likely to churn, and why?
- Which segments generate the most revenue, and where is the growth headroom?
- What concrete, data-backed actions should Retention, Marketing, and Product
  teams take in the next quarter?

This project answers all four questions using a single, reproducible
Python + SQL pipeline and a live interactive dashboard.

---

## Dataset

This project uses a **synthetic dataset generated to exactly match the
schema and statistical structure** of the widely-used public "Bank Customer
Churn" dataset (10,000 customers; columns: `CustomerId`, `Surname`,
`CreditScore`, `Geography`, `Gender`, `Age`, `Tenure`, `Balance`,
`NumOfProducts`, `HasCrCard`, `IsActiveMember`, `EstimatedSalary`, `Exited`).

> **Why synthetic?** This sandbox environment has no network access to
> Kaggle. `src/generate_raw_data.py` reproduces the same schema, realistic
> value distributions, and genuine churn correlations (older, inactive,
> single-product customers churn more - a pattern well documented in the
> real dataset), and seeds realistic messiness (nulls, duplicates,
> inconsistent casing, currency-formatted strings, impossible outliers) so
> the cleaning pipeline has real work to do.
>
> **To use the original dataset instead:** download it from Kaggle and
> save it as `data/raw/bank_customers_raw.csv` with the same column names -
> every downstream script works unchanged.

---

## Tech Stack

| Layer | Tools |
|---|---|
| Language | Python 3.10+ |
| Data manipulation | Pandas, NumPy |
| Database | SQLite (drop-in path to PostgreSQL - see `src/database.py`) |
| SQL | JOINs, GROUP BY, HAVING, CASE, Window Functions, CTEs, Views |
| Visualization (static) | Matplotlib |
| Visualization (interactive) | Plotly |
| Dashboard | Streamlit |
| Testing | Pytest |
| Version control | Git |

No Power BI, no Tableau - every chart, KPI, and filter is custom Python/SQL.

---

## Project Architecture

```
Raw CSV  →  Cleaning Pipeline  →  Segmentation  →  Revenue Estimation
   │              │                    │                  │
   └──────────────┴────────────────────┴──────────────────┘
                          │
                 Analytics-ready CSV
                          │
              ┌───────────┴────────────┐
              │                        │
        SQLite Database         Static EDA Charts
     (sql/*.sql scripts)           (images/*.png)
              │                        │
              └───────────┬────────────┘
                          │
                Streamlit Dashboard
              (dashboard/app.py)
```

Each stage is a standalone, testable, importable Python module in `src/` -
there is no hidden logic duplicated between the notebooks, the dashboard,
and the SQL layer; all three consume the same functions/tables.

---

## Folder Structure

```
banking-customer-analytics/
├── data/
│   ├── raw/                     # raw (messy) source data
│   └── processed/                # cleaned / segmented / revenue-augmented CSVs + SQLite DB
├── sql/
│   ├── 01_schema.sql              # PostgreSQL reference schema (DDL, constraints, indexes)
│   ├── 02_business_queries.sql    # 17 business questions: JOINs, CTEs, window fns, CASE, HAVING
│   └── 03_views.sql               # reusable reporting views
├── notebooks/
│   ├── 01_data_cleaning_eda.ipynb
│   ├── 02_segmentation_churn_revenue.ipynb
│   └── build_notebooks.py         # regenerates the notebooks programmatically
├── src/
│   ├── generate_raw_data.py       # synthetic raw dataset generator
│   ├── data_cleaning.py           # missing values, duplicates, dtypes, outliers, validation
│   ├── segmentation.py            # value / life-stage / risk segmentation logic
│   ├── churn_analysis.py          # churn breakdowns + driver ranking
│   ├── revenue_analysis.py        # documented revenue-proxy model
│   ├── visualization.py           # Matplotlib (static) + Plotly (interactive) chart builders
│   ├── database.py                # SQLite loader + SQL script runner
│   └── utils/logger.py            # shared logging config
├── dashboard/
│   └── app.py                     # Streamlit interactive dashboard
├── reports/
│   ├── business_insights.md       # 22 data-backed business insights
│   └── logs/                      # pipeline run logs
├── images/                        # generated static EDA charts (PNG)
├── tests/
│   └── test_pipeline.py           # pytest unit tests for cleaning/segmentation/churn/revenue
├── run_pipeline.py                 # single entry point: runs the entire pipeline
├── requirements.txt
└── README.md
```

---

## Installation & Quick Start

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd banking-customer-analytics

# 2. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the full pipeline (generates data, cleans it, segments, scores
#    revenue, builds charts, builds the SQL database)
python run_pipeline.py

# 5. Launch the interactive dashboard
streamlit run dashboard/app.py
```

Open the URL Streamlit prints (typically `http://localhost:8501`) to
explore the dashboard.

### Running the notebooks

```bash
jupyter notebook notebooks/01_data_cleaning_eda.ipynb
jupyter notebook notebooks/02_segmentation_churn_revenue.ipynb
```

### Running the SQL analysis directly

```bash
sqlite3 data/processed/banking_analytics.db
sqlite> SELECT * FROM vw_country_summary;
sqlite> SELECT * FROM vw_churn_risk_watchlist ORDER BY churn_risk_score DESC LIMIT 10;
```

### Running tests

```bash
pytest tests/ -v
```

---

## SQL Documentation

- **`01_schema.sql`** - authoritative table schema with `CHECK` constraints
  and indexes, written for PostgreSQL. The project loads data via pandas
  for zero-setup portability, so this file serves as the schema-of-record
  if you deploy to a real Postgres instance.
- **`02_business_queries.sql`** - 17 business questions covering total
  customers, average balance/salary, customers by country/gender, churn
  rate, active-customer %, top 10 high-value customers, average credit
  score by country (with `HAVING`), revenue by segment (with a `JOIN` to a
  product-catalog dimension table), multi-product customers, at-risk
  customers (`CASE`-based composite scoring), country KPIs (`CTE` +
  `RANK()` window function), balance percentiles (`PERCENT_RANK`,
  `NTILE`), running revenue (`SUM() OVER`), churn by tenure band, and a
  combined "high-value + high-risk" retention priority list.
- **`03_views.sql`** - four reusable views (`vw_country_summary`,
  `vw_segment_summary`, `vw_churn_risk_watchlist`, `vw_premium_customers`)
  used by the dashboard and available for any future BI tool.

---

## Customer Segmentation Logic

| Segment | Definition | Business Rationale |
|---|---|---|
| **High-Value** | Balance ≥ 75th percentile, OR ≥ 25th percentile with 2+ products | Deposits are the capital a bank lends against; multi-product customers are more deeply embedded |
| **Medium-Value** | Balance between 25th-75th percentile | Core, stable customer base |
| **Low-Value** | Balance below 25th percentile | Smallest deposit relationships |
| **Young Professional** | Age < 35 | Early-career growth potential |
| **Established** | Age 35-59 | Peak earning / peak product-need years |
| **Senior** | Age 60+ | Retirement-transition needs; highest churn risk |
| **High-Risk** | Inactive member AND single product | The two strongest churn predictors, combined |
| **Premium** | Top-decile balance AND active AND has credit card | Wealth/private-banking candidates |

Full implementation and docstrings: `src/segmentation.py`.

---

## Sample Outputs

Static EDA charts are generated to `images/` by `src/visualization.py`, e.g.:

- `images/geography_distribution.png` - customers by country
- `images/age_distribution.png` - age histogram
- `images/churn_by_geography.png` - churn rate by country
- `images/active_vs_inactive.png` - activity split
- `images/products_owned.png` - product ownership distribution

The Streamlit dashboard additionally renders all of these as interactive
Plotly charts with live filtering by country, gender, age, segment, and
product count.

---

## Business Insights

See **[`reports/business_insights.md`](reports/business_insights.md)** for
22 data-backed insights covering churn drivers, revenue concentration,
and segmentation, plus a top-3 leadership action list. Headline numbers:

- **Overall churn rate: 32.6%**
- **Estimated total annual revenue: ~$17.85M**
- **Strongest churn driver: age (Seniors churn 2.7x more than 18-29s)**
- **High-Value customers generate ~77% of total revenue with 6,180 customers (62% of the base)**

---

## Code Quality

- Modular functions with type hints and docstrings throughout `src/`
- Centralized logging (`src/utils/logger.py`) instead of print statements
- Explicit exception handling with actionable error messages (e.g. missing
  raw data file)
- 12 unit tests covering cleaning, segmentation, churn, and revenue logic
  (`pytest tests/ -v`)
- No duplicated business logic between notebooks, SQL, and the dashboard -
  all three call the same `src/` functions or query the same database

---

## Future Improvements

- Swap the revenue proxy model for real GL/profitability data if available
- Add a predictive churn model (e.g. logistic regression / gradient
  boosting) alongside the current transparent, explainable driver analysis
- Add a PostgreSQL Docker Compose setup for a full production-like local
  environment
- Add cohort-based retention curves (churn by acquisition month) once
  acquisition-date data is available
- CI pipeline (GitHub Actions) running `pytest` and `flake8` on every push

---

## Conclusion

This project demonstrates a complete, production-style Data Analyst
workflow for a banking use case: cleaning messy real-world-shaped data,
answering business questions in SQL, building explainable customer
segments, quantifying churn drivers, estimating revenue, and delivering
insights through both a written report and a live interactive dashboard -
all reproducible end-to-end with a single command (`python run_pipeline.py`).
#   B a n k i n g - C u s t o m e r - A n a l y t i c s - P r o j e c t  
 