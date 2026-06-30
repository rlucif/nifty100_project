# Day 6 Data Quality Review

## Objective

Perform a post-load data quality review of the SQLite database to verify that all datasets were loaded successfully, assess cross-table consistency, investigate data anomalies, and determine whether any issues originated from the ETL pipeline or the source datasets.

---

# Checks Performed

## 1. SQLite Database Verification

Verified that the SQLite database was successfully created and accessible.

Checks performed:

- Database connection
- Table availability
- Post-load verification using `src/etl/dq_review.py`

**Result**

- SQLite database connected successfully.
- All expected tables were present.
- Database structure matched the Sprint 1 implementation.

---

## 2. Table Row Count Verification

Verified the number of records in every SQLite table against the expected dataset counts established after the Day 5 load.

| Dataset          | Status |
| ---------------- | ------ |
| analysis         | PASS   |
| balancesheet     | PASS   |
| cashflow         | PASS   |
| companies        | PASS   |
| documents        | PASS   |
| profitandloss    | PASS   |
| prosandcons      | PASS   |
| financial_ratios | PASS   |
| market_cap       | PASS   |
| peer_groups      | PASS   |
| sectors          | PASS   |
| stock_prices     | PASS   |

**Result**

- All 12 datasets matched the expected row counts.
- No row-count discrepancies were identified.
- The SQLite loader successfully loaded every dataset without record loss.

---

## 3. Company Relationship Validation

Verified the relationship between the master company table and all financial datasets.

Observation:

- `companies.id` stores the business identifier (ticker).
- Financial datasets reference this identifier through the `company_id` column.

Relationship verified:

- companies.id → balancesheet.company_id
- companies.id → cashflow.company_id
- companies.id → profitandloss.company_id
- companies.id → analysis.company_id
- companies.id → documents.company_id
- companies.id → prosandcons.company_id

**Result**

The relationship between master and transactional datasets was confirmed to be consistent across the database.

---

## 4. Manual Data Quality Review

Five companies were randomly selected and manually reviewed.

The review covered:

- Balance Sheet
- Cash Flow
- Profit & Loss
- Analysis
- Documents
- Pros & Cons

The following aspects were verified:

- Presence of financial records
- Reporting-period consistency
- Availability of supporting datasets
- Cross-table record consistency

### Observations

- Financial statements were available for all reviewed companies.
- Annual report records were present as expected.
- The `analysis` dataset was available only for companies included in the files.
- The `prosandcons` dataset contained entries only for a limited number of companies, which is consistent with the dataset.

---

## 5. Time-Series Consistency Review

Reporting periods were compared across the financial statement tables.

Observed characteristics:

- Balance Sheet contains both annual and additional quarterly reporting periods where available (e.g., Sep 2024).
- Profit & Loss includes TTM (Trailing Twelve Months) records for applicable companies.
- Cash Flow primarily contains annual reporting periods.

**Result**

Differences in reporting periods were found to be consistent with the structure of the source datasets and do not indicate ETL issues.

---

## 6. Duplicate Record Investigation

Duplicate records identified during the Day 3 validation process were manually investigated.

Examples reviewed:

- ASIANPAINT (Balance Sheet)
- BAJAJ-AUTO (Cash Flow)

### Findings

Manual inspection showed that each reporting period for the affected companies appeared exactly twice.

Examples:

- Every Balance Sheet year for ASIANPAINT occurred twice.
- Every Cash Flow year for BAJAJ-AUTO occurred twice.

These observations match the duplicate-record counts identified during the Day 3 validation process.

**Conclusion**

The duplicate records originate from the source Excel datasets.

No evidence was found indicating that duplicates were introduced by the SQLite loader or ETL pipeline.

---

# Overall Assessment

The Day 6 review confirms that:

- SQLite database creation completed successfully.
- All 12 datasets were loaded correctly.
- Row counts matched the expected values.
- Company relationships across datasets are consistent.
- Time-series differences reflect source reporting practices rather than ETL defects.
- Duplicate records correspond to known source-data characteristics previously identified during validation.
- No loader defects or database integrity issues were identified during the review.

The SQLite database accurately represents the provided source datasets and is ready for use in Sprint 2 (Financial Ratio Engine).

---

# Status

**PASS**
