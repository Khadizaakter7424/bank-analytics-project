"""
STEP 3 - EXPLORATORY DATA ANALYSIS (EDA)
========================================
Finds WHO is churning and WHERE loans are defaulting, saves charts for the
README, and writes an auto-generated insights file you can paste into README.

Input : data/processed/customers_clean.csv, data/processed/loans.csv
Output: images/*.png   and   reports/key_insights.md

Run:
    python python/03_eda_charts.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # lets matplotlib save images without opening a window
import matplotlib.pyplot as plt
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
CUSTOMERS_FILE = BASE_DIR / "data" / "processed" / "customers_clean.csv"
LOANS_FILE = BASE_DIR / "data" / "processed" / "loans.csv"
IMG_DIR = BASE_DIR / "images"
REPORT_DIR = BASE_DIR / "reports"
IMG_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(exist_ok=True)

if not CUSTOMERS_FILE.exists() or not LOANS_FILE.exists():
    raise SystemExit("Run 01_clean_data.py and 02_generate_loans.py first.")

customers = pd.read_csv(CUSTOMERS_FILE)
loans = pd.read_csv(LOANS_FILE)

# A "flag" column is 1 when the bad thing happened, else 0.
# The average of a 1/0 column is the rate. (mean of exited = churn rate)
loans["is_default"] = (loans["loan_status"] == "Default").astype(int)

# One merge = one SQL JOIN. This attaches customer details to each loan.
loans_cust = loans.merge(customers, on="customer_id", how="left")

# ---- chart colours (one hue, recessive grid, readable text) ----
BAR = "#2F6B9A"
INK = "#1F2937"
MUTED = "#6B7280"
GRID = "#E5E7EB"


def rate_summary(data, column, flag):
    """Count, number of bad events and rate (%) for each group in `column`."""
    out = data.groupby(column)[flag].agg(total="count", events="sum", rate="mean").reset_index()
    out["rate"] = out["rate"] * 100
    return out


def rate_bar(data, column, flag, title, xlabel, filename, rate_name):
    """Draw a bar chart of the rate per group, with the overall rate as a dashed line."""
    summary = rate_summary(data, column, flag)
    overall = data[flag].mean() * 100

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(summary[column].astype(str), summary["rate"], color=BAR, width=0.55)

    # value label on top of every bar (few bars, so labelling all is fine)
    for bar, rate in zip(bars, summary["rate"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.4,
                f"{rate:.1f}%", ha="center", va="bottom", fontsize=10, color=INK)

    ax.axhline(overall, color=MUTED, linestyle="--", linewidth=1)
    ax.text(len(summary) - 0.5, overall + 0.4, f"Overall {overall:.1f}%",
            ha="right", va="bottom", fontsize=9, color=MUTED)

    ax.set_title(title, loc="left", fontsize=13, fontweight="bold", color=INK)
    ax.set_xlabel(xlabel, color=MUTED)
    ax.set_ylabel(rate_name, color=MUTED)
    ax.set_ylim(0, summary["rate"].max() * 1.2)
    ax.yaxis.grid(True, color=GRID)
    ax.set_axisbelow(True)
    for side in ["top", "right", "left"]:
        ax.spines[side].set_visible(False)
    ax.tick_params(colors=MUTED, length=0)
    plt.xticks(rotation=0)
    fig.tight_layout()
    fig.savefig(IMG_DIR / filename, dpi=150)
    plt.close(fig)
    return summary


# ---------------------------------------------------------------
# Churn charts
# ---------------------------------------------------------------
customers["activity"] = customers["is_active_member"].map({1: "Active member", 0: "Inactive member"})
customers["products"] = customers["num_of_products"].astype(str) + " product(s)"

churn_views = [
    ("geography", "Churn rate by country", "Country", "churn_by_geography.png"),
    ("age_group", "Churn rate by age group", "Age group", "churn_by_age_group.png"),
    ("products", "Churn rate by number of products", "Products held", "churn_by_products.png"),
    ("activity", "Churn rate: active vs inactive members", "", "churn_by_activity.png"),
    ("credit_score_band", "Churn rate by credit score band", "Credit score band", "churn_by_credit_band.png"),
    ("gender", "Churn rate by gender", "Gender", "churn_by_gender.png"),
]
churn_summaries = {}
for col, title, xlabel, fname in churn_views:
    churn_summaries[col] = rate_bar(customers, col, "exited", title, xlabel, fname, "Churn rate (%)")

# ---------------------------------------------------------------
# Loan charts (simulated loan data)
# ---------------------------------------------------------------
loan_type_summary = rate_bar(loans, "loan_type", "is_default",
                             "Loan default rate by loan type", "Loan type",
                             "default_by_loan_type.png", "Default rate (%)")
loan_credit_summary = rate_bar(loans_cust, "credit_score_band", "is_default",
                               "Loan default rate by customer credit band", "Credit score band",
                               "default_by_credit_band.png", "Default rate (%)")

# ---------------------------------------------------------------
# Auto-written insights (numbers come straight from the data)
# ---------------------------------------------------------------
overall_churn = customers["exited"].mean() * 100
overall_default = loans["is_default"].mean() * 100


def highest(summary, column):
    row = summary.loc[summary["rate"].idxmax()]
    return row[column], row["rate"]


geo_name, geo_rate = highest(churn_summaries["geography"], "geography")
age_name, age_rate = highest(churn_summaries["age_group"], "age_group")
prod_name, prod_rate = highest(churn_summaries["products"], "products")
cred_name, cred_rate = highest(churn_summaries["credit_score_band"], "credit_score_band")
gender_name, gender_rate = highest(churn_summaries["gender"], "gender")

act = churn_summaries["activity"].set_index("activity")["rate"]
churned_balance = customers.loc[customers["exited"] == 1, "balance"].sum()
churned_balance_share = churned_balance / customers["balance"].sum() * 100

type_name, type_rate = highest(loan_type_summary, "loan_type")
dcred_name, dcred_rate = highest(loan_credit_summary, "credit_score_band")
defaulted_amount = loans.loc[loans["is_default"] == 1, "loan_amount"].sum()

lines = [
    "# Key Insights (auto-generated by python/03_eda_charts.py)",
    "",
    "## Customer churn (real Kaggle data)",
    f"- Overall churn rate is **{overall_churn:.1f}%** ({int(customers['exited'].sum()):,} of {len(customers):,} customers left).",
    f"- **{geo_name}** has the highest churn by country: **{geo_rate:.1f}%** vs {overall_churn:.1f}% overall.",
    f"- Age group **{age_name}** churns the most: **{age_rate:.1f}%**.",
    f"- Customers with **{prod_name}** churn at **{prod_rate:.1f}%**, the highest of any product count.",
    f"- Inactive members churn at **{act.get('Inactive member', float('nan')):.1f}%** vs "
    f"{act.get('Active member', float('nan')):.1f}% for active members.",
    f"- Highest churn credit band: **{cred_name}** ({cred_rate:.1f}%). Highest churn gender: **{gender_name}** ({gender_rate:.1f}%).",
    f"- Churned customers held **{churned_balance_share:.1f}%** of all balances "
    f"({churned_balance:,.0f} in total), which is the money that walked out.",
    "",
    "## Loan portfolio (SIMULATED loan data, see README)",
    f"- {len(loans):,} loans across {loans['customer_id'].nunique():,} customers, total value {loans['loan_amount'].sum():,.0f}.",
    f"- Overall default rate is **{overall_default:.1f}%**; defaulted amount is {defaulted_amount:,.0f}.",
    f"- **{type_name}** loans default the most: **{type_rate:.1f}%**.",
    f"- Customers in credit band **{dcred_name}** default the most: **{dcred_rate:.1f}%**.",
    "",
    "> Loan numbers come from a simulation with built-in rules, so treat them as an illustration of the method, not as findings about real banks.",
]
(REPORT_DIR / "key_insights.md").write_text("\n".join(lines), encoding="utf-8")

print("\n".join(lines))
print("\nCharts saved in:", IMG_DIR)
print("Insights saved in:", REPORT_DIR / "key_insights.md")
