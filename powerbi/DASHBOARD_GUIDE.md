# Dashboard Build Guide (3 pages)

Finish `DAX_MEASURES.md` first. Then build these pages. Save the file as
`powerbi/bank_churn_dashboard.pbix`, and export a screenshot of each page into `images/`
(**File -> Export -> Export to PDF**, or Windows `Win + Shift + S`).

**Design rules that make it look professional**
- One colour family (e.g. blue) + one highlight colour (e.g. orange) for "bad" values only.
- Page background light grey, visuals white, same font everywhere (Segoe UI).
- Every chart title says the insight: "Germany churns almost 2x the average", not "Churn by Geography".
- Align visuals to a grid (View -> Gridlines + Snap to grid). No overlapping.
- Max 4 slicers per page, same position on every page.

---

## Page 1: Executive Overview

| Visual | Fields |
|---|---|
| 5 x **Card** | `Total Customers`, `Churn Rate %`, `Churned Balance`, `Total Loan Amount`, `Default Rate %` |
| **Clustered bar** | Axis `geography`, Values `Churn Rate %` |
| **Clustered column** | Axis `age_group`, Values `Churn Rate %` |
| **Slicers** | `geography`, `gender`, `age_group` |

Tip: add `Overall Churn Rate %` as a **constant line** (Analytics pane -> Constant line, or add it as a second value) so people see which bars are above average.

## Page 2: Churn Deep Dive

| Visual | Fields |
|---|---|
| **Bar** | Axis `num_of_products`, Values `Churn Rate %` |
| **Column** | Axis `is_active_member` (rename 1/0 labels via a small table or just title it "1 = active"), Values `Churn Rate %` |
| **Column** | Axis `credit_score_band`, Values `Churn Rate %` |
| **Column** | Axis `balance_segment`, Values `Churn Rate %` |
| **Matrix** | Rows `geography`, Columns `gender`, Values `Churn Rate %` (Format -> Cell elements -> Background colour -> Gradient) |
| **Image** | Insert `images/feature_importance.png` (Insert -> Image) |

## Page 3: Loan Portfolio & Risk

| Visual | Fields |
|---|---|
| 4 x **Card** | `Total Loans`, `Total Loan Amount`, `Defaulted Amount`, `Default Rate %` |
| **Bar** | Axis `loan_type`, Values `Default Rate %` |
| **Column** | Axis `credit_score_band` (from customers), Values `Default Rate %` |
| **Line** | Axis `loan_start_date` (Year level), Values `Total Loan Amount` |
| **Card** | `Loan Exposure at High Risk` |
| **Table** | `customer_id`, `geography`, `balance`, `churn_probability`. Visual filters: `risk_level` = High, `exited` = 0. Sort by `balance` descending, **Top N = 10** |

The table on this page is your **retention call list**: it is the "so what" of the whole project.

## Finishing touches

1. Rename pages: *Overview*, *Churn Deep Dive*, *Loan & Risk*.
2. **View -> Sync slicers** so the country slicer works on all pages.
3. Add a text box on page 3: "Loan data is simulated for demonstration."
4. Export screenshots as `images/dashboard_page1.png`, `dashboard_page2.png`, `dashboard_page3.png`
   (the README already links to these names).
