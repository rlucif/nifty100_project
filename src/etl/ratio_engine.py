'''
Ratio Engine for the N100 Financial Intelligence Platform:
Reads financial data from SQLite, computes KPIs using the analytics
modules and updates the financial_ratios table.
'''

import sqlite3
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


DB_PATH = 'data/nifty100.db'


def get_connection():
   return sqlite3.connect(DB_PATH)

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
            'face_value'
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
         'operating_activity'
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
         'cash_from_operations_cr'
      ]
   ]

   return financial_ratios_df

def save_financial_ratios(connection, financial_ratios_df):
   # Refresh the financial_ratios table while preserving the database schema.
   cursor = connection.cursor()
   cursor.execute("DELETE FROM financial_ratios")

   financial_ratios_df.to_sql(
      "financial_ratios",
      connection,
      if_exists="append",
      index=False
   )

   connection.commit()
   print(
      f"\nSaved {len(financial_ratios_df)} rows "
      "to financial_ratios."
   )

def main():
   connection = get_connection()

   try:
      tables = load_tables(connection)

      print('Tables loaded successfully.\n')

      master_df = build_master_dataframe(tables)
      master_df = calculate_profitability_kpis(master_df)
      financial_ratios_df = build_financial_ratios_dataframe(master_df)
      save_financial_ratios(connection, financial_ratios_df)
      print()
      print(financial_ratios_df.head())

      print(f'Master dataframe rows : {len(master_df)}')
      print()
      print(master_df[[
                  'company_id',
                  'year',
                  'net_profit_margin_pct',
                  'operating_profit_margin_pct',
                  'return_on_equity_pct'
            ]].head(10)
      )

   finally:
      connection.close()

if __name__ == '__main__':
   main()