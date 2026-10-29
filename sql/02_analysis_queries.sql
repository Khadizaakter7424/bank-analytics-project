-- =====================================================================
-- 02_analysis_queries.sql  |  Bank Customer Churn & Loan Portfolio Analysis
-- Run AFTER 01_schema.sql and loading the data (python/05_load_to_sqlite.py).
-- Written in standard SQL: runs in SQLite as-is, and in SQL Server /
-- MySQL / PostgreSQL with the small notes marked "NOTE".
--
-- Skills shown: GROUP BY, CASE WHEN, JOIN, subquery, CTE (WITH),
--               window functions (RANK, ROW_NUMBER, running SUM), VIEW
-- =====================================================================


-- ---------------------------------------------------------------------
-- Q1. Headline KPIs
-- ---------------------------------------------------------------------
SELECT
    COUNT(*)                                   AS total_customers,
    SUM(exited)                                AS churned_customers,
    ROUND(100.0 * SUM(exited) / COUNT(*), 2)   AS churn_rate_pct,
    ROUND(AVG(balance), 2)                     AS avg_balance,
    ROUND(AVG(credit_score), 0)                AS avg_credit_score
FROM customers;


-- ---------------------------------------------------------------------
-- Q2. Churn rate by country
-- ---------------------------------------------------------------------
SELECT
    geography,
    COUNT(*)                                   AS customers,
    SUM(exited)                                AS churned,
    ROUND(100.0 * SUM(exited) / COUNT(*), 2)   AS churn_rate_pct
FROM customers
GROUP BY geography
ORDER BY churn_rate_pct DESC;


-- ---------------------------------------------------------------------
-- Q3. Churn rate by age group
-- ---------------------------------------------------------------------
SELECT
    age_group,
    COUNT(*)                                   AS customers,
    SUM(exited)                                AS churned,
    ROUND(100.0 * SUM(exited) / COUNT(*), 2)   AS churn_rate_pct
FROM customers
GROUP BY age_group
ORDER BY age_group;


-- ---------------------------------------------------------------------
-- Q4. Churn rate by number of products held
-- ---------------------------------------------------------------------
SELECT
    num_of_products,
    COUNT(*)                                   AS customers,
    SUM(exited)                                AS churned,
    ROUND(100.0 * SUM(exited) / COUNT(*), 2)   AS churn_rate_pct
FROM customers
GROUP BY num_of_products
ORDER BY num_of_products;


-- ---------------------------------------------------------------------
-- Q5. Active vs inactive members (CASE WHEN turns 1/0 into a label)
-- ---------------------------------------------------------------------
SELECT
    CASE WHEN is_active_member = 1 THEN 'Active member' ELSE 'Inactive member' END AS member_type,
    COUNT(*)                                   AS customers,
    SUM(exited)                                AS churned,
    ROUND(100.0 * SUM(exited) / COUNT(*), 2)   AS churn_rate_pct
FROM customers
GROUP BY CASE WHEN is_active_member = 1 THEN 'Active member' ELSE 'Inactive member' END;


-- ---------------------------------------------------------------------
-- Q6. Churn rate by country AND gender (conditional aggregation)
--     One row per country, one column per gender.
-- ---------------------------------------------------------------------
SELECT
    geography,
    ROUND(100.0 * SUM(CASE WHEN gender = 'Female' THEN exited ELSE 0 END)
          / SUM(CASE WHEN gender = 'Female' THEN 1 ELSE 0 END), 2) AS female_churn_pct,
    ROUND(100.0 * SUM(CASE WHEN gender = 'Male' THEN exited ELSE 0 END)
          / SUM(CASE WHEN gender = 'Male' THEN 1 ELSE 0 END), 2)   AS male_churn_pct
FROM customers
GROUP BY geography
ORDER BY geography;


-- ---------------------------------------------------------------------
-- Q7. Money walking out: balance held by churned customers, by country
-- ---------------------------------------------------------------------
SELECT
    geography,
    ROUND(SUM(balance), 0)                                             AS total_balance,
    ROUND(SUM(CASE WHEN exited = 1 THEN balance ELSE 0 END), 0)        AS churned_balance,
    ROUND(100.0 * SUM(CASE WHEN exited = 1 THEN balance ELSE 0 END)
          / SUM(balance), 2)                                           AS churned_balance_pct
FROM customers
GROUP BY geography
ORDER BY churned_balance DESC;


-- ---------------------------------------------------------------------
-- Q8. Loan portfolio summary by loan type
-- ---------------------------------------------------------------------
SELECT
    loan_type,
    COUNT(*)                                                         AS loans,
    ROUND(SUM(loan_amount), 0)                                       AS total_amount,
    ROUND(AVG(interest_rate), 2)                                     AS avg_interest_rate,
    SUM(CASE WHEN loan_status = 'Default' THEN 1 ELSE 0 END)         AS defaulted_loans,
    ROUND(100.0 * SUM(CASE WHEN loan_status = 'Default' THEN 1 ELSE 0 END)
          / COUNT(*), 2)                                             AS default_rate_pct,
    ROUND(SUM(CASE WHEN loan_status = 'Default' THEN loan_amount ELSE 0 END), 0) AS defaulted_amount
FROM loans
GROUP BY loan_type
ORDER BY default_rate_pct DESC;


-- ---------------------------------------------------------------------
-- Q9. Default rate by customer credit band (JOIN loans to customers)
-- ---------------------------------------------------------------------
SELECT
    c.credit_score_band,
    COUNT(*)                                                         AS loans,
    SUM(CASE WHEN l.loan_status = 'Default' THEN 1 ELSE 0 END)       AS defaulted_loans,
    ROUND(100.0 * SUM(CASE WHEN l.loan_status = 'Default' THEN 1 ELSE 0 END)
          / COUNT(*), 2)                                             AS default_rate_pct
FROM loans AS l
JOIN customers AS c ON c.customer_id = l.customer_id
GROUP BY c.credit_score_band
ORDER BY c.credit_score_band;


-- ---------------------------------------------------------------------
-- Q10. CTE: do customers WITH a loan churn differently from those without?
--      (loan data is simulated, so read this as a method demo)
-- ---------------------------------------------------------------------
WITH loan_flag AS (
    SELECT
        c.customer_id,
        c.exited,
        CASE WHEN EXISTS (SELECT 1 FROM loans AS l WHERE l.customer_id = c.customer_id)
             THEN 'Has loan' ELSE 'No loan' END AS loan_group
    FROM customers AS c
)
SELECT
    loan_group,
    COUNT(*)                                   AS customers,
    SUM(exited)                                AS churned,
    ROUND(100.0 * SUM(exited) / COUNT(*), 2)   AS churn_rate_pct
FROM loan_flag
GROUP BY loan_group;


-- ---------------------------------------------------------------------
-- Q11. Window function RANK(): rank countries by churn rate
-- ---------------------------------------------------------------------
WITH geo AS (
    SELECT
        geography,
        ROUND(100.0 * SUM(exited) / COUNT(*), 2) AS churn_rate_pct
    FROM customers
    GROUP BY geography
)
SELECT
    geography,
    churn_rate_pct,
    RANK() OVER (ORDER BY churn_rate_pct DESC) AS churn_rank
FROM geo
ORDER BY churn_rank;


-- ---------------------------------------------------------------------
-- Q12. ROW_NUMBER() with PARTITION BY: top 3 balances in every country
-- ---------------------------------------------------------------------
WITH ranked AS (
    SELECT
        geography,
        customer_id,
        balance,
        exited,
        ROW_NUMBER() OVER (PARTITION BY geography ORDER BY balance DESC) AS rn
    FROM customers
)
SELECT geography, customer_id, balance, exited, rn AS rank_in_country
FROM ranked
WHERE rn <= 3
ORDER BY geography, rn;


-- ---------------------------------------------------------------------
-- Q13. Running total: loans issued per year and cumulative amount
--      NOTE (SQL Server): replace SUBSTRING(loan_start_date, 1, 4) with YEAR(loan_start_date)
-- ---------------------------------------------------------------------
WITH yearly AS (
    SELECT
        SUBSTRING(loan_start_date, 1, 4) AS loan_year,
        COUNT(*)                         AS loans_issued,
        SUM(loan_amount)                 AS amount_issued
    FROM loans
    GROUP BY SUBSTRING(loan_start_date, 1, 4)
)
SELECT
    loan_year,
    loans_issued,
    ROUND(amount_issued, 0)                                   AS amount_issued,
    ROUND(SUM(amount_issued) OVER (ORDER BY loan_year), 0)    AS cumulative_amount
FROM yearly
ORDER BY loan_year;


-- ---------------------------------------------------------------------
-- Q14. Loan exposure at risk: customers the model flags as HIGH churn risk
--      who still have ACTIVE loans (3-table JOIN)
-- ---------------------------------------------------------------------
SELECT
    c.geography,
    COUNT(DISTINCT c.customer_id)   AS high_risk_borrowers,
    COUNT(*)                        AS active_loans,
    ROUND(SUM(l.loan_amount), 0)    AS active_loan_exposure
FROM customers AS c
JOIN churn_scores AS s ON s.customer_id = c.customer_id
JOIN loans AS l        ON l.customer_id = c.customer_id
WHERE s.risk_level = 'High'
  AND c.exited = 0
  AND l.loan_status = 'Active'
GROUP BY c.geography
ORDER BY active_loan_exposure DESC;


-- ---------------------------------------------------------------------
-- Q15. Retention call list: top 10 high-balance customers who are still
--      with the bank but have HIGH churn risk
--      (ROW_NUMBER instead of TOP/LIMIT, so it works in every database)
-- ---------------------------------------------------------------------
WITH at_risk AS (
    SELECT
        c.customer_id,
        c.geography,
        c.age,
        c.balance,
        c.num_of_products,
        s.churn_probability,
        ROW_NUMBER() OVER (ORDER BY c.balance DESC) AS rn
    FROM customers AS c
    JOIN churn_scores AS s ON s.customer_id = c.customer_id
    WHERE s.risk_level = 'High'
      AND c.exited = 0
)
SELECT customer_id, geography, age, balance, num_of_products, churn_probability
FROM at_risk
WHERE rn <= 10
ORDER BY rn;


-- ---------------------------------------------------------------------
-- Q16. A VIEW: one tidy "customer 360" table (customer + loans + risk score).
--      Connect Power BI to this view if you load data from a database.
--      NOTE (SQL Server): CREATE VIEW must be the only statement in its batch,
--      so put GO on the line before and after it.
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS vw_customer_360;

CREATE VIEW vw_customer_360 AS
SELECT
    c.customer_id,
    c.geography,
    c.gender,
    c.age,
    c.age_group,
    c.credit_score,
    c.credit_score_band,
    c.balance,
    c.num_of_products,
    c.is_active_member,
    c.estimated_salary,
    c.exited,
    COALESCE(ln.loan_count, 0)     AS loan_count,
    COALESCE(ln.total_loan_amount, 0) AS total_loan_amount,
    COALESCE(ln.defaulted_loans, 0)   AS defaulted_loans,
    s.churn_probability,
    s.risk_level
FROM customers AS c
LEFT JOIN (
    SELECT
        customer_id,
        COUNT(*)         AS loan_count,
        SUM(loan_amount) AS total_loan_amount,
        SUM(CASE WHEN loan_status = 'Default' THEN 1 ELSE 0 END) AS defaulted_loans
    FROM loans
    GROUP BY customer_id
) AS ln ON ln.customer_id = c.customer_id
LEFT JOIN churn_scores AS s ON s.customer_id = c.customer_id;

SELECT * FROM vw_customer_360 LIMIT 5;  -- NOTE (SQL Server): use SELECT TOP 5 * FROM vw_customer_360;
