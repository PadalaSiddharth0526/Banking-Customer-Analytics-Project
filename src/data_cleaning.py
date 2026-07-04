"""
data_cleaning.py
=================
End-to-end cleaning pipeline for the raw banking customer dataset.

Pipeline stages:
    1. Load raw data
    2. Standardize text formatting (casing, whitespace)
    3. Fix data types (currency-as-string -> float, etc.)
    4. Handle missing values
    5. Remove duplicate records
    6. Handle outliers / impossible values
    7. Validate final data quality
    8. Persist the cleaned dataset

Usage:
    python -m src.data_cleaning
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)

RAW_PATH = Path("data/raw/bank_customers_raw.csv")
CLEAN_PATH = Path("data/processed/bank_customers_clean.csv")

VALID_GEOGRAPHIES = {"France", "Germany", "Spain"}
VALID_GENDERS = {"Male", "Female"}


@dataclass
class CleaningReport:
    """Tracks what the pipeline did, for transparency and the README/report."""

    initial_rows: int = 0
    final_rows: int = 0
    duplicates_removed: int = 0
    missing_values_before: dict = field(default_factory=dict)
    missing_values_after: dict = field(default_factory=dict)
    outliers_fixed: dict = field(default_factory=dict)
    validation_errors: list = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            "=== DATA CLEANING REPORT ===",
            f"Initial rows: {self.initial_rows:,}",
            f"Final rows:   {self.final_rows:,}",
            f"Duplicates removed: {self.duplicates_removed:,}",
            f"Missing values (before): {self.missing_values_before}",
            f"Missing values (after):  {self.missing_values_after}",
            f"Outliers fixed: {self.outliers_fixed}",
            f"Validation errors remaining: {len(self.validation_errors)}",
        ]
        return "\n".join(lines)


def load_raw_data(path: Path = RAW_PATH) -> pd.DataFrame:
    """Load the raw CSV file into a DataFrame."""
    path = Path(path)
    logger.info("Loading raw data from %s", path)
    if not path.exists():
        raise FileNotFoundError(
            f"Raw data not found at {path}. Run `python src/generate_raw_data.py` first, "
            "or place the original dataset CSV at this path."
        )
    df = pd.read_csv(path)
    logger.info("Loaded %d rows, %d columns", *df.shape)
    return df


def standardize_text_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Fix inconsistent casing and stray whitespace in categorical text columns."""
    logger.info("Standardizing text fields (Geography, Gender, Surname)")
    df = df.copy()
    for col in ("Geography", "Gender", "Surname"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # Title-case Geography/Gender so "FRANCE", "france", "France" all collapse
    df["Geography"] = df["Geography"].str.title().replace({"Nan": np.nan})
    df["Gender"] = df["Gender"].str.title().replace({"Nan": np.nan})
    return df


def fix_data_types(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce columns to their correct dtypes, cleaning currency-formatted strings."""
    logger.info("Fixing data types")
    df = df.copy()

    def _parse_balance(value) -> float:
        if pd.isna(value):
            return np.nan
        if isinstance(value, str):
            cleaned = re.sub(r"[^0-9.\-]", "", value)
            return float(cleaned) if cleaned not in ("", "-", ".") else np.nan
        return float(value)

    df["Balance"] = df["Balance"].apply(_parse_balance)
    df["CreditScore"] = pd.to_numeric(df["CreditScore"], errors="coerce")
    df["EstimatedSalary"] = pd.to_numeric(df["EstimatedSalary"], errors="coerce")
    df["Age"] = pd.to_numeric(df["Age"], errors="coerce")
    df["Tenure"] = pd.to_numeric(df["Tenure"], errors="coerce").astype("Int64")
    df["NumOfProducts"] = pd.to_numeric(df["NumOfProducts"], errors="coerce").astype("Int64")
    df["HasCrCard"] = pd.to_numeric(df["HasCrCard"], errors="coerce").astype("Int64")
    df["IsActiveMember"] = pd.to_numeric(df["IsActiveMember"], errors="coerce").astype("Int64")
    df["Exited"] = pd.to_numeric(df["Exited"], errors="coerce").astype("Int64")
    return df


def handle_missing_values(df: pd.DataFrame, report: CleaningReport) -> pd.DataFrame:
    """Impute or drop missing values using column-appropriate strategies."""
    logger.info("Handling missing values")
    df = df.copy()
    report.missing_values_before = df.isna().sum().to_dict()

    # Numeric columns: median imputation (robust to outliers, preserves distribution shape)
    for col in ("CreditScore", "Balance", "EstimatedSalary"):
        if df[col].isna().any():
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            logger.info("Filled %d missing '%s' values with median=%.2f",
                        report.missing_values_before.get(col, 0), col, median_val)

    # Categorical: mode imputation
    for col in ("Geography", "Gender"):
        if df[col].isna().any():
            mode_val = df[col].mode(dropna=True)[0]
            df[col] = df[col].fillna(mode_val)
            logger.info("Filled missing '%s' values with mode='%s'", col, mode_val)

    # Rows still missing a primary key (CustomerId) cannot be salvaged -> drop
    before = len(df)
    df = df.dropna(subset=["CustomerId"])
    dropped = before - len(df)
    if dropped:
        logger.warning("Dropped %d rows with missing CustomerId", dropped)

    report.missing_values_after = df.isna().sum().to_dict()
    return df


def remove_duplicates(df: pd.DataFrame, report: CleaningReport) -> pd.DataFrame:
    """Remove exact duplicate rows and duplicate CustomerIds (keep first)."""
    logger.info("Removing duplicate records")
    before = len(df)

    df = df.drop_duplicates()
    df = df.drop_duplicates(subset=["CustomerId"], keep="first")

    report.duplicates_removed = before - len(df)
    logger.info("Removed %d duplicate rows", report.duplicates_removed)
    return df


def handle_outliers(df: pd.DataFrame, report: CleaningReport) -> pd.DataFrame:
    """Cap/repair impossible or extreme values using domain-informed bounds.

    Strategy: values outside plausible banking-domain ranges are treated as
    data-entry errors and clipped to valid bounds (rather than dropped,
    to preserve sample size), while genuine but extreme values (e.g. very
    high balances) are left untouched since they are plausible.
    """
    logger.info("Handling outliers and impossible values")
    df = df.copy()
    fixes = {}

    # Age: no customer can be < 18 or > 100 in this population
    invalid_age = ((df["Age"] < 18) | (df["Age"] > 100)).sum()
    df["Age"] = df["Age"].clip(lower=18, upper=100)
    fixes["Age_out_of_range"] = int(invalid_age)

    # CreditScore: valid FICO-style range is 300-850
    invalid_credit = ((df["CreditScore"] < 300) | (df["CreditScore"] > 850)).sum()
    df["CreditScore"] = df["CreditScore"].clip(lower=300, upper=850)
    fixes["CreditScore_out_of_range"] = int(invalid_credit)

    # Balance / Salary cannot be negative
    invalid_balance = (df["Balance"] < 0).sum()
    df["Balance"] = df["Balance"].clip(lower=0)
    fixes["Balance_negative"] = int(invalid_balance)

    invalid_salary = (df["EstimatedSalary"] < 0).sum()
    df["EstimatedSalary"] = df["EstimatedSalary"].clip(lower=0)
    fixes["EstimatedSalary_negative"] = int(invalid_salary)

    # Tenure cannot exceed a customer's working-adult lifetime and must be >= 0
    df["Tenure"] = df["Tenure"].clip(lower=0, upper=15)

    report.outliers_fixed = fixes
    logger.info("Outlier fixes applied: %s", fixes)
    return df


def validate_data_quality(df: pd.DataFrame, report: CleaningReport) -> pd.DataFrame:
    """Run final validation rules; log any residual issues (does not raise)."""
    logger.info("Validating final data quality")
    errors = []

    if df["CustomerId"].duplicated().any():
        errors.append("Duplicate CustomerId values remain")
    if df.isna().sum().sum() > 0:
        errors.append(f"Remaining nulls: {df.isna().sum().to_dict()}")
    if not set(df["Geography"].unique()).issubset(VALID_GEOGRAPHIES):
        errors.append(f"Unexpected Geography values: {set(df['Geography'].unique()) - VALID_GEOGRAPHIES}")
    if not set(df["Gender"].unique()).issubset(VALID_GENDERS):
        errors.append(f"Unexpected Gender values: {set(df['Gender'].unique()) - VALID_GENDERS}")
    if (df["Age"] < 18).any() or (df["Age"] > 100).any():
        errors.append("Age values outside [18, 100] remain")
    if (df["CreditScore"] < 300).any() or (df["CreditScore"] > 850).any():
        errors.append("CreditScore values outside [300, 850] remain")

    for e in errors:
        logger.warning("Validation issue: %s", e)

    report.validation_errors = errors
    if not errors:
        logger.info("All validation checks passed.")
    return df


def run_cleaning_pipeline(raw_path: Path = RAW_PATH, output_path: Path = CLEAN_PATH) -> tuple[pd.DataFrame, CleaningReport]:
    """Execute the full cleaning pipeline end-to-end and persist the result."""
    raw_path = Path(raw_path)
    output_path = Path(output_path)
    report = CleaningReport()
    df = load_raw_data(raw_path)
    report.initial_rows = len(df)

    df = standardize_text_fields(df)
    df = fix_data_types(df)
    df = handle_missing_values(df, report)
    df = remove_duplicates(df, report)
    df = handle_outliers(df, report)
    df = validate_data_quality(df, report)

    df = df.drop(columns=["RowNumber"], errors="ignore").reset_index(drop=True)
    report.final_rows = len(df)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info("Saved cleaned dataset to %s", output_path)
    logger.info("\n%s", report.summary())

    return df, report


if __name__ == "__main__":
    clean_df, cleaning_report = run_cleaning_pipeline()
    print(cleaning_report.summary())
