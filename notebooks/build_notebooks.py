"""
build_notebooks.py
===================
Generates the project's Jupyter notebooks programmatically. Run once to
(re)create notebooks/01_data_cleaning_eda.ipynb and
notebooks/02_segmentation_churn_revenue.ipynb.

Usage:
    python notebooks/build_notebooks.py
"""

import nbformat as nbf


def make_cell(kind: str, source: str):
    if kind == "md":
        return nbf.v4.new_markdown_cell(source)
    return nbf.v4.new_code_cell(source)


def build_notebook_01():
    nb = nbf.v4.new_notebook()
    cells = [
        ("md", "# 01 - Data Cleaning & Exploratory Data Analysis\n"
                "Banking Customer Analytics Project\n\n"
                "This notebook loads the raw synthetic banking dataset, walks through the "
                "full cleaning pipeline (missing values, duplicates, formatting, dtypes, "
                "outliers, validation), and explores the cleaned data across demographics, "
                "geography, balances, credit scores, and product ownership."),
        ("code", "import sys\nsys.path.append('..')\n\n"
                 "import pandas as pd\nimport matplotlib.pyplot as plt\n\n"
                 "from src.data_cleaning import run_cleaning_pipeline\n"
                 "from src import visualization as viz\n\n"
                 "pd.set_option('display.max_columns', None)"),
        ("md", "## Load raw data and inspect quality issues"),
        ("code", "raw_df = pd.read_csv('../data/raw/bank_customers_raw.csv')\n"
                 "print(raw_df.shape)\nraw_df.head()"),
        ("code", "raw_df.isna().sum()"),
        ("code", "raw_df.duplicated().sum()"),
        ("md", "## Run the full cleaning pipeline\n"
                "See `src/data_cleaning.py` for the implementation of every step."),
        ("code", "clean_df, report = run_cleaning_pipeline(\n"
                 "    raw_path='../data/raw/bank_customers_raw.csv',\n"
                 "    output_path='../data/processed/bank_customers_clean.csv'\n"
                 ")\n"
                 "print(report.summary())"),
        ("code", "clean_df.head()"),
        ("md", "## Exploratory Data Analysis\n### Demographics: Gender & Age"),
        ("code", "clean_df['Gender'].value_counts(normalize=True).round(3) * 100"),
        ("code", "clean_df['Age'].describe()"),
        ("code", "fig, ax = plt.subplots(figsize=(7,4))\n"
                 "ax.hist(clean_df['Age'], bins=30, color='#0f4c81', edgecolor='white')\n"
                 "ax.set_title('Age Distribution')\nax.set_xlabel('Age')\nplt.show()"),
        ("md", "### Geography"),
        ("code", "clean_df['Geography'].value_counts()"),
        ("md", "### Account Balance"),
        ("code", "clean_df['Balance'].describe()"),
        ("code", "(clean_df['Balance'] == 0).sum(), (clean_df['Balance'] == 0).mean().round(3)"),
        ("md", "### Credit Score"),
        ("code", "clean_df['CreditScore'].describe()"),
        ("md", "### Estimated Salary"),
        ("code", "clean_df['EstimatedSalary'].describe()"),
        ("md", "### Products Owned"),
        ("code", "clean_df['NumOfProducts'].value_counts().sort_index()"),
        ("md", "### Active vs Inactive Customers"),
        ("code", "clean_df['IsActiveMember'].value_counts(normalize=True).round(3) * 100"),
        ("md", "## Generate all static report charts (saved to ../images/)"),
        ("code", "import os\nos.chdir('..')\nviz.generate_all_static_charts(clean_df)\nos.chdir('notebooks')"),
        ("md", "## Key EDA Takeaways\n"
                "- The dataset spans three European markets (France, Germany, Spain) with "
                "France representing roughly half the customer base.\n"
                "- Age is right-skewed, with most customers between 30-50 and a smaller "
                "senior population (60+) that, as later analysis shows, churns disproportionately.\n"
                "- Around a third of customers hold a zero balance, an important segment for "
                "targeted engagement.\n"
                "- Credit scores are approximately normally distributed around the mid-600s, "
                "typical of a mainstream retail banking population.\n"
                "- Most customers hold 1-2 products; very few hold 3-4, representing a "
                "cross-sell growth opportunity explored in the segmentation notebook."),
    ]
    nb["cells"] = [make_cell(k, s) for k, s in cells]
    return nb


def build_notebook_02():
    nb = nbf.v4.new_notebook()
    cells = [
        ("md", "# 02 - Segmentation, Churn & Revenue Analysis\n"
                "Banking Customer Analytics Project\n\n"
                "This notebook builds customer segments, analyzes churn drivers, "
                "estimates revenue, and surfaces the business insights used in the "
                "final report and dashboard."),
        ("code", "import sys\nsys.path.append('..')\n\nimport pandas as pd\n\n"
                 "from src.segmentation import build_segments, segment_summary_table\n"
                 "from src.churn_analysis import full_churn_report, RETENTION_RECOMMENDATIONS\n"
                 "from src.revenue_analysis import full_revenue_report\n\n"
                 "pd.set_option('display.max_columns', None)"),
        ("code", "clean_df = pd.read_csv('../data/processed/bank_customers_clean.csv')\n"
                 "clean_df.shape"),
        ("md", "## Customer Segmentation\n"
                "See `src/segmentation.py` docstrings for the full business logic behind "
                "each segment."),
        ("code", "segmented_df = build_segments(clean_df)\n"
                 "segmented_df.to_csv('../data/processed/bank_customers_segmented.csv', index=False)\n"
                 "segment_summary_table(segmented_df)"),
        ("code", "segmented_df['LifeStageSegment'].value_counts()"),
        ("code", "segmented_df[['HighRiskChurn', 'PremiumCustomer']].mean().round(3) * 100"),
        ("md", "## Churn Analysis"),
        ("code", "churn_report = full_churn_report(segmented_df)\n"
                 "print('Overall churn rate:', round(churn_report['overall_rate']*100, 2), '%')"),
        ("code", "churn_report['by_geography']"),
        ("code", "churn_report['by_age_band']"),
        ("code", "churn_report['by_products']"),
        ("code", "churn_report['by_tenure']"),
        ("code", "churn_report['driver_ranking'].head(10)"),
        ("md", "### Retention Recommendations"),
        ("code", "for rec in RETENTION_RECOMMENDATIONS:\n"
                 "    print('Driver:', rec['driver'])\n"
                 "    print(' Insight:', rec['insight'])\n"
                 "    print(' Recommendation:', rec['recommendation'])\n"
                 "    print()"),
        ("md", "## Revenue Analysis\n"
                "See `src/revenue_analysis.py` for the documented revenue-proxy assumptions."),
        ("code", "revenue_report, revenue_df = full_revenue_report(segmented_df)\n"
                 "revenue_df.to_csv('../data/processed/bank_customers_revenue.csv', index=False)\n"
                 "print('Total estimated annual revenue: $%.2f' % revenue_report['total_estimated_revenue'])"),
        ("code", "revenue_report['by_country']"),
        ("code", "revenue_report['by_value_segment']"),
        ("code", "revenue_report['by_age_group']"),
        ("code", "revenue_report['top_segments']"),
        ("md", "## Summary\n"
                "This notebook produced the analytics-ready dataset "
                "(`data/processed/bank_customers_revenue.csv`) that powers both the SQL "
                "database (`src/database.py`) and the Streamlit dashboard "
                "(`dashboard/app.py`). See `reports/business_insights.md` for the full "
                "list of 20+ data-backed business insights."),
    ]
    nb["cells"] = [make_cell(k, s) for k, s in cells]
    return nb


if __name__ == "__main__":
    nbf.write(build_notebook_01(), "notebooks/01_data_cleaning_eda.ipynb")
    nbf.write(build_notebook_02(), "notebooks/02_segmentation_churn_revenue.ipynb")
    print("Notebooks written to notebooks/")
