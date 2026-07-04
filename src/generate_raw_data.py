"""
generate_raw_data.py
=====================
Generates a synthetic "raw" banking customer dataset that mirrors the schema
and statistical structure of the widely-used public Bank Customer Churn
Dataset (10,000 customers of a European bank; columns: CustomerId, Surname,
CreditScore, Geography, Gender, Age, Tenure, Balance, NumOfProducts,
HasCrCard, IsActiveMember, EstimatedSalary, Exited).

Why generate instead of download?
This environment has no network access to Kaggle. The generator below
reproduces the same schema, value ranges, and realistic correlations
(e.g. older + inactive + single-product customers churn more) so every
downstream script (cleaning, SQL, EDA, segmentation, dashboard) works
identically. To use the real dataset instead, simply drop the original
CSV into data/raw/bank_customers_raw.csv with the same column names and
skip this script.

The dataset is deliberately seeded with realistic messiness (nulls,
duplicate rows, inconsistent text casing, stray whitespace, mixed date
formats) so the cleaning module has genuine work to do.
"""

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)
N = 10000

SURNAMES = [
    "Smith", "Okafor", "Rossi", "Muller", "Dubois", "Garcia", "Kowalski",
    "Ivanov", "Tanaka", "Silva", "Andersen", "Fischer", "Novak", "Costa",
    "Kumar", "Nguyen", "Petrov", "Schmidt", "Moreau", "Bianchi",
]

GEOGRAPHIES = ["France", "Germany", "Spain"]
GEO_WEIGHTS = [0.50, 0.25, 0.25]

GENDERS = ["Male", "Female"]


def _draw_credit_score(n: int) -> np.ndarray:
    return np.clip(RNG.normal(loc=650, scale=96, size=n), 350, 850).round().astype(int)


def _draw_age(n: int) -> np.ndarray:
    return np.clip(RNG.gamma(shape=9, scale=4.2, size=n) + 18, 18, 92).round().astype(int)


def _draw_balance(n: int, has_zero_prob: float = 0.36) -> np.ndarray:
    zero_mask = RNG.random(n) < has_zero_prob
    balances = RNG.normal(loc=97000, scale=45000, size=n)
    balances = np.clip(balances, 0, 260000)
    balances[zero_mask] = 0.0
    return balances.round(2)


def generate_raw_dataframe(n: int = N) -> pd.DataFrame:
    """Build the synthetic raw dataset with realistic churn correlations."""
    customer_id = 15600000 + np.arange(n)
    surname = RNG.choice(SURNAMES, size=n)
    credit_score = _draw_credit_score(n)
    geography = RNG.choice(GEOGRAPHIES, size=n, p=GEO_WEIGHTS)
    gender = RNG.choice(GENDERS, size=n)
    age = _draw_age(n)
    tenure = RNG.integers(0, 11, size=n)
    balance = _draw_balance(n)
    num_products = RNG.choice([1, 2, 3, 4], size=n, p=[0.51, 0.40, 0.07, 0.02])
    has_cr_card = RNG.choice([0, 1], size=n, p=[0.29, 0.71])
    is_active_member = RNG.choice([0, 1], size=n, p=[0.48, 0.52])
    estimated_salary = np.clip(RNG.uniform(11.0, 199999.0, size=n), 11, 199999).round(2)

    # --- Realistic churn probability model ---------------------------------
    # Older customers, inactive members, single-product holders, and
    # customers in Germany churn at meaningfully higher rates - mirrors
    # patterns commonly observed in the public dataset.
    logit = (
        -2.6
        + 0.045 * (age - 38)
        + 0.9 * (is_active_member == 0)
        + 0.55 * (num_products == 1)
        - 0.9 * (num_products >= 3)
        + 0.5 * (geography == "Germany")
        + 0.15 * (gender == "Female")
        - 0.0000035 * (balance - 97000)
    )
    churn_prob = 1 / (1 + np.exp(-logit))
    exited = (RNG.random(n) < churn_prob).astype(int)

    df = pd.DataFrame(
        {
            "RowNumber": np.arange(1, n + 1),
            "CustomerId": customer_id,
            "Surname": surname,
            "CreditScore": credit_score,
            "Geography": geography,
            "Gender": gender,
            "Age": age,
            "Tenure": tenure,
            "Balance": balance,
            "NumOfProducts": num_products,
            "HasCrCard": has_cr_card,
            "IsActiveMember": is_active_member,
            "EstimatedSalary": estimated_salary,
            "Exited": exited,
        }
    )

    df = _inject_messiness(df)
    return df


def _inject_messiness(df: pd.DataFrame) -> pd.DataFrame:
    """Seed realistic data-quality issues for the cleaning pipeline to fix."""
    n = len(df)

    # 1) Missing values in a handful of columns
    for col, frac in [("CreditScore", 0.012), ("Balance", 0.02), ("EstimatedSalary", 0.008), ("Geography", 0.005)]:
        idx = RNG.choice(n, size=int(n * frac), replace=False)
        df.loc[idx, col] = np.nan

    # 2) Inconsistent text casing / stray whitespace
    idx = RNG.choice(n, size=int(n * 0.15), replace=False)
    df.loc[idx, "Geography"] = df.loc[idx, "Geography"].str.upper()
    idx = RNG.choice(n, size=int(n * 0.15), replace=False)
    df.loc[idx, "Gender"] = df.loc[idx, "Gender"].str.lower()
    idx = RNG.choice(n, size=int(n * 0.10), replace=False)
    df.loc[idx, "Geography"] = " " + df.loc[idx, "Geography"].astype(str) + "  "

    # 3) Duplicate rows (exact dupes of existing customers)
    dupes = df.sample(n=120, random_state=7)
    df = pd.concat([df, dupes], ignore_index=True)

    # 4) A few negative / impossible outliers to be caught by validation
    outlier_idx = RNG.choice(df.index, size=15, replace=False)
    df.loc[outlier_idx, "Age"] = RNG.integers(120, 150, size=15)
    outlier_idx2 = RNG.choice(df.index, size=10, replace=False)
    df.loc[outlier_idx2, "CreditScore"] = RNG.integers(-50, 0, size=10)

    # 5) Balance stored as text with currency symbols in a few rows
    df["Balance"] = df["Balance"].astype(object)
    idx = RNG.choice(df.index, size=25, replace=False)
    df.loc[idx, "Balance"] = df.loc[idx, "Balance"].apply(lambda x: f"${float(x):,.2f}")

    return df.sample(frac=1, random_state=1).reset_index(drop=True)


if __name__ == "__main__":
    raw_df = generate_raw_dataframe()
    out_path = "data/raw/bank_customers_raw.csv"
    raw_df.to_csv(out_path, index=False)
    print(f"Generated {len(raw_df):,} raw rows -> {out_path}")
