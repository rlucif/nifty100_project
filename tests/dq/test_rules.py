import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from src.analytics.periods import period_sort_key
from src.etl.validator import (
   check_company_id_uppercase,
   check_duplicate_columns,
   check_duplicate_records,
   check_empty_rows,
   check_null_company_id,
   check_null_year,
   check_required_columns,
   check_unexpected_columns
)

DB_PATH = Path('data/nifty100.db')

MINIMUM_RATIO_ROWS = 1100
EXPECTED_PEER_GROUPS = 11

# Tickers present in the financial statements but absent from the truncated companies.xlsx master. Documented in the Sprint 2 audit.
KNOWN_ORPHAN_COMPANY_IDS = {'ULTRACEMCO', 'UNIONBANK'}

KPI_COLUMNS = [
   'net_profit_margin_pct',
   'operating_profit_margin_pct',
   'return_on_equity_pct',
   'debt_to_equity',
   'interest_coverage',
   'asset_turnover',
   'free_cash_flow_cr',
   'capex_cr',
   'earnings_per_share',
   'book_value_per_share',
   'dividend_payout_ratio_pct',
   'total_debt_cr',
   'cash_from_operations_cr',
   'revenue_cagr_5yr',
   'pat_cagr_5yr',
   'eps_cagr_5yr',
   'composite_quality_score'
]


@pytest.fixture(scope='module')
def connection():
   if not DB_PATH.exists():
      pytest.skip('data/nifty100.db is not present')

   database = sqlite3.connect(DB_PATH)
   yield database
   database.close()


@pytest.fixture(scope='module')
def financial_ratios(connection):
   return pd.read_sql('SELECT * FROM financial_ratios', connection)


def test_dq_rule_01_required_columns_present():
   frame = pd.DataFrame({'company_id': ['TCS'], 'year': ['Mar 2024']})

   assert check_required_columns(frame, ['company_id', 'year']) == []
   assert check_required_columns(frame, ['company_id', 'sales']) != []


def test_dq_rule_02_no_duplicate_columns():
   clean = pd.DataFrame({'company_id': ['TCS'], 'year': ['Mar 2024']})
   duplicated = pd.DataFrame(
      [['TCS', 'Mar 2024']],
      columns=['company_id', 'company_id']
   )

   assert check_duplicate_columns(clean) == []
   assert check_duplicate_columns(duplicated) != []


def test_dq_rule_03_no_empty_rows():
   frame = pd.DataFrame({
      'company_id': ['TCS', None],
      'year': ['Mar 2024', None]
   })

   assert len(check_empty_rows(frame)) == 1


def test_dq_rule_04_duplicate_records_detected():
   frame = pd.DataFrame({
      'id': [1, 2],
      'company_id': ['TCS', 'TCS'],
      'year': ['Mar 2024', 'Mar 2024']
   })

   assert len(check_duplicate_records(frame)) == 2


def test_dq_rule_05_no_null_company_id():
   frame = pd.DataFrame({'company_id': ['TCS', None]})

   assert len(check_null_company_id(frame)) == 1


def test_dq_rule_06_no_null_year():
   frame = pd.DataFrame({'year': ['Mar 2024', None]})

   assert len(check_null_year(frame)) == 1


def test_dq_rule_07_company_id_is_uppercase():
   frame = pd.DataFrame({'company_id': ['TCS', 'infy']})

   assert len(check_company_id_uppercase(frame)) == 1


def test_dq_rule_08_unexpected_columns_flagged():
   frame = pd.DataFrame({'company_id': ['TCS'], 'surprise': [1]})

   assert check_unexpected_columns(frame, ['company_id']) != []


# Rules 9-14: delivered database integrity
def test_dq_rule_09_financial_ratios_row_count(financial_ratios):
   # Sprint 2 exit criterion: at least 1,100 company-year rows.
   assert len(financial_ratios) >= MINIMUM_RATIO_ROWS


def test_dq_rule_10_all_kpi_columns_present(financial_ratios):
   missing = [
      column for column in KPI_COLUMNS
      if column not in financial_ratios.columns
   ]

   assert missing == [], f'financial_ratios is missing {missing}'


def test_dq_rule_11_no_kpi_column_is_entirely_null(financial_ratios):
   empty_columns = [
      column for column in KPI_COLUMNS
      if financial_ratios[column].notna().sum() == 0
   ]

   assert empty_columns == [], f'columns with no data: {empty_columns}'


def test_dq_rule_12_every_ratio_company_exists(connection, financial_ratios):
   # The supplied companies.xlsx is truncated: it carries 92 rows and stops part way through the alphabet, so the financial statements reference tickers that have no company master record. This is a source data defect recorded in the Sprint 2 audit, not a pipeline defect, so the two known orphans are accepted. Any NEW orphan is a regression and fails this rule.
   companies = pd.read_sql('SELECT id FROM companies', connection)
   orphans = set(financial_ratios['company_id']) - set(companies['id'])
   unexpected = orphans - KNOWN_ORPHAN_COMPANY_IDS

   assert unexpected == set(), (
      f'undocumented orphan company_id values: {sorted(unexpected)}'
   )


def test_dq_rule_13_period_labels_parse(financial_ratios):
   unparseable = [
      year for year in financial_ratios['year'].unique()
      if period_sort_key(year) <= 0
   ]

   assert unparseable == [], f'unparseable periods: {unparseable}'


def test_dq_rule_14_peer_percentiles_cover_all_groups(connection):
   percentiles = pd.read_sql(
      'SELECT DISTINCT peer_group_name FROM peer_percentiles',
      connection
   )
   assert len(percentiles) == EXPECTED_PEER_GROUPS
