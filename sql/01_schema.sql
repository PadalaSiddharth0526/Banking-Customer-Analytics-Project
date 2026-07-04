-- =============================================================================
-- 01_schema.sql
-- Schema documentation for the `customers` table.
-- Note: in this project the table is created programmatically by
-- src/database.py (pandas.to_sql) from the cleaned + segmented + revenue
-- CSV so that Python and SQL always stay in sync. This script is the
-- authoritative schema reference and can be run directly against a fresh
-- PostgreSQL database if you prefer to load data via COPY instead of pandas.
-- =============================================================================

DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    "CustomerId"             BIGINT PRIMARY KEY,
    "Surname"                VARCHAR(50),
    "CreditScore"            INTEGER        CHECK ("CreditScore" BETWEEN 300 AND 850),
    "Geography"              VARCHAR(20)    CHECK ("Geography" IN ('France', 'Germany', 'Spain')),
    "Gender"                 VARCHAR(10)    CHECK ("Gender" IN ('Male', 'Female')),
    "Age"                    INTEGER        CHECK ("Age" BETWEEN 18 AND 100),
    "Tenure"                 INTEGER        CHECK ("Tenure" >= 0),
    "Balance"                NUMERIC(14,2)  CHECK ("Balance" >= 0),
    "NumOfProducts"          SMALLINT       CHECK ("NumOfProducts" BETWEEN 1 AND 4),
    "HasCrCard"              SMALLINT       CHECK ("HasCrCard" IN (0, 1)),
    "IsActiveMember"         SMALLINT       CHECK ("IsActiveMember" IN (0, 1)),
    "EstimatedSalary"        NUMERIC(14,2)  CHECK ("EstimatedSalary" >= 0),
    "Exited"                 SMALLINT       CHECK ("Exited" IN (0, 1)),
    "ValueSegment"           VARCHAR(20),
    "LifeStageSegment"       VARCHAR(25),
    "HighRiskChurn"          BOOLEAN,
    "PremiumCustomer"        BOOLEAN,
    "EstimatedAnnualRevenue" NUMERIC(14,2)
);

-- Helpful indexes for the query patterns used throughout sql/02_business_queries.sql
CREATE INDEX idx_customers_geography ON customers ("Geography");
CREATE INDEX idx_customers_exited    ON customers ("Exited");
CREATE INDEX idx_customers_segment   ON customers ("ValueSegment");
