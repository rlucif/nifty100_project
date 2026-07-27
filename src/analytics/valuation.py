import sqlite3
from pathlib import Path

import pandas as pd
from src.screener.universe import build_universe

DB_PATH = 'data/nifty100.db'
SUMMARY_PATH = 'output/valuation_summary.xlsx'
FLAGS_PATH = 'output/valuation_flags.csv'

# Multiples of the sector median that trigger each flag.
CAUTION_MULTIPLE = 1.5
DISCOUNT_MULTIPLE = 0.7

MEDIAN_PE_WINDOW_YEARS = 5

FLAG_CAUTION = 'Caution'
FLAG_DISCOUNT = 'Discount'
FLAG_FAIR = 'Fair'

SUMMARY_COLUMNS = [
   'company_id',
   'company_name',
   'sector',
   'pe_ratio',
   'pb_ratio',
   'ev_ebitda',
   'fcf_yield_pct',
   'median_pe_5yr',
   'pe_vs_sector_median_pct',
   'sector_median_pe',
   'flag'
]


def get_connection():
   return sqlite3.connect(DB_PATH)


def calculate_fcf_yield(free_cash_flow_cr, market_cap_crore):
   # Free cash flow as a percentage of market capitalisation.
   if pd.isna(free_cash_flow_cr) or pd.isna(market_cap_crore):
      return None
   if market_cap_crore == 0:
      return None

   return (free_cash_flow_cr / market_cap_crore) * 100


def assign_flag(pe_ratio, sector_median_pe):
   if pd.isna(pe_ratio) or pd.isna(sector_median_pe) or sector_median_pe == 0:
      return None
   if pe_ratio > sector_median_pe * CAUTION_MULTIPLE:
      return FLAG_CAUTION
   if pe_ratio < sector_median_pe * DISCOUNT_MULTIPLE:
      return FLAG_DISCOUNT

   return FLAG_FAIR


def calculate_median_pe_history(market_cap_df, window_years=None):
   if window_years is None:
      window_years = MEDIAN_PE_WINDOW_YEARS

   history = market_cap_df.sort_values(['company_id', 'year'])
   recent = history.groupby('company_id').tail(window_years)

   return (
      recent.groupby('company_id')['pe_ratio']
      .median()
      .rename('median_pe_5yr')
      .reset_index()
   )


def build_valuation_summary(connection=None):
   owns_connection = connection is None
   if owns_connection:
      connection = get_connection()

   try:
      universe_df = build_universe(connection)
      market_cap_df = pd.read_sql('SELECT * FROM market_cap', connection)
   finally:
      if owns_connection:
         connection.close()

   valuation_df = universe_df[[
      'company_id',
      'company_name',
      'broad_sector',
      'year',
      'pe_ratio',
      'pb_ratio',
      'ev_ebitda',
      'free_cash_flow_cr',
      'market_cap_crore'
   ]].copy()

   valuation_df = valuation_df.rename(columns={'broad_sector': 'sector'})

   valuation_df['fcf_yield_pct'] = [
      calculate_fcf_yield(free_cash_flow, market_cap)
      for free_cash_flow, market_cap in zip(
         valuation_df['free_cash_flow_cr'],
         valuation_df['market_cap_crore']
      )
   ]

   # Sector median P/E in the latest year.
   sector_median = (
      valuation_df.groupby('sector')['pe_ratio']
      .median()
      .rename('sector_median_pe')
      .reset_index()
   )
   valuation_df = valuation_df.merge(sector_median, on='sector', how='left')

   valuation_df = valuation_df.merge(
      calculate_median_pe_history(market_cap_df),
      on='company_id',
      how='left'
   )

   valuation_df['pe_vs_sector_median_pct'] = (
      (valuation_df['pe_ratio'] / valuation_df['sector_median_pe'] - 1) * 100
   )

   valuation_df['flag'] = [
      assign_flag(pe_ratio, sector_median_pe)
      for pe_ratio, sector_median_pe in zip(
         valuation_df['pe_ratio'],
         valuation_df['sector_median_pe']
      )
   ]

   numeric_columns = [
      'pe_ratio',
      'pb_ratio',
      'ev_ebitda',
      'fcf_yield_pct',
      'median_pe_5yr',
      'pe_vs_sector_median_pct',
      'sector_median_pe'
   ]
   for column in numeric_columns:
      valuation_df[column] = pd.to_numeric(
         valuation_df[column],
         errors='coerce'
      ).round(2)

   return valuation_df[SUMMARY_COLUMNS].sort_values('company_id')


def export_valuation_outputs(valuation_df=None):
   if valuation_df is None:
      valuation_df = build_valuation_summary()

   summary_path = Path(SUMMARY_PATH)
   summary_path.parent.mkdir(parents=True, exist_ok=True)

   with pd.ExcelWriter(summary_path, engine='openpyxl') as writer:
      valuation_df.to_excel(writer, sheet_name='Valuation', index=False)

      note_df = pd.DataFrame({
         'Note': [
            'P/E, P/B, EV/EBITDA and market cap are SIMULATED datasets.',
            'Flags demonstrate the valuation logic and are not an '
            'investment view.',
            f'Caution: P/E above {CAUTION_MULTIPLE}x the sector median.',
            f'Discount: P/E below {DISCOUNT_MULTIPLE}x the sector median.',
            'FCF yield = free cash flow / market cap x 100.'
         ]
      })
      note_df.to_excel(writer, sheet_name='Notes', index=False)

   flags_df = valuation_df[
      valuation_df['flag'].isin([FLAG_CAUTION, FLAG_DISCOUNT])
   ]
   flags_path = Path(FLAGS_PATH)
   flags_df.to_csv(flags_path, index=False)

   print(f'Wrote {summary_path} ({len(valuation_df)} rows)')
   print(f'Wrote {flags_path} ({len(flags_df)} flagged companies)')

   return valuation_df, flags_df


def main():
   valuation_df, flags_df = export_valuation_outputs()

   print()
   print('Flag distribution:')
   print(valuation_df['flag'].value_counts(dropna=False).to_string())
   print()
   print('Sector median P/E:')
   print(
      valuation_df.groupby('sector')['sector_median_pe']
      .first()
      .round(2)
      .to_string()
   )


if __name__ == '__main__':
   main()
