"""
test_pipeline.py
=================
Unit tests for the core analytics modules. Run with:
    pytest tests/ -v
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.data_cleaning import (
    CleaningReport,
    fix_data_types,
    handle_missing_values,
    handle_outliers,
    remove_duplicates,
    standardize_text_fields,
    validate_data_quality,
)
from src.segmentation import add_life_stage_segment, add_risk_flags, add_value_segment
from src.churn_analysis import overall_churn_rate, churn_by_dimension
from src.revenue_analysis import estimate_annual_revenue


@pytest.fixture
def messy_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "CustomerId": [1, 2, 3, 4, 4],  # duplicate id
            "Surname": ["Smith", "Jones", "Doe", "Lee", "Lee"],
            "CreditScore": [700, np.nan, -20, 900, 900],
            "Geography": ["france", "GERMANY", " Spain ", "France", "France"],
            "Gender": ["male", "Female", "Female", "Male", "Male"],
            "Age": [30, 45, 130, 60, 60],
            "Tenure": [2, 5, 8, 3, 3],
            "Balance": ["$1,000.00", 50000.0, 0.0, np.nan, np.nan],
            "NumOfProducts": [1, 2, 1, 3, 3],
            "HasCrCard": [1, 0, 1, 1, 1],
            "IsActiveMember": [1, 0, 1, 0, 0],
            "EstimatedSalary": [50000, 60000, 70000, 80000, 80000],
            "Exited": [0, 1, 0, 1, 1],
        }
    )


def test_standardize_text_fields(messy_df):
    df = standardize_text_fields(messy_df)
    assert set(df["Geography"].unique()) <= {"France", "Germany", "Spain"}
    assert set(df["Gender"].unique()) <= {"Male", "Female"}


def test_fix_data_types_parses_currency_strings(messy_df):
    df = standardize_text_fields(messy_df)
    df = fix_data_types(df)
    assert df["Balance"].iloc[0] == pytest.approx(1000.00)
    assert pd.api.types.is_float_dtype(df["Balance"])


def test_handle_missing_values_fills_all_nulls(messy_df):
    df = standardize_text_fields(messy_df)
    df = fix_data_types(df)
    report = CleaningReport()
    df = handle_missing_values(df, report)
    assert df.isna().sum().sum() == 0


def test_remove_duplicates_drops_duplicate_customer_id(messy_df):
    df = standardize_text_fields(messy_df)
    df = fix_data_types(df)
    report = CleaningReport()
    df = handle_missing_values(df, report)
    df = remove_duplicates(df, report)
    assert df["CustomerId"].is_unique
    assert report.duplicates_removed >= 1


def test_handle_outliers_clips_impossible_values(messy_df):
    df = standardize_text_fields(messy_df)
    df = fix_data_types(df)
    report = CleaningReport()
    df = handle_missing_values(df, report)
    df = remove_duplicates(df, report)
    df = handle_outliers(df, report)
    assert df["Age"].max() <= 100
    assert df["CreditScore"].min() >= 300


def test_validate_data_quality_passes_after_full_pipeline(messy_df):
    df = standardize_text_fields(messy_df)
    df = fix_data_types(df)
    report = CleaningReport()
    df = handle_missing_values(df, report)
    df = remove_duplicates(df, report)
    df = handle_outliers(df, report)
    df = validate_data_quality(df, report)
    assert report.validation_errors == []


@pytest.fixture
def clean_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "CustomerId": range(1, 11),
            "Balance": [0, 10000, 50000, 80000, 120000, 150000, 200000, 30000, 60000, 90000],
            "NumOfProducts": [1, 1, 2, 2, 3, 1, 4, 2, 1, 2],
            "Age": [22, 33, 44, 55, 66, 77, 28, 39, 50, 61],
            "HasCrCard": [1, 0, 1, 1, 0, 1, 1, 0, 1, 1],
            "IsActiveMember": [1, 0, 1, 0, 1, 0, 1, 1, 0, 1],
            "Geography": ["France", "Germany", "Spain", "France", "Germany", "Spain", "France", "Germany", "Spain", "France"],
            "Exited": [0, 1, 0, 1, 0, 1, 0, 0, 1, 0],
        }
    )


def test_add_value_segment_creates_expected_categories(clean_df):
    df = add_value_segment(clean_df)
    assert set(df["ValueSegment"].unique()) <= {"High-Value", "Medium-Value", "Low-Value"}


def test_add_life_stage_segment_buckets_correctly(clean_df):
    df = add_life_stage_segment(clean_df)
    young = df[df["Age"] < 35]
    assert (young["LifeStageSegment"] == "Young Professional").all()


def test_add_risk_flags_are_boolean(clean_df):
    df = add_risk_flags(clean_df)
    assert df["HighRiskChurn"].dtype == bool
    assert df["PremiumCustomer"].dtype == bool


def test_overall_churn_rate_matches_manual_calc(clean_df):
    rate = overall_churn_rate(clean_df)
    assert rate == pytest.approx(clean_df["Exited"].mean(), abs=1e-6)


def test_churn_by_dimension_sums_to_total_customers(clean_df):
    result = churn_by_dimension(clean_df, "Geography")
    assert result["customers"].sum() == len(clean_df)


def test_estimate_annual_revenue_is_positive_and_numeric(clean_df):
    df = estimate_annual_revenue(clean_df)
    assert (df["EstimatedAnnualRevenue"] >= 0).all()
    assert pd.api.types.is_numeric_dtype(df["EstimatedAnnualRevenue"])
