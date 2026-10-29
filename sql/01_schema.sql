-- =====================================================================
-- 01_schema.sql  |  Bank Customer Churn & Loan Portfolio Analysis
-- Creates three tables:
--   customers     (one row per customer)         <- Kaggle data, cleaned
--   loans         (0, 1 or 2 rows per customer)  <- simulated
--   churn_scores  (one row per customer)         <- output of the ML model
-- Works in SQLite, SQL Server, MySQL and PostgreSQL (standard SQL types).
-- =====================================================================

DROP TABLE IF EXISTS churn_scores;
DROP TABLE IF EXISTS loans;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id        INT PRIMARY KEY,
    credit_score       INT           NOT NULL,
    geography          VARCHAR(20)   NOT NULL,
    gender             VARCHAR(10)   NOT NULL,
    age                INT           NOT NULL,
    tenure             INT           NOT NULL,
    balance            DECIMAL(14,2) NOT NULL,
    num_of_products    INT           NOT NULL,
    has_cr_card        INT           NOT NULL,   -- 1 = yes, 0 = no
    is_active_member   INT           NOT NULL,   -- 1 = yes, 0 = no
    estimated_salary   DECIMAL(14,2) NOT NULL,
    exited             INT           NOT NULL,   -- 1 = churned, 0 = retained
    age_group          VARCHAR(10),
    credit_score_band  VARCHAR(20),
    balance_segment    VARCHAR(20),
    tenure_group       VARCHAR(20),
    churn_status       VARCHAR(10)
);

CREATE TABLE loans (
    loan_id          VARCHAR(10) PRIMARY KEY,
    customer_id      INT           NOT NULL,
    loan_type        VARCHAR(20)   NOT NULL,   -- Personal / Home / Auto / Business / Education
    loan_amount      DECIMAL(14,2) NOT NULL,
    interest_rate    DECIMAL(5,2)  NOT NULL,
    tenure_months    INT           NOT NULL,
    loan_start_date  DATE          NOT NULL,
    loan_status      VARCHAR(10)   NOT NULL,   -- Active / Closed / Default
    days_past_due    INT           NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
);

CREATE TABLE churn_scores (
    customer_id        INT PRIMARY KEY,
    churn_probability  DECIMAL(5,4) NOT NULL,  -- 0.0000 to 1.0000
    risk_level         VARCHAR(10)  NOT NULL,  -- Low / Medium / High
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
);
