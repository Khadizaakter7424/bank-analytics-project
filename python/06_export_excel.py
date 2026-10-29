"""
STEP 6 - BUILD THE EXCEL WORKBOOK
=================================
Creates excel/bank_analytics_summary.xlsx with:
  * "KPI Summary" sheet: every number is a LIVE EXCEL FORMULA
    (COUNTIF, COUNTIFS, SUMIF, AVERAGE ...) that reads the data sheets,
    so you can click any cell and see how it is calculated.
  * "Customers" and "Loans" sheets: the cleaned data.

After this, follow excel/EXCEL_GUIDE.md to add Pivot Tables and charts.

Run:
    python python/06_export_excel.py
"""

from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.formatting.rule import DataBarRule
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED = BASE_DIR / "data" / "processed"
OUT_FILE = BASE_DIR / "excel" / "bank_analytics_summary.xlsx"

for f in ["customers_clean.csv", "loans.csv"]:
    if not (PROCESSED / f).exists():
        raise SystemExit(f"Missing {f}. Run steps 01 and 02 first.")

customers = pd.read_csv(PROCESSED / "customers_clean.csv")
loans = pd.read_csv(PROCESSED / "loans.csv")

# ---------- styles ----------
FONT = "Arial"
f_normal = Font(name=FONT, size=10)
f_bold = Font(name=FONT, size=10, bold=True)
f_title = Font(name=FONT, size=16, bold=True, color="1F2937")
f_section = Font(name=FONT, size=12, bold=True, color="1F2937")
f_header = Font(name=FONT, size=10, bold=True, color="FFFFFF")
f_note = Font(name=FONT, size=9, italic=True, color="6B7280")
fill_header = PatternFill("solid", start_color="2F6B9A")


def col_range(sheet, df, column):
    """Return a range like Customers!$L$2:$L$10001 for a column name."""
    letter = get_column_letter(list(df.columns).index(column) + 1)
    return f"{sheet}!${letter}$2:${letter}${len(df) + 1}"


# Ranges used by the formulas
C_ID = col_range("Customers", customers, "customer_id")
C_GEO = col_range("Customers", customers, "geography")
C_AGE = col_range("Customers", customers, "age")
C_AGEGRP = col_range("Customers", customers, "age_group")
C_BAL = col_range("Customers", customers, "balance")
C_SCORE = col_range("Customers", customers, "credit_score")
C_PROD = col_range("Customers", customers, "num_of_products")
C_ACTIVE = col_range("Customers", customers, "is_active_member")
C_EXITED = col_range("Customers", customers, "exited")
L_ID = col_range("Loans", loans, "loan_id")
L_TYPE = col_range("Loans", loans, "loan_type")
L_AMT = col_range("Loans", loans, "loan_amount")
L_RATE = col_range("Loans", loans, "interest_rate")
L_STATUS = col_range("Loans", loans, "loan_status")

wb = Workbook()
ws = wb.active
ws.title = "KPI Summary"
ws.sheet_view.showGridLines = False

ws["A1"] = "Bank Customer Churn & Loan Portfolio - KPI Summary"
ws["A1"].font = f_title
ws["A2"] = "Every number below is a live formula on the Customers and Loans sheets. Loan data is simulated."
ws["A2"].font = f_note

row = 4


def kpi_block(title, items, start_row):
    """items = list of (label, formula, number_format)."""
    ws.cell(start_row, 1, title).font = f_section
    r = start_row + 1
    for label, formula, fmt in items:
        ws.cell(r, 1, label).font = f_normal
        c = ws.cell(r, 2, formula)
        c.font = f_bold
        c.number_format = fmt
        c.alignment = Alignment(horizontal="right")
        r += 1
    return r + 1


def group_block(title, label_header, groups, crit_range, event_range_formula, start_row, extra=None):
    """
    A small table: label | total | events | rate.
    groups = list of (label, criterion). A criterion starting with '$A' means
    'use the label cell'; otherwise it is written into the formula as-is (e.g. 1 or 0).
    """
    ws.cell(start_row, 1, title).font = f_section
    hdr = start_row + 1
    headers = [label_header, "Total", "Events", "Rate"]
    for i, h in enumerate(headers, start=1):
        c = ws.cell(hdr, i, h)
        c.font, c.fill = f_header, fill_header
        c.alignment = Alignment(horizontal="center")
    first = hdr + 1
    r = first
    for label, crit in groups:
        crit_expr = f"$A{r}" if crit == "label" else crit
        ws.cell(r, 1, label).font = f_normal
        ws.cell(r, 2, f"=COUNTIF({crit_range},{crit_expr})")
        ws.cell(r, 3, event_range_formula(crit_expr))
        ws.cell(r, 4, f"=IF(B{r}=0,0,C{r}/B{r})")
        for ci in (2, 3):
            ws.cell(r, ci).number_format = "#,##0"
            ws.cell(r, ci).font = f_normal
        ws.cell(r, 4).number_format = "0.0%"
        ws.cell(r, 4).font = f_bold
        r += 1
    ws.conditional_formatting.add(
        f"D{first}:D{r - 1}",
        DataBarRule(start_type="num", start_value=0, end_type="num", end_value=1, color="9DC3E6"),
    )
    return r + 1


# ---------- Section 1: customer KPIs ----------
row = kpi_block("1. Customer KPIs", [
    ("Total customers", f"=COUNTA({C_ID})", "#,##0"),
    ("Churned customers", f"=SUM({C_EXITED})", "#,##0"),
    ("Churn rate", "=B6/B5", "0.0%"),
    ("Average balance", f"=AVERAGE({C_BAL})", "#,##0.00"),
    ("Average credit score", f"=AVERAGE({C_SCORE})", "0"),
    ("Average age", f"=AVERAGE({C_AGE})", "0.0"),
], row)

# ---------- Section 2: churn tables ----------
churned_in = lambda crit_range: (lambda crit: f"=COUNTIFS({crit_range},{crit},{C_EXITED},1)")

geos = sorted(customers["geography"].unique())
row = group_block("2. Churn by country", "Country", [(g, "label") for g in geos],
                  C_GEO, churned_in(C_GEO), row)

ages = sorted(customers["age_group"].unique())
row = group_block("3. Churn by age group", "Age group", [(a, "label") for a in ages],
                  C_AGEGRP, churned_in(C_AGEGRP), row)

prods = sorted(customers["num_of_products"].unique())
row = group_block("4. Churn by number of products", "Products", [(int(p), "label") for p in prods],
                  C_PROD, churned_in(C_PROD), row)

row = group_block("5. Churn: active vs inactive members", "Member type",
                  [("Active member", "1"), ("Inactive member", "0")],
                  C_ACTIVE, churned_in(C_ACTIVE), row)

# ---------- Section 3: loan KPIs ----------
loan_kpi_start = row
row = kpi_block("6. Loan portfolio KPIs (simulated data)", [
    ("Total loans", f"=COUNTA({L_ID})", "#,##0"),
    ("Total loan amount", f"=SUM({L_AMT})", "#,##0"),
    ("Average interest rate (%)", f"=AVERAGE({L_RATE})", "0.00"),
    ("Defaulted loans", f'=COUNTIF({L_STATUS},"Default")', "#,##0"),
    ("Default rate", f"=B{loan_kpi_start + 4}/B{loan_kpi_start + 1}", "0.0%"),
    ("Defaulted amount", f'=SUMIF({L_STATUS},"Default",{L_AMT})', "#,##0"),
], row)

# ---------- Section 4: default by loan type ----------
types = sorted(loans["loan_type"].unique())
row = group_block(
    "7. Default rate by loan type", "Loan type", [(t, "label") for t in types], L_TYPE,
    lambda crit: f'=COUNTIFS({L_TYPE},{crit},{L_STATUS},"Default")', row,
)

ws.column_dimensions["A"].width = 34
for letter in "BCD":
    ws.column_dimensions[letter].width = 14

# ---------- Data sheets ----------
def write_df(sheet_name, df):
    sheet = wb.create_sheet(sheet_name)
    sheet.append(list(df.columns))
    for rec in df.itertuples(index=False):
        sheet.append(list(rec))
    for c in sheet[1]:
        c.font, c.fill = f_header, fill_header
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    for i, name in enumerate(df.columns, start=1):
        sheet.column_dimensions[get_column_letter(i)].width = max(12, len(name) + 3)


write_df("Customers", customers)
write_df("Loans", loans)

OUT_FILE.parent.mkdir(exist_ok=True)
wb.save(OUT_FILE)
print("Saved:", OUT_FILE)
print("Open it in Excel. If the numbers look empty, press F9 (recalculate).")
