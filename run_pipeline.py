"""
run_pipeline.py
================
Single entry point that runs the entire analytics pipeline end-to-end:

    1. Generate raw data (skip if data/raw/bank_customers_raw.csv already exists,
       or if you've placed the real Kaggle dataset there yourself)
    2. Clean the data
    3. Build customer segments
    4. Estimate revenue
    5. Generate static EDA charts (images/*.png)
    6. Load everything into the SQLite analytics database and run SQL scripts

Usage:
    python run_pipeline.py

After running, launch the dashboard with:
    streamlit run dashboard/app.py
"""

from pathlib import Path

import pandas as pd

from src.utils.logger import get_logger

logger = get_logger("pipeline")

RAW_PATH = Path("data/raw/bank_customers_raw.csv")


def main() -> None:
    logger.info("STEP 0/6: Ensuring raw data exists")
    if not RAW_PATH.exists():
        from src.generate_raw_data import generate_raw_dataframe
        RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
        generate_raw_dataframe().to_csv(RAW_PATH, index=False)
        logger.info("Synthetic raw dataset generated at %s", RAW_PATH)
    else:
        logger.info("Raw data already present at %s - skipping generation", RAW_PATH)

    logger.info("STEP 1/6: Cleaning data")
    from src.data_cleaning import run_cleaning_pipeline
    clean_df, cleaning_report = run_cleaning_pipeline()
    print(cleaning_report.summary())

    logger.info("STEP 2/6: Building customer segments")
    from src.segmentation import build_segments
    segmented_df = build_segments(clean_df)
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    segmented_df.to_csv("data/processed/bank_customers_segmented.csv", index=False)

    logger.info("STEP 3/6: Estimating revenue")
    from src.revenue_analysis import full_revenue_report
    revenue_report, revenue_df = full_revenue_report(segmented_df)
    revenue_df.to_csv("data/processed/bank_customers_revenue.csv", index=False)

    logger.info("STEP 4/6: Running churn analysis")
    from src.churn_analysis import full_churn_report
    churn_report = full_churn_report(revenue_df)
    logger.info("Overall churn rate: %.2f%%", churn_report["overall_rate"] * 100)

    logger.info("STEP 5/6: Generating static EDA charts")
    from src.visualization import generate_all_static_charts
    generate_all_static_charts(revenue_df)

    logger.info("STEP 6/6: Building SQL database and running SQL scripts")
    from src.database import load_dataframe_to_db, run_sql_file
    load_dataframe_to_db()
    for script in sorted(Path("sql").glob("*.sql")):
        if script.name == "01_schema.sql":
            continue
        run_sql_file(script)

    logger.info("Pipeline complete. Launch the dashboard with: streamlit run dashboard/app.py")


if __name__ == "__main__":
    main()
