"""
churn_analysis.py
==================
Computes churn (attrition) metrics across every key customer dimension and
ranks the strongest drivers of churn using a simple, explainable lift
metric (churn rate of a subgroup vs. overall churn rate).

This intentionally avoids opaque ML models - for a portfolio / business
analytics project, transparent, explainable metrics are more valuable
and more defensible in a stakeholder presentation than a black-box model.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)

SEGMENTED_PATH = Path("data/processed/bank_customers_segmented.csv")


def overall_churn_rate(df: pd.DataFrame) -> float:
    return round(df["Exited"].mean(), 4)


def churn_by_dimension(df: pd.DataFrame, dimension: str, bins: list | None = None,
                        labels: list | None = None) -> pd.DataFrame:
    """Compute churn rate and customer count grouped by a given column.

    If `bins` is provided, the dimension is bucketed first (used for
    continuous fields like Age or Balance).
    """
    work = df.copy()
    group_col = dimension

    if bins is not None:
        group_col = f"{dimension}Band"
        work[group_col] = pd.cut(work[dimension], bins=bins, labels=labels)

    result = (
        work.groupby(group_col, observed=True)
        .agg(customers=("CustomerId", "count"), churned=("Exited", "sum"))
        .assign(churn_rate=lambda d: (d["churned"] / d["customers"]).round(4))
        .reset_index()
        .sort_values("churn_rate", ascending=False)
    )
    return result


def churn_driver_ranking(df: pd.DataFrame) -> pd.DataFrame:
    """Rank categorical/binary churn drivers by lift over the overall churn rate.

    Lift > 1 means the subgroup churns more than the base rate; lift < 1
    means it churns less. This gives a single comparable score across very
    different dimensions (geography, activity, product count, etc.).
    """
    base_rate = overall_churn_rate(df)
    rows = []

    dimension_specs = [
        ("Geography", None),
        ("Gender", None),
        ("IsActiveMember", None),
        ("NumOfProducts", None),
        ("HasCrCard", None),
        ("LifeStageSegment", None) if "LifeStageSegment" in df.columns else None,
    ]

    for spec in dimension_specs:
        if spec is None:
            continue
        col, _ = spec
        grouped = df.groupby(col, observed=True)["Exited"].agg(["mean", "count"])
        for level, r in grouped.iterrows():
            rows.append(
                {
                    "dimension": col,
                    "segment": level,
                    "customers": int(r["count"]),
                    "churn_rate": round(r["mean"], 4),
                    "lift_vs_overall": round(r["mean"] / base_rate, 2) if base_rate else None,
                }
            )

    ranking = pd.DataFrame(rows).sort_values("lift_vs_overall", ascending=False).reset_index(drop=True)
    return ranking


def full_churn_report(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Build the complete set of churn breakdowns used in the dashboard/report."""
    logger.info("Building full churn analysis report")

    report = {
        "overall_rate": overall_churn_rate(df),
        "by_geography": churn_by_dimension(df, "Geography"),
        "by_gender": churn_by_dimension(df, "Gender"),
        "by_age_band": churn_by_dimension(
            df, "Age", bins=[17, 29, 39, 49, 59, 100], labels=["18-29", "30-39", "40-49", "50-59", "60+"]
        ),
        "by_balance_band": churn_by_dimension(
            df, "Balance",
            bins=[-1, 0, 50000, 100000, 150000, 1_000_000],
            labels=["Zero", "1-50K", "50-100K", "100-150K", "150K+"],
        ),
        "by_products": churn_by_dimension(df, "NumOfProducts"),
        "by_tenure": churn_by_dimension(
            df, "Tenure", bins=[-1, 2, 5, 8, 15], labels=["0-2 yrs", "3-5 yrs", "6-8 yrs", "9+ yrs"]
        ),
        "by_activity": churn_by_dimension(df, "IsActiveMember"),
        "driver_ranking": churn_driver_ranking(df),
    }

    logger.info("Overall churn rate: %.2f%%", report["overall_rate"] * 100)
    return report


RETENTION_RECOMMENDATIONS = [
    {
        "driver": "Inactive membership",
        "insight": "Inactive members churn at roughly double the rate of active members.",
        "recommendation": "Launch a re-engagement campaign (app nudges, fee waivers, "
                           "personal banker outreach) for members inactive 60+ days.",
    },
    {
        "driver": "Single product ownership",
        "insight": "Customers holding only one product churn far more than those with 2 products.",
        "recommendation": "Prioritize cross-sell offers (savings account, credit card, "
                           "investment product) to single-product customers in their first 12 months.",
    },
    {
        "driver": "Germany geography",
        "insight": "German customers show a meaningfully higher churn rate than France or Spain.",
        "recommendation": "Commission a local NPS/satisfaction study in Germany; benchmark "
                           "local competitor rates and fees.",
    },
    {
        "driver": "Age 50+",
        "insight": "Churn rises steadily with age, peaking in the 50-59 band.",
        "recommendation": "Build a dedicated retirement/wealth-transition advisory track "
                           "for customers approaching retirement age.",
    },
    {
        "driver": "Zero-balance accounts",
        "insight": "Customers holding a zero balance churn more than any other balance band, "
                    "suggesting these are dormant or 'parked' relationships at high flight risk.",
        "recommendation": "Trigger an automated low/zero-balance alert workflow that offers a "
                           "starter savings incentive or check-in call before the relationship lapses.",
    },
]


if __name__ == "__main__":
    segmented_df = pd.read_csv(SEGMENTED_PATH)
    churn_report = full_churn_report(segmented_df)
    for key, value in churn_report.items():
        print(f"\n--- {key} ---")
        print(value)
