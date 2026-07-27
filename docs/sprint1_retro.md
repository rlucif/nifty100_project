# Sprint 1 Retrospective

## Sprint Objective

Sprint 1 focused on establishing the data foundation for the N100 Financial Intelligence Platform. The primary objectives were to ingest the provided Excel datasets, validate data quality, normalize key fields, build a SQLite warehouse, and prepare the project for downstream financial analytics.

---

## Work Completed

- Implemented Excel data loading for all provided datasets.
- Developed normalization logic for company identifiers and reporting periods.
- Built automated data validation checks.
- Generated validation reports for failed records.
- Designed and implemented the SQLite database schema.
- Loaded all datasets into the SQLite database.
- Generated load audit reports.
- Performed manual data quality review on sampled companies.
- Created exploratory SQL queries for database validation and data exploration.
- Achieved successful execution of all unit tests (44 passed).

---

## Key Findings

- The Companies master dataset contains 92 companies, while certain financial datasets include additional company IDs.
- The Analysis dataset intentionally provides partial company coverage.
- Reporting periods include both annual financial statements and TTM (Trailing Twelve Months) values.
- Duplicate company-year records were identified for Adani Ports in the Profit & Loss dataset and documented through exploratory SQL.

---

## Challenges

- Understanding relationships between multiple datasets and establishing appropriate company mappings.
- Handling varying reporting period formats across companies.
- Distinguishing between expected source-data characteristics and genuine data quality issues.
- Ensuring all ETL and validation processes remained reproducible through automated testing.

---

## Lessons Learned

- Validate source data before modifying transformation logic.
- Separate exploratory findings from implementation changes.
- Use automated validation alongside manual data quality review.
- Maintain a consistent project structure to support future sprint development.

---

## Sprint Outcome

Sprint 1 objectives were successfully achieved. The project now has a validated SQLite database, automated ETL pipeline, data validation framework, audit reports, and exploratory SQL documentation, providing a stable foundation for Sprint 2 development.
