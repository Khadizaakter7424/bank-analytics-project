"""
STEP 1 - DATA CLEANING
======================
Input : data/raw/Churn_Modelling.csv   (Kaggle "Bank Customer Churn" dataset)
Output: data/processed/customers_clean.csv

What this script does, in plain words:
  1. Reads the raw CSV file
  2. Drops columns we do not need (row number, surname)
  3. Renames columns to snake_case (easier to use in SQL and Power BI)
  4. Checks for missing values, duplicates and impossible values
  5. Creates "segment" columns (age_group, credit_score_band ...) for analysis
  6. Saves the clean file

Run from the project root folder:
    python python/01_clean_data.py
"""

from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------
# 0. File paths (built from the location of this script, so it
#    works no matter where you run it from)
# ---------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_FILE = BASE_DIR / "data" / "raw" / "Churn_Modelling.csv"
OUT_FILE = BASE_DIR / "data" / "processed" / "customers_clean.csv"

if not RAW_FILE.exists():
    raise SystemExit(
        f"Raw file not found: {RAW_FILE}\n"
        "Download 'Churn_Modelling.csv' from Kaggle (search: Bank Customer Churn) "
        "and put it inside data/raw/"
    )

# ---------------------------------------------------------------
# 1. Read the raw data
# ---------------------------------------------------------------
df = pd.read_csv(RAW_FILE)
print("Raw data shape (rows, columns):", df.shape)
print(df.head(3), "\n")

expected_columns = {
    "RowNumber", "CustomerId", "Surname", "CreditScore", "Geography", "Gender",
    "Age", "Tenure", "Balance", "NumOfProducts", "HasCrCard",
    "IsActiveMember", "EstimatedSalary", "Exited",
}
missing_cols = expected_columns - set(df.columns)
if missing_cols:
    raise SystemExit(f"These columns are missing from the raw file: {missing_cols}")

# ---------------------------------------------------------------
# 2. Drop columns we do not need
#    - RowNumber is just a counter
#    - Surname is personal data and not useful for analysis
# ---------------------------------------------------------------
df = df.drop(columns=["RowNumber", "Surname"])

# ---------------------------------------------------------------
# 3. Rename columns to snake_case
# ---------------------------------------------------------------
df = df.rename(columns={
    "CustomerId": "customer_id",
    "CreditScore": "credit_score",
    "Geography": "geography",
    "Gender": "gender",
    "Age": "age",
    "Tenure": "tenure",
    "Balance": "balance",
    "NumOfProducts": "num_of_products",
    "HasCrCard": "has_cr_card",
    "IsActiveMember": "is_active_member",
    "EstimatedSalary": "estimated_salary",
    "Exited": "exited",
})

# ---------------------------------------------------------------
# 4. Data quality checks
# ---------------------------------------------------------------
print("Missing values per column:")
print(df.isnull().sum(), "\n")

duplicate_ids = df["customer_id"].duplicated().sum()
print("Duplicate customer_id rows:", duplicate_ids)
df = df.drop_duplicates(subset="customer_id")

# Remove stray spaces in text columns
for col in ["geography", "gender"]:
    df[col] = df[col].str.strip()

# Drop rows with missing values (this dataset normally has none)
before = len(df)
df = df.dropna()
print("Rows dropped because of missing values:", before - len(df))

# Sanity checks - the script stops with a clear message if something is wrong
assert df["exited"].isin([0, 1]).all(), "exited must be only 0 or 1"
assert df["has_cr_card"].isin([0, 1]).all(), "has_cr_card must be only 0 or 1"
assert df["is_active_member"].isin([0, 1]).all(), "is_active_member must be only 0 or 1"
assert (df["age"] >= 18).all(), "found a customer younger than 18"
assert (df["balance"] >= 0).all(), "found a negative balance"

# ---------------------------------------------------------------
# 5. Feature engineering: segment columns
#    The "1. ", "2. " prefixes keep the labels in the right order
#    automatically when you sort or chart them in Power BI.
# ---------------------------------------------------------------
df["age_group"] = pd.cut(
    df["age"],
    bins=[0, 29, 39, 49, 59, 120],
    labels=["18-29", "30-39", "40-49", "50-59", "60+"],
).astype(str)

df["credit_score_band"] = pd.cut(
    df["credit_score"],
    bins=[0, 579, 669, 739, 799, 1000],
    labels=["1. Poor", "2. Fair", "3. Good", "4. Very Good", "5. Excellent"],
).astype(str)

df["balance_segment"] = pd.cut(
    df["balance"],
    bins=[-1, 0, 100_000, 150_000, float("inf")],
    labels=["1. Zero", "2. Up to 100K", "3. 100K-150K", "4. Above 150K"],
).astype(str)

df["tenure_group"] = pd.cut(
    df["tenure"],
    bins=[-1, 2, 5, 8, 10],
    labels=["0-2 yrs", "3-5 yrs", "6-8 yrs", "9-10 yrs"],
).astype(str)

df["churn_status"] = df["exited"].map({1: "Churned", 0: "Retained"})

# ---------------------------------------------------------------
# 6. Save
# ---------------------------------------------------------------
OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT_FILE, index=False)

print("\nClean data shape:", df.shape)
print(f"Overall churn rate: {df['exited'].mean():.2%}")
print("Saved to:", OUT_FILE)
