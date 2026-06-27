# Nifty100 Data Foundation

## Overview

This repository contains the Data Foundation layer for the Nifty100 Analytics Project (Progress till D3).

The primary objective of Sprint 1 is to establish a reliable, validated, and standardized data pipeline that supports future analytics, reporting, and visualization requirements.

---

## Project Structure

```text
.
├── data/
│   ├── raw/
│   └── processed/
│
├── scripts/
│   ├── validation/
│   └── ingestion/
│
├── tests/
│
├── validator.py
├── run_validation.py
├── requirements.txt
└── README.md
```

---

## Datasets

The project currently includes the following datasets:

- Companies
- Sectors
- Peer Groups
- Market Capitalization
- Stock Prices
- Balance Sheet
- Profit & Loss
- Cash Flow
- Financial Ratios
- Documents Metadata

---

## Features Implemented

### Sprint 1 – Data Foundation

- Data ingestion setup
- Dataset standardization
- Validation framework
- Duplicate record detection
- Missing value validation
- Schema validation
- Automated testing using PyTest

---

## Installation

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the environment:

### Windows

```bash
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Running Validation

```bash
python run_validation.py
```

---

## Running Tests

```bash
pytest
```

Expected result:

```text
44 passed
```

---

## Current Status

### Completed

- Environment setup
- Dataset ingestion
- Validation framework
- Automated testing

### In Progress

- Data quality improvements
- Documentation enhancements

---

## Author

**Raj Sarania**  
Summer Internship Program (SIP)  
Data Analyst @Bluestock Fintech
