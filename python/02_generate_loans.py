"""
STEP 2 - CREATE A (SIMULATED) LOAN TABLE
========================================
The Kaggle churn dataset has NO loan information. To build a "Loan Portfolio"
analysis we create a realistic SIMULATED loans table linked to customers
through customer_id (one customer can have 0, 1 or 2 loans).

IMPORTANT: this table is synthetic. Say so clearly in your README and in
interviews. It is a normal practice for portfolio projects, as long as you are
honest about it. The random seed is fixed, so everyone gets the same data.

Input : data/processed/customers_clean.csv
Output: data/processed/loans.csv

Run:
    python python/02_generate_loans.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
CUSTOMERS_FILE = BASE_DIR / "data" / "processed" / "customers_clean.csv"
OUT_FILE = BASE_DIR / "data" / "processed" / "loans.csv"

SEED = 42                                 # same seed -> same data every time
AS_OF_DATE = pd.Timestamp("2025-12-31")   # "today" inside the simulated world

if not CUSTOMERS_FILE.exists():
    raise SystemExit("Run python/01_clean_data.py first.")

customers = pd.read_csv(CUSTOMERS_FILE)
rng = np.random.default_rng(SEED)

# ---------------------------------------------------------------
# 1. Decide which customers have a loan
#    Better credit score and more products -> a bit more likely.
# ---------------------------------------------------------------
p_loan = (
    0.25
    + 0.12 * (customers["credit_score"] >= 650)
    + 0.10 * (customers["num_of_products"] >= 2)
)
has_loan = rng.random(len(customers)) < p_loan
borrowers = customers[has_loan]

# 80% of borrowers have 1 loan, 20% have 2 loans
n_loans = rng.choice([1, 2], size=len(borrowers), p=[0.8, 0.2])
loans = borrowers.loc[
    borrowers.index.repeat(n_loans),
    ["customer_id", "credit_score", "estimated_salary", "is_active_member"],
].reset_index(drop=True)
n = len(loans)

# ---------------------------------------------------------------
# 2. Loan type and loan terms
# ---------------------------------------------------------------
loan_types = ["Personal", "Home", "Auto", "Business", "Education"]
loans["loan_type"] = rng.choice(loan_types, size=n, p=[0.30, 0.20, 0.25, 0.15, 0.10])

# For each type: loan size as a multiple of salary, base interest rate, tenures
settings = {
    "Personal":  {"salary_mult": 0.5, "base_rate": 11.0, "tenures": [12, 24, 36, 48, 60]},
    "Home":      {"salary_mult": 4.0, "base_rate": 6.0,  "tenures": [120, 180, 240, 300, 360]},
    "Auto":      {"salary_mult": 1.5, "base_rate": 8.0,  "tenures": [24, 36, 48, 60, 72]},
    "Business":  {"salary_mult": 2.5, "base_rate": 10.0, "tenures": [24, 36, 60, 84]},
    "Education": {"salary_mult": 0.8, "base_rate": 7.0,  "tenures": [36, 60, 84, 120]},
}

loans["loan_amount"] = 0.0
loans["interest_rate"] = 0.0
loans["tenure_months"] = 0

for loan_type, cfg in settings.items():
    mask = loans["loan_type"] == loan_type
    k = int(mask.sum())
    salary = loans.loc[mask, "estimated_salary"]
    credit = loans.loc[mask, "credit_score"]

    loans.loc[mask, "loan_amount"] = salary * cfg["salary_mult"] * rng.uniform(0.6, 1.4, k)
    # lower credit score -> higher interest rate
    loans.loc[mask, "interest_rate"] = cfg["base_rate"] + (700 - credit) / 100 + rng.normal(0, 0.5, k)
    loans.loc[mask, "tenure_months"] = rng.choice(cfg["tenures"], size=k)

loans["loan_amount"] = ((loans["loan_amount"] / 100).round() * 100).clip(lower=1000)
loans["interest_rate"] = loans["interest_rate"].clip(3, 22).round(2)
loans["tenure_months"] = loans["tenure_months"].astype(int)

# ---------------------------------------------------------------
# 3. Start date
# ---------------------------------------------------------------
start_min = pd.Timestamp("2021-01-01")
start_max = pd.Timestamp("2025-06-30")
days_range = (start_max - start_min).days
loans["loan_start_date"] = start_min + pd.to_timedelta(
    rng.integers(0, days_range + 1, size=n), unit="D"
)

# ---------------------------------------------------------------
# 4. Loan status: Default / Closed / Active
#    Default chance goes UP when: credit score is low, the loan is large
#    compared with salary, or the customer is not an active member.
# ---------------------------------------------------------------
loan_to_salary = (loans["loan_amount"] / loans["estimated_salary"].clip(lower=1000)).clip(upper=6)
z = (
    -3.2
    - 0.006 * (loans["credit_score"] - 650)
    + 0.35 * loan_to_salary
    + 0.30 * (loans["is_active_member"] == 0)
)
p_default = 1 / (1 + np.exp(-z))
is_default = rng.random(n) < p_default

months_elapsed = (AS_OF_DATE - loans["loan_start_date"]).dt.days / 30.44
is_closed = months_elapsed >= loans["tenure_months"]

loans["loan_status"] = np.where(is_default, "Default", np.where(is_closed, "Closed", "Active"))

# Days past due: defaulted loans are 90+ days late; some active loans are slightly late
dpd = np.zeros(n, dtype=int)
default_mask = (loans["loan_status"] == "Default").to_numpy()
dpd[default_mask] = rng.integers(90, 366, size=default_mask.sum())
active_mask = (loans["loan_status"] == "Active").to_numpy()
late_active = active_mask & (rng.random(n) < 0.10)
dpd[late_active] = rng.integers(1, 61, size=late_active.sum())
loans["days_past_due"] = dpd

# ---------------------------------------------------------------
# 5. Final tidy-up and save
# ---------------------------------------------------------------
loans = loans.sort_values("loan_start_date").reset_index(drop=True)
loans["loan_id"] = ["L" + str(i).zfill(5) for i in range(1, n + 1)]
loans["loan_start_date"] = loans["loan_start_date"].dt.strftime("%Y-%m-%d")

loans = loans[[
    "loan_id", "customer_id", "loan_type", "loan_amount", "interest_rate",
    "tenure_months", "loan_start_date", "loan_status", "days_past_due",
]]
loans.to_csv(OUT_FILE, index=False)

print(f"Loans created: {len(loans):,} for {loans['customer_id'].nunique():,} customers")
print(f"Overall default rate: {(loans['loan_status'] == 'Default').mean():.2%}")
print("\nLoans by status:")
print(loans["loan_status"].value_counts())
print("\nSaved to:", OUT_FILE)
