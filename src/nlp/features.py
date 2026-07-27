import sqlite3
import pandas as pd

from src.analytics.periods import add_period_columns, deduplicate_company_years
from src.analytics.ratios import calculate_roce

DB_PATH = 'data/nifty100.db'
EBITDA_COLUMN = 'operating_profit'


def get_connection():
   return sqlite3.connect(DB_PATH)


def load_history(connection=None):
   owns_connection = connection is None
   if owns_connection:
      connection = get_connection()

   try:
      ratios_df = pd.read_sql('SELECT * FROM financial_ratios', connection)
      profit_df = pd.read_sql(
         'SELECT company_id, year, sales, operating_profit, other_income, '
         'net_profit, eps, dividend_payout FROM profitandloss',
         connection
      )
      balance_df = pd.read_sql(
         'SELECT company_id, year, equity_capital, reserves, borrowings, '
         'investments, total_assets FROM balancesheet',
         connection
      )
      cashflow_df = pd.read_sql(
         'SELECT company_id, year, operating_activity, investing_activity, '
         'financing_activity FROM cashflow',
         connection
      )
      sectors_df = pd.read_sql(
         'SELECT company_id, broad_sector, sub_sector FROM sectors',
         connection
      )
      companies_df = pd.read_sql(
         'SELECT id AS company_id, company_name FROM companies',
         connection
      )
      market_cap_df = pd.read_sql('SELECT * FROM market_cap', connection)
   finally:
      if owns_connection:
         connection.close()

   history = deduplicate_company_years(ratios_df)
   for frame in (profit_df, balance_df, cashflow_df):
      history = history.merge(
         deduplicate_company_years(frame),
         on=['company_id', 'year'],
         how='left',
         suffixes=('', '_src')
      )

   history = history.merge(sectors_df, on='company_id', how='left')
   history = history.merge(companies_df, on='company_id', how='left')

   history = add_period_columns(history)
   history = history[history['period_sort_key'] > 0]

   # ROCE and net debt are not persisted, so derive them here.
   history['return_on_capital_employed_pct'] = [
      calculate_roce(
         operating_profit, other_income, equity, reserves, borrowings
      )
      for operating_profit, other_income, equity, reserves, borrowings in zip(
         history['operating_profit'],
         history['other_income'],
         history['equity_capital'],
         history['reserves'],
         history['borrowings']
      )
   ]

   history['net_debt_cr'] = (
      pd.to_numeric(history['borrowings'], errors='coerce')
      - pd.to_numeric(history['investments'], errors='coerce')
   )

   # Latest-year valuation for the dividend yield rule.
   latest_valuation = (
      market_cap_df.sort_values('year')
      .groupby('company_id')
      .tail(1)[['company_id', 'dividend_yield_pct', 'market_cap_crore']]
   )
   history = history.merge(latest_valuation, on='company_id', how='left')

   return history.sort_values(['company_id', 'period_sort_key'])


def _series(group, column):
   # Numeric series for one company, oldest first, index reset.
   if column not in group.columns:
      return pd.Series(dtype='float64')

   return pd.to_numeric(group[column], errors='coerce').reset_index(drop=True)


def build_company_features(history):
   # company_id -> feature dict consumed by the rule engine.
   features = {}

   for company_id, group in history.groupby('company_id'):
      group = group.sort_values('period_sort_key')
      latest = group.iloc[-1]

      features[company_id] = {
         'company_id': company_id,
         'company_name': latest.get('company_name'),
         'broad_sector': latest.get('broad_sector'),
         'latest_year': latest.get('year'),
         'years_of_data': len(group),

         # Latest snapshot values.
         'roe': _to_float(latest.get('return_on_equity_pct')),
         'roce': _to_float(latest.get('return_on_capital_employed_pct')),
         'opm': _to_float(latest.get('operating_profit_margin_pct')),
         'npm': _to_float(latest.get('net_profit_margin_pct')),
         'debt_to_equity': _to_float(latest.get('debt_to_equity')),
         'interest_coverage': _to_float(latest.get('interest_coverage')),
         'net_profit': _to_float(latest.get('net_profit')),
         'dividend_payout_pct': _to_float(
            latest.get('dividend_payout_ratio_pct')
         ),
         'dividend_yield_pct': _to_float(latest.get('dividend_yield_pct')),
         'free_cash_flow': _to_float(latest.get('free_cash_flow_cr')),
         'net_debt': _to_float(latest.get('net_debt_cr')),
         'ebitda': _to_float(latest.get(EBITDA_COLUMN)),

         # Growth already computed by the ratio engine.
         'revenue_cagr_5yr': _to_float(latest.get('revenue_cagr_5yr')),
         'pat_cagr_5yr': _to_float(latest.get('pat_cagr_5yr')),
         'eps_cagr_5yr': _to_float(latest.get('eps_cagr_5yr')),

         # Ordered series for streak and trend rules.
         'roe_series': _series(group, 'return_on_equity_pct'),
         'opm_series': _series(group, 'operating_profit_margin_pct'),
         'eps_series': _series(group, 'earnings_per_share'),
         'sales_series': _series(group, 'sales'),
         'fcf_series': _series(group, 'free_cash_flow_cr'),
         'de_series': _series(group, 'debt_to_equity'),
         'assets_series': _series(group, 'total_assets'),
         'borrowings_series': _series(group, 'borrowings')
      }

   return features


def _to_float(value):
   if value is None or pd.isna(value):
      return None

   try:
      return float(value)
   except (TypeError, ValueError):
      return None


# Streak and trend helpers used by the rules
def trailing_streak(series, predicate):
   streak = 0

   for value in reversed(list(series)):
      if pd.isna(value) or not predicate(value):
         break
      streak += 1

   return streak


def consecutive_direction(series, rising=True, periods=3):
   # True if the last `periods` transitions all move the same way.
   values = [value for value in list(series)[-(periods + 1):]]

   if len(values) < periods + 1:
      return False
   if any(pd.isna(value) for value in values):
      return False

   for earlier, later in zip(values, values[1:]):
      if rising and not later > earlier:
         return False
      if not rising and not later < earlier:
         return False

   return True


def sustained_above(series, threshold, periods=3):
   # True if the last `periods` values are all above the threshold.
   values = list(series)[-periods:]

   if len(values) < periods:
      return False
   if any(pd.isna(value) for value in values):
      return False

   return all(value > threshold for value in values)
