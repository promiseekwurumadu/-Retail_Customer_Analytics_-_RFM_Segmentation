-- analysis_queries.sql
-- Core retail analytics queries
-- Written in standard PostgreSQL SQL
-- Compatible with pgAdmin query tool

-- ── QUERY 1: OVERALL BUSINESS SUMMARY ────────────────────────────
-- The first thing any analyst does — understand the big picture
-- Run this in pgAdmin to get a feel for the data

SELECT
    COUNT(DISTINCT t.transaction_id)          AS total_transactions,
    COUNT(DISTINCT t.customer_id)             AS unique_customers,
    COUNT(DISTINCT t.product_id)              AS unique_products,
    COUNT(DISTINCT t.store_id)                AS stores_trading,
    ROUND(SUM(t.total_value)::NUMERIC, 2)     AS total_revenue,
    ROUND(AVG(t.total_value)::NUMERIC, 2)     AS avg_transaction_value,
    MIN(t.transaction_date)                   AS earliest_date,
    MAX(t.transaction_date)                   AS latest_date
FROM transactions t
WHERE t.quantity > 0;  -- exclude returns


-- ── QUERY 2: MONTHLY REVENUE TREND ───────────────────────────────
-- Answers: Is the business growing month by month?
-- DATE_TRUNC rounds a date down to the start of the month

SELECT
    DATE_TRUNC('month', transaction_date)     AS month,
    COUNT(transaction_id)                     AS num_transactions,
    COUNT(DISTINCT customer_id)               AS unique_customers,
    ROUND(SUM(total_value)::NUMERIC, 2)       AS monthly_revenue,
    ROUND(AVG(total_value)::NUMERIC, 2)       AS avg_order_value
FROM transactions
WHERE quantity > 0
GROUP BY DATE_TRUNC('month', transaction_date)
ORDER BY month;


-- ── QUERY 3: REVENUE BY CATEGORY ─────────────────────────────────
-- Answers: Which product categories make the most money?
-- JOIN connects transactions to products using product_id

SELECT
    p.category,
    COUNT(t.transaction_id)                   AS num_transactions,
    SUM(t.quantity)                           AS units_sold,
    ROUND(SUM(t.total_value)::NUMERIC, 2)     AS total_revenue,
    ROUND(AVG(t.total_value)::NUMERIC, 2)     AS avg_order_value,
    ROUND(
        SUM(t.total_value) * 100.0 /
        SUM(SUM(t.total_value)) OVER ()
    , 1)                                      AS revenue_pct
FROM transactions t
JOIN products p
  ON t.product_id = p.product_id
WHERE t.quantity > 0
GROUP BY p.category
ORDER BY total_revenue DESC;


-- ── QUERY 4: TOP 10 BEST SELLING PRODUCTS ────────────────────────
SELECT
    p.product_name,
    p.category,
    COUNT(t.transaction_id)                   AS times_purchased,
    SUM(t.quantity)                           AS total_units,
    ROUND(SUM(t.total_value)::NUMERIC, 2)     AS total_revenue
FROM transactions t
JOIN products p
  ON t.product_id = p.product_id
WHERE t.quantity > 0
GROUP BY p.product_name, p.category
ORDER BY total_revenue DESC
LIMIT 10;


-- ── QUERY 5: REVENUE BY REGION ────────────────────────────────────
-- Answers: Which parts of the UK perform best?
-- Joins transactions → stores → region

SELECT
    s.region,
    COUNT(DISTINCT t.store_id)                AS num_stores,
    COUNT(t.transaction_id)                   AS num_transactions,
    ROUND(SUM(t.total_value)::NUMERIC, 2)     AS total_revenue,
    ROUND(
        SUM(t.total_value) /
        COUNT(DISTINCT t.store_id)
    , 2)                                      AS revenue_per_store
FROM transactions t
JOIN stores s
  ON t.store_id = s.store_id
WHERE t.quantity > 0
GROUP BY s.region
ORDER BY total_revenue DESC;


-- ── QUERY 6: ONLINE VS IN-STORE ───────────────────────────────────
-- Answers: How does online compare to physical stores?
SELECT
    channel,
    COUNT(transaction_id)                     AS transactions,
    COUNT(DISTINCT customer_id)               AS unique_customers,
    ROUND(SUM(total_value)::NUMERIC, 2)       AS total_revenue,
    ROUND(AVG(total_value)::NUMERIC, 2)       AS avg_order_value
FROM transactions
WHERE quantity > 0
GROUP BY channel
ORDER BY total_revenue DESC;


-- ── QUERY 7: RETURNS ANALYSIS ─────────────────────────────────────
-- Answers: How many returns are we getting and which categories?
SELECT
    p.category,
    COUNT(t.transaction_id)                   AS num_returns,
    ABS(SUM(t.total_value))                   AS value_returned,
    ROUND(
        COUNT(t.transaction_id) * 100.0 /
        (SELECT COUNT(*) FROM transactions
         WHERE quantity < 0)
    , 1)                                      AS pct_of_all_returns
FROM transactions t
JOIN products p
  ON t.product_id = p.product_id
WHERE t.quantity < 0
GROUP BY p.category
ORDER BY num_returns DESC;


-- ── QUERY 8: PAYMENT METHOD BREAKDOWN ────────────────────────────
SELECT
    payment_method,
    COUNT(*)                                  AS transactions,
    ROUND(SUM(total_value)::NUMERIC, 2)       AS total_revenue,
    ROUND(AVG(total_value)::NUMERIC, 2)       AS avg_value
FROM transactions
WHERE quantity > 0
GROUP BY payment_method
ORDER BY transactions DESC;