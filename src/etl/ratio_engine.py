'''
Ratio Engine for the N100 Financial Intelligence Platform:
Reads financial data from SQLite, computes KPIs using the analytics
modules and updates the financial_ratios table.
'''

import csv
import sqlite3
from pathlib import Path

import pandas as pd

from src.analytics.ratios import (
   calculate_net_profit_margin,
   calculate_operating_profit_margin,
   calculate_roe,
   calculate_roce,
   calculate_debt_to_equity,
   calculate_interest_coverage,
   calculate_asset_turnover,
   calculate_net_debt,
   calculate_free_cash_flow,
   calculate_cfo_quality_score,
   calculate_capital_allocation,
   calculate_capex_intensity,
   calculate_fcf_conversion
)

from src.analytics.cagr import (
   calculate_revenue_cagr,
   calculate_pat_cagr,
   calculate_eps_cagr
)

from src.analytics.cashflow_kpis import get_cash_flow_sign

from src.analytics.periods import (
   add_period_columns,
   deduplicate_company_years
)


DB_PATH = 'data/nifty100.db'
CAPITAL_ALLOCATION_CSV = 'output/capital_allocation.csv'

# Number of years in the standard CAGR window.
CAGR_WINDOW_YEARS = 5

# CAGR columns added in Sprint 2 Day 12. composite_quality_score is
# declared here but populated by the Sprint 3 screener, because it is a
# cross-sectional score that needs the whole universe to normalise against.
CAGR_COLUMNS = {
   'revenue_cagr_5yr': 'REAL',
   'pat_cagr_5yr': 'REAL',
   'eps_cagr_5yr': 'REAL',
   'composite_quality_score': 'REAL'
}


def get_connection():
   return sqlite3.connect(DB_PATH)

def ensure_cagr_columns(connection):
   # Databases created before Sprint 2 Day 12 predate the CAGR columns.
   # schema.sql already declares them, so only existing files need patching.
   cursor = connection.cursor()
   existing = {
      row[1] for row in cursor.execute('PRAGMA table_info(financial_ratios)')
   }

   for column_name, column_type in CAGR_COLUMNS.items():
      if column_name in existing:
         continue

      cursor.execute(
         f'ALTER TABLE financial_ratios ADD COLUMN {column_name} {column_type}'
      )
      print(f'Added missing column financial_ratios.{column_name}')

   connection.commit()

def load_tables(connection):
   return {
      'profitandloss': pd.read_sql(
         'SELECT * FROM profitandloss',
         connection
      ),
      'balancesheet': pd.read_sql(
         'SELECT * FROM balancesheet',
         connection
      ),
      'cashflow': pd.read_sql(
         'SELECT * FROM cashflow',
         connection
      ),
      'companies': pd.read_sql(
         'SELECT * FROM companies',
         connection
      )
   }

def build_master_dataframe(tables):
   master_df = (
      tables['profitandloss']
      .merge(
         tables['balancesheet'],
         on=['company_id', 'year'],
         how='inner',
         suffixes=('_pl', '_bs')
      )
      .merge(
         tables['cashflow'],
         on=['company_id', 'year'],
         how='inner'
      )
      .merge(
         tables['companies'][[
            'id',
            'book_value',
            'face_value',
            'roe_percentage',
            'roce_percentage'
         ]],
         left_on='company_id',
         right_on='id',
         how='left'
      )
   )

   return master_df

def calculate_profitability_kpis(master_df):

   # Profitability Ratios
   master_df['net_profit_margin_pct'] = master_df.apply(
      lambda row: calculate_net_profit_margin(
         row['net_profit'],
         row['sales']
      ),
      axis=1
   )
   master_df['operating_profit_margin_pct'] = master_df.apply(
      lambda row: calculate_operating_profit_margin(
         row['operating_profit'],
         row['sales'],
         row['opm_percentage']
      ),
      axis=1
   )
   master_df['return_on_equity_pct'] = master_df.apply(
      lambda row: calculate_roe(
         row['net_profit'],
         row['equity_capital'],
         row['reserves']
      ),
      axis=1
   )
   master_df['return_on_capital_employed_pct'] = master_df.apply(
      lambda row: calculate_roce(
         row['operating_profit'],
         row['other_income'],
         row['equity_capital'],
         row['reserves'],
         row['borrowings']
      ),
      axis=1
   )

   # Leverage & Efficiency
   master_df['debt_to_equity'] = master_df.apply(
      lambda row: calculate_debt_to_equity(
         row['borrowings'],
         row['equity_capital'],
         row['reserves']
      ),
      axis=1
   )
   master_df['interest_coverage'] = master_df.apply(
      lambda row: calculate_interest_coverage(
         row['operating_profit'],
         row['other_income'],
         row['interest']
      ),
      axis=1
   )
   master_df['asset_turnover'] = master_df.apply(
      lambda row: calculate_asset_turnover(
         row['sales'],
         row['total_assets']
      ),
      axis=1
   )
   master_df['net_debt'] = master_df.apply(
      lambda row: calculate_net_debt(
         row['borrowings'],
         row['investments']
      ),
      axis=1
   )
   
   # Cash Flow KPIs
   master_df['free_cash_flow_cr'] = master_df.apply(
      lambda row: calculate_free_cash_flow(
         row['operating_activity'],
         row['investing_activity']
      ),
      axis=1
   )
   master_df['cfo_quality_score'] = master_df.apply(
      lambda row: calculate_cfo_quality_score(
         row['operating_activity'],
         row['net_profit']
      ),
      axis=1
   )
   master_df['capital_allocation'] = master_df.apply(
      lambda row: calculate_capital_allocation(
         row['operating_activity'],
         row['investing_activity'],
         row['financing_activity'],
         row['cfo_quality_score']
      ),
      axis=1
   )
   master_df['capex_intensity'] = master_df.apply(
      lambda row: calculate_capex_intensity(
         row['investing_activity'],
         row['sales']
      ),
      axis=1
   )
   master_df['fcf_conversion'] = master_df.apply(
      lambda row: calculate_fcf_conversion(
         row['free_cash_flow_cr'],
         row['operating_profit']
      ),
      axis=1
   )

   return master_df


def calculate_cagr_kpis(master_df):
   # Rolling 5-year CAGR for revenue, PAT and EPS.
   #
   # The window is built on de-duplicated company-year history: the
   # Sprint 2 joins fan out on duplicate source rows, and counting the
   # same year five times would corrupt the lookback.
   history = master_df[[
      'company_id',
      'year',
      'sales',
      'net_profit',
      'eps'
   ]].copy()

   history = deduplicate_company_years(history)
   history = add_period_columns(history)
   history = history[history['period_sort_key'] > 0]
   history = history.sort_values(['company_id', 'period_sort_key'])

   grouped = history.groupby('company_id')

   cagr_specs = (
      ('sales', 'revenue_cagr_5yr', calculate_revenue_cagr),
      ('net_profit', 'pat_cagr_5yr', calculate_pat_cagr),
      ('eps', 'eps_cagr_5yr', calculate_eps_cagr)
   )

   for source_column, target_column, cagr_function in cagr_specs:
      start_values = grouped[source_column].shift(CAGR_WINDOW_YEARS)

      history[target_column] = [
         _safe_cagr(cagr_function, start_value, end_value)
         for start_value, end_value
         in zip(start_values, history[source_column])
      ]

   cagr_columns = [target for _, target, _ in cagr_specs]

   return master_df.merge(
      history[['company_id', 'year'] + cagr_columns],
      on=['company_id', 'year'],
      how='left'
   )


def _safe_cagr(cagr_function, start_value, end_value):
   # calculate_cagr returns (value, reason). Rows without a full window,
   # or with a documented edge case such as TURNAROUND, stay null.
   if pd.isna(start_value) or pd.isna(end_value):
      return None

   value, _reason = cagr_function(start_value, end_value, CAGR_WINDOW_YEARS)

   return value


def export_capital_allocation(master_df):
   # Sprint 2 Day 11 deliverable D-06.
   allocation_df = deduplicate_company_years(master_df).copy()

   allocation_df['cfo_sign'] = allocation_df['operating_activity'].map(
      get_cash_flow_sign
   )
   allocation_df['cfi_sign'] = allocation_df['investing_activity'].map(
      get_cash_flow_sign
   )
   allocation_df['cff_sign'] = allocation_df['financing_activity'].map(
      get_cash_flow_sign
   )

   allocation_df = allocation_df.rename(
      columns={'capital_allocation': 'pattern_label'}
   )

   allocation_df = allocation_df[[
      'company_id',
      'year',
      'cfo_sign',
      'cfi_sign',
      'cff_sign',
      'pattern_label'
   ]]

   output_path = Path(CAPITAL_ALLOCATION_CSV)
   output_path.parent.mkdir(parents=True, exist_ok=True)
   allocation_df.to_csv(output_path, index=False, quoting=csv.QUOTE_MINIMAL)

   print(f'Wrote {len(allocation_df)} rows to {output_path}.')

   return allocation_df


'''
TODO:
Existing financial_ratios table contains book_value_per_share values
that do not match either companies.book_value or
(equity_capital + reserves).
Source requires clarification or future audit.
'''
def build_financial_ratios_dataframe(master_df):
   # Build the final dataframe matching the financial_ratios
   # SQLite table schema
   # ROCE is intentionally computed for validation and audit purposes.
   # It is not persisted because the current financial_ratios schema
   # defined for Sprint 2 does not include a ROCE column.   
   financial_ratios_df = master_df[[
         'company_id',
         'year',
         'net_profit_margin_pct',
         'operating_profit_margin_pct',
         'return_on_equity_pct',
         'debt_to_equity',
         'interest_coverage',
         'asset_turnover',
         'free_cash_flow_cr',
         'eps',
         'book_value',
         'dividend_payout',
         'borrowings',
         'operating_activity',
         'revenue_cagr_5yr',
         'pat_cagr_5yr',
         'eps_cagr_5yr'
      ]].copy()

   financial_ratios_df.rename(columns={
         'eps': 'earnings_per_share',
         'book_value': 'book_value_per_share',
         'dividend_payout': 'dividend_payout_ratio_pct',
         'borrowings': 'total_debt_cr',
         'operating_activity': 'cash_from_operations_cr'
      },
      inplace=True
   )

   financial_ratios_df['capex_cr'] = (
      master_df['investing_activity'].abs()
   )

   financial_ratios_df = financial_ratios_df[[
         'company_id',
         'year',
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
         'eps_cagr_5yr'
      ]
   ]

   return financial_ratios_df

def save_financial_ratios(connection, financial_ratios_df):
   # Refresh the financial_ratios table while preserving the database schema.
   cursor = connection.cursor()
   cursor.execute('DELETE FROM financial_ratios')

   financial_ratios_df.to_sql(
      'financial_ratios',
      connection,
      if_exists='append',
      index=False
   )

   connection.commit()
   print(
      f'\nSaved {len(financial_ratios_df)} rows '
      'to financial_ratios.'
   )

def main():
   connection = get_connection()

   try:
      ensure_cagr_columns(connection)
      tables = load_tables(connection)

      print('Tables loaded successfully.\n')

      master_df = build_master_dataframe(tables)
      master_df = calculate_profitability_kpis(master_df)
      master_df = calculate_cagr_kpis(master_df)

      export_capital_allocation(master_df)

      financial_ratios_df = build_financial_ratios_dataframe(master_df)
      save_financial_ratios(connection, financial_ratios_df)

      print()
      print(financial_ratios_df.head())

   finally:
      connection.close()

if __name__ == '__main__':
   main()