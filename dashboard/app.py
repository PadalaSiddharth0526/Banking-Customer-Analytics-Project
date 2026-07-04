"""
dashboard/app.py
=================
Interactive Streamlit dashboard for the Banking Customer Analytics project.

Run with:
    streamlit run dashboard/app.py

The dashboard reads the final analytics-ready CSV (data/processed/
bank_customers_revenue.csv) - run the pipeline first via:
    python -m src.data_cleaning
    python -m src.segmentation
    python -m src.revenue_analysis
or simply: python run_pipeline.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Allow running via `streamlit run dashboard/app.py` from repo root or dashboard/
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.visualization import (
    plotly_age_histogram,
    plotly_balance_vs_salary_scatter,
    plotly_churn_by_dimension,
    plotly_churn_donut,
    plotly_credit_score_box,
    plotly_geography_bar,
    plotly_revenue_by_country,
    plotly_segment_treemap,
)
from src.churn_analysis import churn_by_dimension

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "bank_customers_revenue.csv"

st.set_page_config(
    page_title="Banking Customer Analytics",
    page_icon="🏦",
    layout="wide",
)


@st.cache_data
def load_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        st.error(
            "Processed data not found. Run the pipeline first:\n\n"
            "`python run_pipeline.py`"
        )
        st.stop()
    return pd.read_csv(DATA_PATH)


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filters")

    countries = st.sidebar.multiselect(
        "Country", options=sorted(df["Geography"].unique()), default=list(df["Geography"].unique())
    )
    genders = st.sidebar.multiselect(
        "Gender", options=sorted(df["Gender"].unique()), default=list(df["Gender"].unique())
    )
    age_range = st.sidebar.slider(
        "Age range", int(df["Age"].min()), int(df["Age"].max()),
        (int(df["Age"].min()), int(df["Age"].max())),
    )
    segments = st.sidebar.multiselect(
        "Customer Segment", options=sorted(df["ValueSegment"].unique()), default=list(df["ValueSegment"].unique())
    )
    products = st.sidebar.multiselect(
        "Product Count", options=sorted(df["NumOfProducts"].unique()), default=list(df["NumOfProducts"].unique())
    )

    filtered = df[
        df["Geography"].isin(countries)
        & df["Gender"].isin(genders)
        & df["Age"].between(age_range[0], age_range[1])
        & df["ValueSegment"].isin(segments)
        & df["NumOfProducts"].isin(products)
    ]

    if filtered.empty:
        st.sidebar.warning("No customers match the selected filters.")
    return filtered


def render_kpis(df: pd.DataFrame) -> None:
    total = len(df)
    active = int(df["IsActiveMember"].sum())
    churn_rate = df["Exited"].mean() * 100 if total else 0
    avg_balance = df["Balance"].mean() if total else 0
    avg_credit = df["CreditScore"].mean() if total else 0
    revenue = df["EstimatedAnnualRevenue"].sum() if total else 0

    cols = st.columns(6)
    cols[0].metric("Total Customers", f"{total:,}")
    cols[1].metric("Active Customers", f"{active:,}", f"{100 * active / total:.1f}%" if total else "0%")
    cols[2].metric("Churn Rate", f"{churn_rate:.1f}%")
    cols[3].metric("Avg Balance", f"${avg_balance:,.0f}")
    cols[4].metric("Avg Credit Score", f"{avg_credit:.0f}")
    cols[5].metric("Est. Annual Revenue", f"${revenue:,.0f}")


def main() -> None:
    st.title("🏦 Banking Customer Analytics Dashboard")
    st.caption(
        "Customer demographics, churn drivers, revenue, and segmentation - "
        "built with Python, SQL, Pandas, Plotly, and Streamlit."
    )

    df_full = load_data()
    df = apply_filters(df_full)

    render_kpis(df)
    st.divider()

    tab_overview, tab_churn, tab_revenue, tab_segments = st.tabs(
        ["📊 Customer Overview", "⚠️ Churn Analysis", "💰 Revenue Analysis", "🎯 Segmentation"]
    )

    with tab_overview:
        c1, c2 = st.columns(2)
        c1.plotly_chart(plotly_geography_bar(df), use_container_width=True)
        c2.plotly_chart(plotly_age_histogram(df), use_container_width=True)

        c3, c4 = st.columns(2)
        c3.plotly_chart(plotly_credit_score_box(df), use_container_width=True)
        c4.plotly_chart(plotly_balance_vs_salary_scatter(df), use_container_width=True)

    with tab_churn:
        c1, c2 = st.columns([1, 2])
        c1.plotly_chart(plotly_churn_donut(df), use_container_width=True)

        churn_geo = churn_by_dimension(df, "Geography")
        c2.plotly_chart(
            plotly_churn_by_dimension(churn_geo, "Geography", "Churn Rate by Country"),
            use_container_width=True,
        )

        c3, c4 = st.columns(2)
        churn_age = churn_by_dimension(
            df, "Age", bins=[17, 29, 39, 49, 59, 100], labels=["18-29", "30-39", "40-49", "50-59", "60+"]
        )
        c3.plotly_chart(
            plotly_churn_by_dimension(churn_age, "AgeBand", "Churn Rate by Age Group"),
            use_container_width=True,
        )
        churn_products = churn_by_dimension(df, "NumOfProducts")
        c4.plotly_chart(
            plotly_churn_by_dimension(churn_products, "NumOfProducts", "Churn Rate by Product Count"),
            use_container_width=True,
        )

        st.subheader("Highest Churn-Risk Customers (still active relationships)")
        risk_df = df[df["Exited"] == 0].copy()
        risk_df["ChurnRiskScore"] = (
            (risk_df["IsActiveMember"] == 0).astype(int) * 2
            + (risk_df["NumOfProducts"] == 1).astype(int) * 2
            + (risk_df["Age"] >= 50).astype(int)
            + (risk_df["Balance"] == 0).astype(int)
        )
        st.dataframe(
            risk_df.sort_values("ChurnRiskScore", ascending=False)
            [["CustomerId", "Surname", "Geography", "Age", "NumOfProducts", "Balance", "ChurnRiskScore"]]
            .head(15),
            use_container_width=True, hide_index=True,
        )

    with tab_revenue:
        c1, c2 = st.columns(2)
        revenue_country = (
            df.groupby("Geography", observed=True)["EstimatedAnnualRevenue"].sum().reset_index()
            .rename(columns={"EstimatedAnnualRevenue": "total_revenue"})
        )
        c1.plotly_chart(plotly_revenue_by_country(revenue_country), use_container_width=True)
        c2.plotly_chart(plotly_segment_treemap(df), use_container_width=True)

        st.subheader("Revenue by Value Segment")
        seg_rev = (
            df.groupby("ValueSegment", observed=True)
            .agg(customers=("CustomerId", "count"), total_revenue=("EstimatedAnnualRevenue", "sum"),
                 avg_revenue=("EstimatedAnnualRevenue", "mean"))
            .round(2).reset_index()
        )
        st.dataframe(seg_rev, use_container_width=True, hide_index=True)

    with tab_segments:
        c1, c2 = st.columns(2)
        c1.bar_chart(df["ValueSegment"].value_counts())
        c2.bar_chart(df["LifeStageSegment"].value_counts())

        st.subheader("Segment Deep Dive")
        seg_summary = (
            df.groupby(["ValueSegment", "LifeStageSegment"], observed=True)
            .agg(customers=("CustomerId", "count"), churn_rate=("Exited", "mean"),
                 avg_balance=("Balance", "mean"), total_revenue=("EstimatedAnnualRevenue", "sum"))
            .round(3).reset_index()
        )
        st.dataframe(seg_summary, use_container_width=True, hide_index=True)

        st.metric("High-Risk Customers", int(df["HighRiskChurn"].sum()))
        st.metric("Premium Customers", int(df["PremiumCustomer"].sum()))

    st.divider()
    st.caption("Banking Customer Analytics Project · Built with Python, SQL, Pandas, Plotly & Streamlit")


if __name__ == "__main__":
    main()
