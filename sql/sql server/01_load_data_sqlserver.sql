-- =====================================================================
-- 01_load_data_sqlserver.sql  |  SQL Server (SSMS) - load the 3 CSV files
--
-- BEFORE YOU RUN:
--  1. Create the database once:   CREATE DATABASE BankAnalytics;
--  2. Run  sql/01_schema.sql  inside that database (creates the 3 tables).
--  3. Make a folder  C:\Users\HP\Downloads\bank-analytics-project\data\processed\  and COPY these 3 files into it
--     (from data\processed\):  customers_clean.csv, loans.csv, churn_scores.csv
--     Why: the SQL Server service often cannot read your Downloads folder.
--  4. Needs SQL Server 2017 or newer (FORMAT = 'CSV').
--
-- If BULK INSERT gives a permission error, use the wizard instead:
--  right-click the database -> Tasks -> Import Data -> Flat File Source,
--  and load each CSV into the EXISTING table of the same name.
-- =====================================================================

USE BankAnalytics;
GO

-- order matters: customers first (the other tables point to it)
DELETE FROM churn_scores;
DELETE FROM loans;
DELETE FROM customers;
GO

BULK INSERT dbo.customers
FROM 'C:\Users\HP\Downloads\bank-analytics-project\data\processed\customers_clean.csv'
WITH (FORMAT = 'CSV', FIRSTROW = 2, FIELDTERMINATOR = ',', TABLOCK);

BULK INSERT dbo.loans
FROM 'C:\Users\HP\Downloads\bank-analytics-project\data\processed\loans.csv'
WITH (FORMAT = 'CSV', FIRSTROW = 2, FIELDTERMINATOR = ',', TABLOCK);

BULK INSERT dbo.churn_scores
FROM 'C:\Users\HP\Downloads\bank-analytics-project\data\processed\churn_scores.csv'
WITH (FORMAT = 'CSV', FIRSTROW = 2, FIELDTERMINATOR = ',', TABLOCK);
GO

-- check: expect 10000 / ~4300 / 10000 rows
SELECT 'customers' AS table_name, COUNT(*) AS row_count FROM customers
UNION ALL SELECT 'loans',        COUNT(*) FROM loans
UNION ALL SELECT 'churn_scores', COUNT(*) FROM churn_scores;
