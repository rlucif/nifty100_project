'''
The screener needs metrics that live in four different tables:
   financial_ratios  ratio engine output (Sprint 2)
   profitandloss     sales and net profit
   market_cap        P/E, P/B, dividend yield, market cap  (SIMULATED)
   sectors           broad_sector, needed for the Financials D/E rule

Note: market_cap and stock_prices are simulated datasets. Any report
built on P/E, P/B, dividend yield or market cap must label them
SIMULATED.
'''

import sqlite3

import pandas as pd

from src.analytics.periods import (
   add_period_columns,
   deduplicate_company_years,
   latest_rows
)
from src.analytics.ratios import calculate_roce

DB_PATH = 'data/nifty100.db'

# Columns carried through from the ratio engine output.
RATIO_COLUMNS = [
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

REVENUE_CAGR_3YR_WINDOW = 3
FCF_CAGR_WINDOW = 5


def get_connection():
   return sqlite3.connect(DB_PATH)


def load_source_frames(connection):
   return {
      'financial_ratios': pd.read_sql(
         'SELECT * FROM financial_ratios',
         connection
      ),
      'profitandloss': pd.read_sql(
         'SELECT company_id, year, sales, net_profit, operating_profit, '
         'other_income FROM profitandloss',
         connection
      ),
      'balancesheet': pd.read_sql(
         'SELECT company_id, year, equity_capital, reserves, borrowings '
         'FROM balancesheet',
         connection
      ),
      'market_cap': pd.read_sql('SELECT * FROM market_cap', connection),
      'sectors': pd.read_sql(
         'SELECT company_id, broad_sector, sub_sector, market_cap_category '
         'FROM sectors',
         connection
      ),
      'companies': pd.read_sql(
         'SELECT id AS company_id, company_name FROM companies',
         connection
      )
   }


def _cagr(start_value, end_value, years):
   if pd.isna(start_value) or pd.isna(end_value):
      return None
   if start_value == 0 or start_value < 0 or end_value < 0:
      return None

   return ((end_value / start_value) ** (1 / years) - 1) * 100


def build_history_derivations(ratios_df, profitandloss_df):
   ratio_history = deduplicate_company_years(ratios_df)
   ratio_history = add_period_columns(ratio_history)
   ratio_history = ratio_history[ratio_history['period_sort_key'] > 0]
   ratio_history = ratio_history.sort_values(
      ['company_id', 'period_sort_key']
   )

   grouped = ratio_history.groupby('company_id')

   fcf_start = grouped['free_cash_flow_cr'].shift(FCF_CAGR_WINDOW)
   ratio_history['fcf_cagr_5yr'] = [
      _cagr(start, end, FCF_CAGR_WINDOW)
      for start, end in zip(fcf_start, ratio_history['free_cash_flow_cr'])
   ]

   previous_de = grouped['debt_to_equity'].shift(1)
   ratio_history['debt_to_equity_declining'] = (
      ratio_history['debt_to_equity'] < previous_de
   ).where(previous_de.notna(), False)

   sales_history = deduplicate_company_years(profitandloss_df)
   sales_history = add_period_columns(sales_history)
   sales_history = sales_history[sales_history['period_sort_key'] > 0]
   sales_history = sales_history.sort_values(
      ['company_id', 'period_sort_key']
   )

   sales_start = sales_history.groupby('company_id')['sales'].shift(
      REVENUE_CAGR_3YR_WINDOW
   )
   sales_history['revenue_cagr_3yr'] = [
      _cagr(start, end, REVENUE_CAGR_3YR_WINDOW)
      for start, end in zip(sales_start, sales_history['sales'])
   ]

   derived_ratio_columns = [
      'company_id',
      'year',
      'fcf_cagr_5yr',
      'debt_to_equity_declining'
   ]

   return (
      ratio_history[derived_ratio_columns],
      sales_history[['company_id', 'year', 'revenue_cagr_3yr']]
   )


def build_universe(connection=None):
   # One row per company at its latest financial year.
   owns_connection = connection is None
   if owns_connection:
      connection = get_connection()

   try:
      frames = load_source_frames(connection)
   finally:
      if owns_connection:
         connection.close()

   ratios_df = frames['financial_ratios']
   profitandloss_df = frames['profitandloss']

   ratio_derived, sales_derived = build_history_derivations(
      ratios_df,
      profitandloss_df
   )

   # Latest ratio row per company drives the whole universe.
   universe_df = latest_rows(deduplicate_company_years(ratios_df))
   universe_df = universe_df[
      ['company_id', 'year', 'period_sort_key', 'fiscal_year']
      + RATIO_COLUMNS
   ]

   universe_df = universe_df.merge(
      ratio_derived,
      on=['company_id', 'year'],
      how='left'
   )

   # Sales and profit for the same period.
   statement_df = deduplicate_company_years(profitandloss_df)
   universe_df = universe_df.merge(
      statement_df,
      on=['company_id', 'year'],
      how='left'
   )
   universe_df = universe_df.merge(
      sales_derived,
      on=['company_id', 'year'],
      how='left'
   )

   balance_df = deduplicate_company_years(frames['balancesheet'])
   universe_df = universe_df.merge(
      balance_df,
      on=['company_id', 'year'],
      how='left'
   )

   # ROCE is required by the composite score but Sprint 2 deliberately did not persist it, so it is recomputed here.
   universe_df['return_on_capital_employed_pct'] = universe_df.apply(
      lambda row: calculate_roce(
         row['operating_profit'],
         row['other_income'],
         row['equity_capital'],
         row['reserves'],
         row['borrowings']
      ) if pd.notna(row['operating_profit']) else None,
      axis=1
   )

   universe_df['cfo_to_pat_ratio'] = universe_df.apply(
      lambda row: (
         row['cash_from_operations_cr'] / row['net_profit']
         if pd.notna(row['net_profit']) and row['net_profit'] != 0
         else None
      ),
      axis=1
   )

   universe_df['fcf_positive_flag'] = (
      universe_df['free_cash_flow_cr'] > 0
   ).astype(int)

   # Valuation metrics, matched on the calendar year the period closes in.
   market_cap_df = frames['market_cap'].rename(
      columns={'year': 'fiscal_year'}
   )
   universe_df = universe_df.merge(
      market_cap_df.drop(columns=['id']),
      on=['company_id', 'fiscal_year'],
      how='left'
   )

   universe_df = universe_df.merge(
      frames['sectors'],
      on='company_id',
      how='left'
   )
   universe_df = universe_df.merge(
      frames['companies'],
      on='company_id',
      how='left'
   )

   return universe_df.reset_index(drop=True)


def main():
   universe_df = build_universe()

   print(f'Universe built: {len(universe_df)} companies')
   print(f'Latest periods: {sorted(universe_df["year"].unique())}')
   print()
   print(universe_df[[
      'company_id',
      'year',
      'broad_sector',
      'return_on_equity_pct',
      'debt_to_equity',
      'pe_ratio',
      'revenue_cagr_5yr'
   ]].head(10).round(2).to_string(index=False))


if __name__ == '__main__':
   main()
