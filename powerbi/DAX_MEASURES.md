# DAX Measures (copy and paste)

You do not need to *know* DAX to use these. Each measure is one line you paste into Power BI.
Short idea of DAX: a **measure** is a formula that recalculates for whatever the user has
clicked or filtered (a country, an age group ...). That is why one card can show different numbers
on different charts.

## Before you start: load the data

1. Power BI Desktop -> **Home -> Get data -> Text/CSV**.
2. Load these two files from `data/processed/`:
   - `customers_scored.csv`  -> rename the table to **customers**
   - `loans.csv`             -> rename the table to **loans**
   (Rename in Power Query: click the query, change the **Name** box on the right.)
3. Check data types (Transform data): `loan_start_date` = **Date**, `balance` / `loan_amount` /
   `estimated_salary` = **Fixed decimal** or **Decimal**, `exited` and `is_active_member` = **Whole number**.
4. **Model view**: drag `customers[customer_id]` onto `loans[customer_id]`.
   It must be **One (customers) to Many (loans)**, cross-filter direction **Single**.

## Where to paste the measures

1. **Home -> Enter data** -> make an empty table named `_Measures` (just to keep measures tidy).
2. Right-click `_Measures` -> **New measure** -> paste ONE block below -> Enter. Repeat for each.
3. Set the format in **Measure tools**: percentages as `%` (1 decimal), money as `#,0`.

---

## A. Customer measures

```DAX
Total Customers = COUNTROWS ( customers )
```

```DAX
Churned Customers =
CALCULATE ( COUNTROWS ( customers ), customers[exited] = 1 )
```

```DAX
Retained Customers = [Total Customers] - [Churned Customers]
```

```DAX
Churn Rate % = DIVIDE ( [Churned Customers], [Total Customers] )
```

```DAX
Overall Churn Rate % =
CALCULATE ( [Churn Rate %], ALL ( customers ) )
```
*ALL removes the filters, so this is always the bank-wide rate. Use it as a reference line.*

```DAX
Churn Gap vs Overall = [Churn Rate %] - [Overall Churn Rate %]
```
*Positive = this group churns MORE than the bank average. Great for conditional colouring.*

```DAX
Total Balance = SUM ( customers[balance] )
```

```DAX
Avg Balance = AVERAGE ( customers[balance] )
```

```DAX
Churned Balance =
CALCULATE ( SUM ( customers[balance] ), customers[exited] = 1 )
```

```DAX
Churned Balance % = DIVIDE ( [Churned Balance], [Total Balance] )
```

```DAX
Avg Credit Score = AVERAGE ( customers[credit_score] )
```

```DAX
Active Member % =
DIVIDE (
    CALCULATE ( COUNTROWS ( customers ), customers[is_active_member] = 1 ),
    [Total Customers]
)
```

## B. Loan measures

```DAX
Total Loans = COUNTROWS ( loans )
```

```DAX
Total Loan Amount = SUM ( loans[loan_amount] )
```

```DAX
Avg Interest Rate = AVERAGE ( loans[interest_rate] )
```

```DAX
Defaulted Loans =
CALCULATE ( COUNTROWS ( loans ), loans[loan_status] = "Default" )
```

```DAX
Default Rate % = DIVIDE ( [Defaulted Loans], [Total Loans] )
```

```DAX
Defaulted Amount =
CALCULATE ( SUM ( loans[loan_amount] ), loans[loan_status] = "Default" )
```

```DAX
Active Loan Exposure =
CALCULATE ( SUM ( loans[loan_amount] ), loans[loan_status] = "Active" )
```

```DAX
Customers With Loan = DISTINCTCOUNT ( loans[customer_id] )
```

```DAX
Loan Penetration % = DIVIDE ( [Customers With Loan], [Total Customers] )
```

## C. Risk measures (use the ML model's output)

```DAX
High Risk Customers =
CALCULATE ( COUNTROWS ( customers ), customers[risk_level] = "High", customers[exited] = 0 )
```
*Customers the model flags as High risk who are still with the bank = the retention call list.*

```DAX
Avg Churn Probability = AVERAGE ( customers[churn_probability] )
```

```DAX
Loan Exposure at High Risk =
CALCULATE (
    SUM ( loans[loan_amount] ),
    loans[loan_status] = "Active",
    customers[risk_level] = "High",
    customers[exited] = 0
)
```
*Active loan money held by customers who are likely to leave. Works because the relationship
passes the customer filter to the loans table.*

## Quick test

Put `Total Customers`, `Churn Rate %` and `Default Rate %` in three **Card** visuals.
Check them against `reports/key_insights.md` or the Excel KPI sheet. If the numbers match, your
model and measures are correct.

## Common problems

| Problem | Fix |
|---|---|
| Measure shows the same number everywhere | Relationship missing or wrong direction, check Model view |
| `loans` visuals ignore the country slicer | Relationship must be customers (One) -> loans (Many) |
| Percent shows `0.2037` | Select the measure -> Measure tools -> Format -> Percentage |
| Age groups / credit bands in odd order | The labels already contain `1.`, `2.` prefixes: sort the axis **Ascending by that field** |
