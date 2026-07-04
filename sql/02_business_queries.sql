-- =============================================================================
-- 02_business_queries.sql
-- Answers every business question requested in the project brief.
-- Compatible with SQLite (used by this project's src/database.py) and
-- PostgreSQL (only trivial dialect differences, noted inline where relevant).
--
-- Two small reference/dimension tables are created here purely to give
-- legitimate JOIN examples against the main `customers` fact table, mirroring
-- how a real bank would join customer data to a product-catalog or
-- country-metadata dimension table maintained by another team.
-- =============================================================================

DROP TABLE IF EXISTS product_catalog;
CREATE TABLE product_catalog (
    NumOfProducts INTEGER PRIMARY KEY,
    ProductBundleName TEXT,
    AnnualFeeUSD NUMERIC
);
INSERT INTO product_catalog (NumOfProducts, ProductBundleName, AnnualFeeUSD) VALUES
    (1, 'Essential Checking',      50),
    (2, 'Essential + Savings',     90),
    (3, 'Wealth Starter Bundle',  150),
    (4, 'Premier Relationship',   220);

DROP TABLE IF EXISTS country_metadata;
CREATE TABLE country_metadata (
    Geography TEXT PRIMARY KEY,
    Region TEXT,
    CurrencyCode TEXT
);
INSERT INTO country_metadata (Geography, Region, CurrencyCode) VALUES
    ('France',  'Western Europe',  'EUR'),
    ('Germany', 'Central Europe',  'EUR'),
    ('Spain',   'Southern Europe', 'EUR');


-- -----------------------------------------------------------------------------
-- Q1. Total customers
-- -----------------------------------------------------------------------------
SELECT COUNT(*) AS total_customers
FROM customers;


-- -----------------------------------------------------------------------------
-- Q2. Average account balance
-- -----------------------------------------------------------------------------
SELECT ROUND(AVG("Balance"), 2) AS avg_balance
FROM customers;


-- -----------------------------------------------------------------------------
-- Q3. Average salary
-- -----------------------------------------------------------------------------
SELECT ROUND(AVG("EstimatedSalary"), 2) AS avg_salary
FROM customers;


-- -----------------------------------------------------------------------------
-- Q4. Customers by country (GROUP BY)
-- -----------------------------------------------------------------------------
SELECT "Geography" AS country, COUNT(*) AS customer_count
FROM customers
GROUP BY "Geography"
ORDER BY customer_count DESC;


-- -----------------------------------------------------------------------------
-- Q5. Customers by gender (GROUP BY)
-- -----------------------------------------------------------------------------
SELECT "Gender" AS gender, COUNT(*) AS customer_count,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM customers), 2) AS pct_of_total
FROM customers
GROUP BY "Gender";


-- -----------------------------------------------------------------------------
-- Q6. Overall churn rate
-- -----------------------------------------------------------------------------
SELECT
    SUM("Exited")                                    AS churned_customers,
    COUNT(*)                                         AS total_customers,
    ROUND(100.0 * SUM("Exited") / COUNT(*), 2)       AS churn_rate_pct
FROM customers;


-- -----------------------------------------------------------------------------
-- Q7. Active customer percentage
-- -----------------------------------------------------------------------------
SELECT
    ROUND(100.0 * SUM("IsActiveMember") / COUNT(*), 2) AS active_pct,
    ROUND(100.0 * (COUNT(*) - SUM("IsActiveMember")) / COUNT(*), 2) AS inactive_pct
FROM customers;


-- -----------------------------------------------------------------------------
-- Q8. Top 10 high-value customers (by balance, with CASE-based tier label)
-- -----------------------------------------------------------------------------
SELECT
    "CustomerId",
    "Surname",
    "Geography",
    "Balance",
    "EstimatedAnnualRevenue",
    CASE
        WHEN "Balance" >= 150000 THEN 'Ultra High Net Worth'
        WHEN "Balance" >= 100000 THEN 'High Net Worth'
        ELSE 'Affluent'
    END AS wealth_tier
FROM customers
ORDER BY "Balance" DESC
LIMIT 10;


-- -----------------------------------------------------------------------------
-- Q9. Average credit score by country (GROUP BY + HAVING)
-- Only show countries where the average credit score is below the
-- portfolio-wide "good" threshold of 660, flagging countries needing
-- credit-quality attention.
-- -----------------------------------------------------------------------------
SELECT
    "Geography" AS country,
    ROUND(AVG("CreditScore"), 1) AS avg_credit_score,
    COUNT(*) AS customers
FROM customers
GROUP BY "Geography"
HAVING AVG("CreditScore") < 660
ORDER BY avg_credit_score ASC;


-- -----------------------------------------------------------------------------
-- Q10. Revenue by customer segment (GROUP BY + JOIN to product_catalog)
-- -----------------------------------------------------------------------------
SELECT
    c."ValueSegment",
    pc.ProductBundleName,
    COUNT(*) AS customers,
    ROUND(SUM(c."EstimatedAnnualRevenue"), 2) AS total_revenue,
    ROUND(AVG(c."EstimatedAnnualRevenue"), 2) AS avg_revenue_per_customer
FROM customers c
JOIN product_catalog pc ON c."NumOfProducts" = pc.NumOfProducts
GROUP BY c."ValueSegment", pc.ProductBundleName
ORDER BY total_revenue DESC;


-- -----------------------------------------------------------------------------
-- Q11. Customers with multiple products (CASE + filter)
-- -----------------------------------------------------------------------------
SELECT
    "CustomerId",
    "Surname",
    "NumOfProducts",
    CASE WHEN "NumOfProducts" >= 3 THEN 'Deeply Cross-Sold' ELSE 'Multi-Product' END AS multi_product_tier
FROM customers
WHERE "NumOfProducts" >= 2
ORDER BY "NumOfProducts" DESC;


-- -----------------------------------------------------------------------------
-- Q12. Customers at risk of churn (CASE-based composite risk score)
-- -----------------------------------------------------------------------------
SELECT
    "CustomerId",
    "Surname",
    "Geography",
    "Age",
    "NumOfProducts",
    "IsActiveMember",
    (
        CASE WHEN "IsActiveMember" = 0 THEN 2 ELSE 0 END +
        CASE WHEN "NumOfProducts" = 1 THEN 2 ELSE 0 END +
        CASE WHEN "Age" >= 50 THEN 1 ELSE 0 END +
        CASE WHEN "Balance" = 0 THEN 1 ELSE 0 END
    ) AS churn_risk_score
FROM customers
WHERE "Exited" = 0   -- still an active relationship worth protecting
ORDER BY churn_risk_score DESC
LIMIT 25;


-- -----------------------------------------------------------------------------
-- Q13. Country-level KPI dashboard feed (JOIN + CTE + window function)
-- Uses a CTE to pre-aggregate, then a window function to rank countries
-- by revenue without a second pass over the base table.
-- -----------------------------------------------------------------------------
WITH country_agg AS (
    SELECT
        c."Geography",
        cm.Region,
        COUNT(*)                                   AS customers,
        ROUND(AVG(c."Balance"), 2)                 AS avg_balance,
        ROUND(100.0 * SUM(c."Exited") / COUNT(*), 2) AS churn_rate_pct,
        ROUND(SUM(c."EstimatedAnnualRevenue"), 2)  AS total_revenue
    FROM customers c
    JOIN country_metadata cm ON c."Geography" = cm.Geography
    GROUP BY c."Geography", cm.Region
)
SELECT
    *,
    RANK() OVER (ORDER BY total_revenue DESC) AS revenue_rank
FROM country_agg
ORDER BY revenue_rank;


-- -----------------------------------------------------------------------------
-- Q14. Window functions: percentile rank of each customer's balance within
-- their own country (useful for "top X% of customers in your market" flags)
-- -----------------------------------------------------------------------------
SELECT
    "CustomerId",
    "Geography",
    "Balance",
    ROUND(PERCENT_RANK() OVER (PARTITION BY "Geography" ORDER BY "Balance"), 3) AS balance_percentile_in_country,
    NTILE(4) OVER (PARTITION BY "Geography" ORDER BY "Balance") AS balance_quartile_in_country
FROM customers
ORDER BY "Geography", "Balance" DESC;


-- -----------------------------------------------------------------------------
-- Q15. Running/cumulative revenue by country (window function, ordered frame)
-- -----------------------------------------------------------------------------
SELECT
    "Geography",
    "CustomerId",
    "EstimatedAnnualRevenue",
    SUM("EstimatedAnnualRevenue") OVER (
        PARTITION BY "Geography" ORDER BY "CustomerId"
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_revenue_in_country
FROM customers
ORDER BY "Geography", "CustomerId"
LIMIT 50;


-- -----------------------------------------------------------------------------
-- Q16. Churn rate by tenure band (CASE bucketing + GROUP BY)
-- -----------------------------------------------------------------------------
SELECT
    CASE
        WHEN "Tenure" <= 2 THEN '0-2 yrs'
        WHEN "Tenure" <= 5 THEN '3-5 yrs'
        WHEN "Tenure" <= 8 THEN '6-8 yrs'
        ELSE '9+ yrs'
    END AS tenure_band,
    COUNT(*) AS customers,
    ROUND(100.0 * SUM("Exited") / COUNT(*), 2) AS churn_rate_pct
FROM customers
GROUP BY tenure_band
ORDER BY churn_rate_pct DESC;


-- -----------------------------------------------------------------------------
-- Q17. High-value customers who are ALSO high churn-risk (the bank's most
-- urgent retention priority list) - combines CASE, HAVING-style filtering,
-- and a CTE.
-- -----------------------------------------------------------------------------
WITH risk_scored AS (
    SELECT
        "CustomerId", "Surname", "Geography", "Balance", "EstimatedAnnualRevenue",
        (
            CASE WHEN "IsActiveMember" = 0 THEN 2 ELSE 0 END +
            CASE WHEN "NumOfProducts" = 1 THEN 2 ELSE 0 END +
            CASE WHEN "Age" >= 50 THEN 1 ELSE 0 END
        ) AS churn_risk_score
    FROM customers
    WHERE "Exited" = 0 AND "ValueSegment" = 'High-Value'
)
SELECT *
FROM risk_scored
WHERE churn_risk_score >= 3
ORDER BY "EstimatedAnnualRevenue" DESC
LIMIT 20;
