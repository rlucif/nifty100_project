# Sprint 2 Retrospective

## N100 Financial Intelligence Platform

**Sprint:** Sprint 2 - Financial Ratio Engine (Days 8-14)

**Status:** Completed
**Prepared On:** Day 14

---

# Purpose

This retrospective summarizes the decisions, technical finding, implementation outcomes, and lesson learned during Sprint 2.

This document captures why certain decisions were made, what technical debt remains, and the recommendations carried forward into Sprint 3.

---

# Sprint Objective

Sprint 2 focused on transforming validated financial statement data into a reusable Financial Ratio Engine capable of producing standardized investment KPIs for the N100 Financial Intelligence Platform.

Primary Objectives:

- Develop reusable financial ratio calculation modules.
- Populate the `financial_ratio` SQLite table.
- Validate calculations against sources datasets.
- Handle real world financial edge cases.
- Produce a reliable analytics foundation for later platform modules.

---

# Objective Achieved

## Ratio Engine

Successfully implemented:

### Profitability

- Net profit margin
- Operating profit margin
- Return on Equity
- Return on capital employed (validation)

### Leverage

- debt-to-equity
- interest coverage
- net debt

### Efficiency

- Asset turnover

### Cash Flow KPIs

- Free cash flow
- CFO quality score
- capital allocation classification
- CapEx intensity
- FCF conversion

---

## CAGR Engine

Implemented reusable CAGR calculations for:

- Revenue CAGR
- PAT CAGR
- EPS CAGR

Supported business scenarios includes:

- Zero base
- company turnaround
- Decline into less
- Both values negative
- Invalid year handling

The CAGR engine had been fully unit tested and is ready for integration when schema requirements include CAGR persistence.

---

# Major Decisions

## Operating Profit Margin

The supplied `opm_percentage` dataset contained widespread inconsistencies.

Decision:

- Ignore dataset OPM values.
- Compute OPM using:

```
Operating Profit / Sales * 100
```

This becomes the production implementation.

---

## Book Values Per Share

Book value calculations could not be reproduce consistently from available financial statements.

Decision:

- Use `companies.book_value`
- Document the Limitation.
- Avoid introducing unsupported calculations.

---

## Database Join Strategy

Final implementation:

- INNER JOIN
  - Profit & Loss
  - Balance Sheet
  - Cash Flow
- LEFT JOIN
  - companies

This preserves financial integrity while allowing incomplete company metadata.

---

## Duplicate Records

Duplicate company-year records were investigated.

Conclusion:

Duplicate originate from the supplied dataset rather than the implementation.

Decision:

- Preserve duplicates.
- Do not silently modify source data.

---

# Financial Institutions

git
Debt-to-Equity warning flags are suppressed for Banks, NBFCs and Insurance companies where high leverage is structurally normal.

ROCE calculations are retained for validation but are not currently persisted because the existing schema does not contain a ROCE field.

---

# Major Dataset Findings

Sprint 2 identified several issues originating form the supplied datasets rather than the implementation.

Confirmed findings include:

- Corrupted operating profit margin values
- Missing companies
- Orphan company IDs
- Duplicate company-year records
- Missing financial fields
- Book values ambiguity
- Accounting inconsistencies

These findings are documented separately within the Sprint 2 data quality audit report.

---

# Testing Summary

Sprint 2 completed with:

- 109/109 automated test passing

Coverage includes:

- Ratio calculations
- validator
- ETL
- CAGR
- Financial edge cases

---

# Technical Debt

The following items are intentionally deferred to future sprints.

## CAGR Integration

The CAGR analytics module has been implemented and fully tested.
Integration into the ETL pipeline has been deferred because the current `financial_ratios` schema does not contains CARG fields.

---

## Configuration

Current implementation contains hardcoded configuration values such as the SQLite database path.
Future work should migrate configuration into environment variables or a dedicated configuration module.

---

## Repository Cleanup

Future repository maintenance should include:

- Remove unused imports after confirming future integration plans.
- Ignore `__pycache__` directories in version control.
- Apply automated formatting tools (Black/Ruff) when appropriate.

These are maintainability improvements and are not Sprint 2 blockers.

---

## Function Naming

`calculate_profitability_kpi()` currently computes profitability, leverage, efficiency and cash flow KPIs.

A Future refactor should rename the function to better reflects its responsibilities.

---

# Lesson Learned

Sprint 2 reinforced several engineering principles.

- Never assume supplied financial datasets are correct.
- Validate business formulas independently of source data.
- Separate analytics logic from ETL orchestration.
- Document engineering decisions rather than silently applying workarounds.
- Build edge-case handling into the implementation rather than fixing failures after deployment.

---

# Recommendation for Sprint 3

Sprint 3 should focus on consuming the validated analytics layer rather than modifying it.

Recommendation priorities:

1. Screener Engine
2. Peer comparison
3. Health Intelligence

The Ratio Ending should now be treated as a dependency unless defects are discovered.

---

# Sprint 2 Outcome

Sprint 2 successfully established the analytics foundation of the N100 Financial Ratio Engine has been implemented, validated, documented and tested. Major dataset inconsistencies have been investigated and engineering decision have been recorded.

The project is now ready o progress to Sprint 3.

---

# Final Sign-Off

| Area                | Status    |
| ------------------- | --------- |
| Sprint Objective    | Completed |
| Ratio Engine        | Completed |
| Database Population | Completed |
| Data Validation     | Completed |
| Edge Case Handling  | Completed |
| Automated Testing   | 109/109   |
| Documentation       | Completed |
| Critical Issues     | None      |
