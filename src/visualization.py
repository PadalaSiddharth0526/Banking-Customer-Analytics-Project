"""
visualization.py
=================
Reusable chart builders used by both the static EDA notebook/report
(Matplotlib, saved as PNGs into images/) and the interactive Streamlit
dashboard (Plotly, rendered live).

Keeping chart-building logic here (rather than duplicated inline in the
notebook and the dashboard) keeps the project DRY and testable.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless rendering
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.utils.logger import get_logger

logger = get_logger(__name__)

IMAGES_DIR = Path("images")
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

plt.style.use("seaborn-v0_8-whitegrid")
PALETTE = ["#0f4c81", "#4f9dcf", "#8fc1e3", "#f2a154", "#e26d5c", "#6b5b95"]


# --------------------------------------------------------------------------
# Static Matplotlib charts (EDA -> images/*.png for README/reports)
# --------------------------------------------------------------------------

def save_gender_distribution(df: pd.DataFrame, path: Path = IMAGES_DIR / "gender_distribution.png") -> None:
    counts = df["Gender"].value_counts()
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.pie(counts.values, labels=counts.index, autopct="%1.1f%%", colors=PALETTE[:2], startangle=90)
    ax.set_title("Customer Gender Distribution")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    logger.info("Saved %s", path)


def save_age_distribution(df: pd.DataFrame, path: Path = IMAGES_DIR / "age_distribution.png") -> None:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.hist(df["Age"], bins=30, color=PALETTE[0], edgecolor="white")
    ax.set_title("Customer Age Distribution")
    ax.set_xlabel("Age")
    ax.set_ylabel("Number of Customers")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    logger.info("Saved %s", path)


def save_geography_distribution(df: pd.DataFrame, path: Path = IMAGES_DIR / "geography_distribution.png") -> None:
    counts = df["Geography"].value_counts()
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.bar(counts.index, counts.values, color=PALETTE[:len(counts)])
    ax.set_title("Customers by Country")
    ax.set_ylabel("Number of Customers")
    for i, v in enumerate(counts.values):
        ax.text(i, v + 30, str(v), ha="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    logger.info("Saved %s", path)


def save_balance_distribution(df: pd.DataFrame, path: Path = IMAGES_DIR / "balance_distribution.png") -> None:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.hist(df["Balance"], bins=40, color=PALETTE[1], edgecolor="white")
    ax.set_title("Account Balance Distribution")
    ax.set_xlabel("Balance")
    ax.set_ylabel("Number of Customers")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    logger.info("Saved %s", path)


def save_credit_score_distribution(df: pd.DataFrame, path: Path = IMAGES_DIR / "credit_score_distribution.png") -> None:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.hist(df["CreditScore"], bins=30, color=PALETTE[3], edgecolor="white")
    ax.set_title("Credit Score Distribution")
    ax.set_xlabel("Credit Score")
    ax.set_ylabel("Number of Customers")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    logger.info("Saved %s", path)


def save_churn_by_geography(df: pd.DataFrame, path: Path = IMAGES_DIR / "churn_by_geography.png") -> None:
    rates = df.groupby("Geography", observed=True)["Exited"].mean().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.bar(rates.index, rates.values * 100, color=PALETTE[4])
    ax.set_title("Churn Rate by Country")
    ax.set_ylabel("Churn Rate (%)")
    for i, v in enumerate(rates.values):
        ax.text(i, v * 100 + 0.5, f"{v * 100:.1f}%", ha="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    logger.info("Saved %s", path)


def save_active_vs_inactive(df: pd.DataFrame, path: Path = IMAGES_DIR / "active_vs_inactive.png") -> None:
    counts = df["IsActiveMember"].map({1: "Active", 0: "Inactive"}).value_counts()
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.pie(counts.values, labels=counts.index, autopct="%1.1f%%", colors=[PALETTE[0], PALETTE[4]], startangle=90)
    ax.set_title("Active vs Inactive Customers")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    logger.info("Saved %s", path)


def save_products_owned(df: pd.DataFrame, path: Path = IMAGES_DIR / "products_owned.png") -> None:
    counts = df["NumOfProducts"].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.bar(counts.index.astype(str), counts.values, color=PALETTE[2])
    ax.set_title("Number of Products Owned")
    ax.set_xlabel("Products Owned")
    ax.set_ylabel("Number of Customers")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    logger.info("Saved %s", path)


def generate_all_static_charts(df: pd.DataFrame) -> None:
    """Generate and save every static EDA chart used in the README/reports."""
    save_gender_distribution(df)
    save_age_distribution(df)
    save_geography_distribution(df)
    save_balance_distribution(df)
    save_credit_score_distribution(df)
    save_churn_by_geography(df)
    save_active_vs_inactive(df)
    save_products_owned(df)
    logger.info("All static charts generated in %s", IMAGES_DIR)


# --------------------------------------------------------------------------
# Interactive Plotly chart builders (used live by the Streamlit dashboard)
# --------------------------------------------------------------------------

def plotly_geography_bar(df: pd.DataFrame) -> go.Figure:
    counts = df["Geography"].value_counts().reset_index()
    counts.columns = ["Geography", "Customers"]
    fig = px.bar(counts, x="Geography", y="Customers", color="Geography",
                 color_discrete_sequence=PALETTE, title="Customers by Country")
    fig.update_layout(showlegend=False)
    return fig


def plotly_age_histogram(df: pd.DataFrame) -> go.Figure:
    fig = px.histogram(df, x="Age", nbins=30, color_discrete_sequence=[PALETTE[0]],
                        title="Age Distribution")
    return fig


def plotly_churn_donut(df: pd.DataFrame) -> go.Figure:
    counts = df["Exited"].map({1: "Churned", 0: "Retained"}).value_counts()
    fig = px.pie(values=counts.values, names=counts.index, hole=0.5,
                 color_discrete_sequence=[PALETTE[4], PALETTE[0]], title="Churn Overview")
    return fig


def plotly_churn_by_dimension(churn_df: pd.DataFrame, x_col: str, title: str) -> go.Figure:
    fig = px.bar(churn_df, x=x_col, y="churn_rate", color="churn_rate",
                 color_continuous_scale="Blues", title=title,
                 labels={"churn_rate": "Churn Rate"})
    fig.update_layout(yaxis_tickformat=".0%")
    return fig


def plotly_revenue_by_country(revenue_df: pd.DataFrame) -> go.Figure:
    fig = px.bar(revenue_df, x="Geography", y="total_revenue", color="Geography",
                 color_discrete_sequence=PALETTE, title="Estimated Revenue by Country")
    fig.update_layout(showlegend=False)
    return fig


def plotly_segment_treemap(df: pd.DataFrame) -> go.Figure:
    fig = px.treemap(
        df, path=["ValueSegment", "LifeStageSegment"], values="EstimatedAnnualRevenue",
        color="ValueSegment", color_discrete_sequence=PALETTE,
        title="Revenue by Value Segment & Life Stage",
    )
    return fig


def plotly_credit_score_box(df: pd.DataFrame) -> go.Figure:
    fig = px.box(df, x="Geography", y="CreditScore", color="Geography",
                 color_discrete_sequence=PALETTE, title="Credit Score Distribution by Country")
    fig.update_layout(showlegend=False)
    return fig


def plotly_balance_vs_salary_scatter(df: pd.DataFrame) -> go.Figure:
    sample = df.sample(min(2000, len(df)), random_state=1)
    fig = px.scatter(
        sample, x="EstimatedSalary", y="Balance", color="Exited",
        color_continuous_scale=["#4f9dcf", "#e26d5c"],
        title="Balance vs. Estimated Salary (colored by churn)",
        opacity=0.6,
    )
    return fig


if __name__ == "__main__":
    data_path = Path("data/processed/bank_customers_clean.csv")
    clean_df = pd.read_csv(data_path)
    generate_all_static_charts(clean_df)
