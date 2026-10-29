# Excel Guide

`python python/06_export_excel.py` creates **`bank_analytics_summary.xlsx`** with three sheets:

| Sheet | What it has |
|---|---|
| **KPI Summary** | Live formulas: customer KPIs, churn by country / age / products / activity, loan KPIs, default rate by loan type |
| **Customers** | Cleaned customer data (filters and frozen header already on) |
| **Loans** | Loan data (simulated) |

Open the file and click any number on *KPI Summary*: the formula bar shows how it is calculated.
If cells look empty, press **F9** once.

## Formulas used (good interview talking points)

| Formula | Used for |
|---|---|
| `COUNTA`, `SUM`, `AVERAGE` | headline KPIs |
| `COUNTIF(range, value)` | customers in a group (e.g. all of Germany) |
| `COUNTIFS(range1, v1, range2, v2)` | customers in a group **and** churned |
| `SUMIF` | defaulted loan amount |
| `IF(B=0, 0, C/B)` | safe division for rates |

## Add Pivot Tables (about 15 minutes)

**Pivot 1: churn rate by country and gender**
1. Go to *Customers* -> click any cell -> **Insert -> PivotTable** -> New Worksheet.
2. Rows: `geography`. Columns: `gender`. Values: `exited` -> **Average** (right-click -> Value Field Settings -> Average).
3. Format values as **Percentage** (Value Field Settings -> Number Format).

**Pivot 2: churn by age group and products**
Rows `age_group`, Columns `num_of_products`, Values `exited` -> Average.
Add **Conditional Formatting -> Color Scales** so the risky cells glow red.

**Pivot 3: loans**
On the *Loans* sheet: Rows `loan_type`, Columns `loan_status`, Values `loan_amount` -> Sum.

## Add charts

Select a pivot -> **PivotTable Analyze -> PivotChart** -> clustered column.
Add a **Slicer** for `geography` (PivotTable Analyze -> Insert Slicer) and connect it to all pivots
(right-click slicer -> Report Connections).

## Name and save

Rename the pivot sheets: `Pivot_Churn_Geo`, `Pivot_Churn_Age`, `Pivot_Loans`.
Save into this folder (`excel/`). Excel files up to 100 MB are fine on GitHub.
