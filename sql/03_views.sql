-- =============================================================================
-- 03_views.sql
-- Reusable reporting views. Views encapsulate business logic once so that
-- the dashboard, reports, and any future BI tool query a single consistent
-- definition rather than re-deriving segments/metrics inconsistently.
-- =============================================================================

DROP VIEW IF EXISTS vw_country_summary;
CREATE VIEW vw_country_summary AS
SELECT
    "Geography" AS country,
    COUNT(*) AS total_customers,
    SUM("Exited") AS churned_customers,
    ROUND(100.0 * SUM("Exited") / COUNT(*), 2) AS churn_rate_pct,
    ROUND(AVG("Balance"), 2) AS avg_balance,
    ROUND(AVG("CreditScore"), 1) AS avg_credit_score,
    ROUND(SUM("EstimatedAnnualRevenue"), 2) AS total_estimated_revenue
FROM customers
GROUP BY "Geography";


DROP VIEW IF EXISTS vw_segment_summary;
CREATE VIEW vw_segment_summary AS
SELECT
    "ValueSegment" AS value_segment,
    "LifeStageSegment" AS life_stage_segment,
    COUNT(*) AS customers,
    ROUND(AVG("Balance"), 2) AS avg_balance,
    ROUND(100.0 * SUM("Exited") / COUNT(*), 2) AS churn_rate_pct,
    ROUND(SUM("EstimatedAnnualRevenue"), 2) AS total_estimated_revenue
FROM customers
GROUP BY "ValueSegment", "LifeStageSegment";


DROP VIEW IF EXISTS vw_churn_risk_watchlist;
CREATE VIEW vw_churn_risk_watchlist AS
SELECT
    "CustomerId",
    "Surname",
    "Geography",
    "Age",
    "Balance",
    "NumOfProducts",
    "IsActiveMember",
    "EstimatedAnnualRevenue",
    (
        CASE WHEN "IsActiveMember" = 0 THEN 2 ELSE 0 END +
        CASE WHEN "NumOfProducts" = 1 THEN 2 ELSE 0 END +
        CASE WHEN "Age" >= 50 THEN 1 ELSE 0 END +
        CASE WHEN "Balance" = 0 THEN 1 ELSE 0 END
    ) AS churn_risk_score
FROM customers
WHERE "Exited" = 0;


DROP VIEW IF EXISTS vw_premium_customers;
CREATE VIEW vw_premium_customers AS
SELECT
    "CustomerId", "Surname", "Geography", "Balance",
    "NumOfProducts", "EstimatedAnnualRevenue"
FROM customers
WHERE "PremiumCustomer" = 1;

-- Usage examples:
--   SELECT * FROM vw_country_summary ORDER BY total_estimated_revenue DESC;
--   SELECT * FROM vw_churn_risk_watchlist ORDER BY churn_risk_score DESC LIMIT 25;
