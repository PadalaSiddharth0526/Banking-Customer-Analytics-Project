"""
revenue_analysis.py
====================
Estimates per-customer annual revenue from available features, since the
dataset does not contain a direct revenue field (this mirrors real-world
banking analytics work, where revenue must often be modeled from account
attributes rather than read directly from a general ledger extract).

Revenue proxy model (documented so any reviewer can audit the assumption):
    - Net Interest Margin on deposits: 2.0% of Balance annually
      (approximates what a retail bank earns on customer deposits it re-lends)
    - Product/fee revenue: a flat annual fee-and-interchange estimate per
      product held (200 base, scaling with product count), reflecting
      account fees, card interchange, and cross-sold product margin
    - Credit card interchange: an additional flat amount if HasCrCard = 1
    - Active-member multiplier: active members transact more, generating
      ~15% more fee/interchange revenue than inactive members holding the
      same products

This is intentionally a simple, transparent proxy - in production this
would be replaced with actual GL/profitability data joined from the
bank's finance systems.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)

SEGMENTED_PATH = Path("data/processed/bank_customers_segmented.csv")
REVENUE_PATH = Path("data/processed/bank_customers_revenue.csv")

NIM_RATE = 0.02          # net interest margin earned on deposit balances
BASE_FEE_PER_PRODUCT = 200.0
CREDIT_CARD_BONUS = 120.0
ACTIVE_MULTIPLIER = 1.15


def estimate_annual_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """Add an `EstimatedAnnualRevenue` column using the documented proxy model."""
    df = df.copy()

    interest_revenue = df["Balance"] * NIM_RATE
    fee_revenue = df["NumOfProducts"] * BASE_FEE_PER_PRODUCT
    card_revenue = df["HasCrCard"] * CREDIT_CARD_BONUS
    multiplier = df["IsActiveMember"].map({1: ACTIVE_MULTIPLIER, 0: 1.0})

    df["EstimatedAnnualRevenue"] = (
        (interest_revenue + fee_revenue + card_revenue) * multiplier
    ).round(2)
    return df


def revenue_by(df: pd.DataFrame, dimension: str) -> pd.DataFrame:
    """Aggregate estimated revenue by a given categorical dimension."""
    return (
        df.groupby(dimension, observed=True)
        .agg(
            customers=("CustomerId", "count"),
            total_revenue=("EstimatedAnnualRevenue", "sum"),
            avg_revenue_per_customer=("EstimatedAnnualRevenue", "mean"),
        )
        .round(2)
        .sort_values("total_revenue", ascending=False)
        .reset_index()
    )


def revenue_by_age_group(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    work["AgeGroup"] = pd.cut(
        work["Age"], bins=[17, 29, 39, 49, 59, 100],
        labels=["18-29", "30-39", "40-49", "50-59", "60+"],
    )
    return revenue_by(work, "AgeGroup")


def top_revenue_segments(df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    """Identify which ValueSegment x LifeStageSegment combos generate the most revenue."""
    combo = (
        df.groupby(["ValueSegment", "LifeStageSegment"], observed=True)
        .agg(customers=("CustomerId", "count"), total_revenue=("EstimatedAnnualRevenue", "sum"))
        .round(2)
        .sort_values("total_revenue", ascending=False)
        .reset_index()
    )
    return combo.head(top_n)


def full_revenue_report(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    logger.info("Building full revenue analysis report")
    df = estimate_annual_revenue(df)

    report = {
        "total_estimated_revenue": round(df["EstimatedAnnualRevenue"].sum(), 2),
        "by_country": revenue_by(df, "Geography"),
        "by_value_segment": revenue_by(df, "ValueSegment"),
        "by_age_group": revenue_by_age_group(df),
        "by_product_count": revenue_by(df, "NumOfProducts"),
        "top_segments": top_revenue_segments(df),
    }
    logger.info("Total estimated annual revenue: $%.2f", report["total_estimated_revenue"])
    return report, df


if __name__ == "__main__":
    segmented_df = pd.read_csv(SEGMENTED_PATH)
    revenue_report, revenue_df = full_revenue_report(segmented_df)
    revenue_df.to_csv(REVENUE_PATH, index=False)
    logger.info("Saved revenue-augmented dataset to %s", REVENUE_PATH)
    for key, value in revenue_report.items():
        print(f"\n--- {key} ---")
        print(value)
