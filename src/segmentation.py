"""
segmentation.py
================
Rule-based customer segmentation for banking analytics.

Segments produced (a customer can belong to more than one, since they
answer different business questions - value tier vs. life-stage vs. risk):

    Value tier (mutually exclusive):
        - High-Value:   Balance >= 75th percentile AND NumOfProducts >= 2
        - Medium-Value: Balance between 25th-75th percentile
        - Low-Value:    Balance < 25th percentile

    Life-stage (mutually exclusive):
        - Young Professional: Age < 35
        - Established:        35 <= Age < 60
        - Senior:             Age >= 60

    Risk / behavioral flags (independent boolean flags):
        - High-Risk (of churn): inactive member AND single product
        - Premium: top decile of Balance AND has credit card AND active member

The thresholds are computed dynamically from the dataset's own
distribution (percentiles) rather than hard-coded, so the logic remains
valid if the dataset changes size or currency.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)

CLEAN_PATH = Path("data/processed/bank_customers_clean.csv")
SEGMENTED_PATH = Path("data/processed/bank_customers_segmented.csv")


def add_value_segment(df: pd.DataFrame) -> pd.DataFrame:
    """Classify customers into High/Medium/Low value tiers.

    Business logic: 'value' to the bank is driven primarily by the funds a
    customer keeps on deposit (Balance) - this is the capital the bank can
    lend against or invest. Customers who additionally hold 2+ products are
    more deeply embedded and promoted to High-Value even if their balance
    sits at the boundary, since cross-sold customers carry higher lifetime
    value and are costlier for competitors to poach.
    """
    df = df.copy()
    p25, p75 = df["Balance"].quantile([0.25, 0.75])

    def _classify(row) -> str:
        if row["Balance"] >= p75 or (row["Balance"] >= p25 and row["NumOfProducts"] >= 2):
            return "High-Value"
        elif row["Balance"] >= p25:
            return "Medium-Value"
        return "Low-Value"

    df["ValueSegment"] = df.apply(_classify, axis=1)
    return df


def add_life_stage_segment(df: pd.DataFrame) -> pd.DataFrame:
    """Classify customers into life-stage bands used for marketing targeting."""
    df = df.copy()
    bins = [0, 34, 59, 150]
    labels = ["Young Professional", "Established", "Senior"]
    df["LifeStageSegment"] = pd.cut(df["Age"], bins=bins, labels=labels)
    return df


def add_risk_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Add independent boolean segment flags: HighRisk and Premium."""
    df = df.copy()

    # High-Risk: inactive + only one product -> the two strongest churn
    # predictors identified in the churn-driver analysis (see churn_analysis.py)
    df["HighRiskChurn"] = (df["IsActiveMember"] == 0) & (df["NumOfProducts"] == 1)

    # Premium: top 10% balance, holds a credit card, and currently active -
    # the profile the bank most wants to retain and upsell (wealth/private
    # banking candidates).
    p90 = df["Balance"].quantile(0.90)
    df["PremiumCustomer"] = (
        (df["Balance"] >= p90) & (df["HasCrCard"] == 1) & (df["IsActiveMember"] == 1)
    )
    return df


def build_segments(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the full segmentation suite to a cleaned customer DataFrame."""
    logger.info("Building customer segments")
    df = add_value_segment(df)
    df = add_life_stage_segment(df)
    df = add_risk_flags(df)

    logger.info("Value segment distribution:\n%s", df["ValueSegment"].value_counts())
    logger.info("Life-stage distribution:\n%s", df["LifeStageSegment"].value_counts())
    logger.info("High-risk customers: %d (%.1f%%)", df["HighRiskChurn"].sum(),
                100 * df["HighRiskChurn"].mean())
    logger.info("Premium customers: %d (%.1f%%)", df["PremiumCustomer"].sum(),
                100 * df["PremiumCustomer"].mean())
    return df


def segment_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    """Produce a summary table of key metrics per value segment (for reports/dashboard)."""
    return (
        df.groupby("ValueSegment", observed=True)
        .agg(
            customers=("CustomerId", "count"),
            avg_balance=("Balance", "mean"),
            avg_credit_score=("CreditScore", "mean"),
            churn_rate=("Exited", "mean"),
            avg_products=("NumOfProducts", "mean"),
        )
        .round(2)
        .sort_values("avg_balance", ascending=False)
        .reset_index()
    )


if __name__ == "__main__":
    clean_df = pd.read_csv(CLEAN_PATH)
    segmented_df = build_segments(clean_df)
    SEGMENTED_PATH.parent.mkdir(parents=True, exist_ok=True)
    segmented_df.to_csv(SEGMENTED_PATH, index=False)
    logger.info("Saved segmented dataset to %s", SEGMENTED_PATH)
    print(segment_summary_table(segmented_df))
