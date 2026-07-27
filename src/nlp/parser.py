import re
import sqlite3
from pathlib import Path
import pandas as pd

from src.analytics.periods import deduplicate_company_years, latest_rows

DB_PATH = 'data/nifty100.db'
PARSED_PATH = 'output/analysis_parsed.csv'
FAILURES_PATH = 'output/parse_failures.csv'
GROWTH_PATTERN = re.compile(r'(\d+)\s*Years?:?\s*([\d.]+)%')

METRIC_COLUMNS = {
   'compounded_sales_growth': 'sales_growth',
   'compounded_profit_growth': 'profit_growth',
   'stock_price_cagr': 'stock_price_cagr',
   'roe': 'roe'
}

# Divergence above this many percentage points is flagged for review.
DIVERGENCE_TOLERANCE_PCT = 5.0

# Parsed metric mapped to the ratio engine column it is checked against.
CROSS_VALIDATION_MAP = {
   'sales_growth': 'revenue_cagr_5yr',
   'profit_growth': 'pat_cagr_5yr'
}

CROSS_VALIDATION_PERIOD_YEARS = 5


def get_connection():
   return sqlite3.connect(DB_PATH)


def parse_growth_text(text):
   if not isinstance(text, str):
      return None, None

   match = GROWTH_PATTERN.search(text)
   if not match:
      return None, None

   return int(match.group(1)), float(match.group(2))


def parse_analysis_table(analysis_df):
   parsed_records = []
   failure_records = []

   for row in analysis_df.itertuples():
      for column, metric_type in METRIC_COLUMNS.items():
         raw_value = getattr(row, column, None)
         period_years, value_pct = parse_growth_text(raw_value)

         if period_years is None:
            failure_records.append({
               'company_id': row.company_id,
               'metric_type': metric_type,
               'raw_text': (
                  '' if raw_value is None or pd.isna(raw_value)
                  else str(raw_value).strip()
               ),
               'reason': 'No period-and-percentage match'
            })
            continue

         parsed_records.append({
            'company_id': row.company_id,
            'metric_type': metric_type,
            'period_years': period_years,
            'value_pct': value_pct
         })

   parsed_df = pd.DataFrame(
      parsed_records,
      columns=['company_id', 'metric_type', 'period_years', 'value_pct']
   )
   failures_df = pd.DataFrame(
      failure_records,
      columns=['company_id', 'metric_type', 'raw_text', 'reason']
   )

   return parsed_df, failures_df


def cross_validate_against_ratio_engine(parsed_df, ratios_df):
   latest_ratios = latest_rows(deduplicate_company_years(ratios_df))
   comparisons = []

   window = parsed_df[
      parsed_df['period_years'] == CROSS_VALIDATION_PERIOD_YEARS
   ]

   for row in window.itertuples():
      computed_column = CROSS_VALIDATION_MAP.get(row.metric_type)
      if computed_column is None:
         continue

      match = latest_ratios[latest_ratios['company_id'] == row.company_id]
      if match.empty:
         continue

      computed_value = match.iloc[0][computed_column]
      if pd.isna(computed_value):
         continue

      divergence = abs(row.value_pct - float(computed_value))

      comparisons.append({
         'company_id': row.company_id,
         'metric_type': row.metric_type,
         'source_value_pct': row.value_pct,
         'computed_value_pct': round(float(computed_value), 2),
         'divergence_pct': round(divergence, 2),
         'needs_review': divergence > DIVERGENCE_TOLERANCE_PCT
      })

   return pd.DataFrame(comparisons)


def export_parsed_analysis(connection=None):
   owns_connection = connection is None
   if owns_connection:
      connection = get_connection()

   try:
      analysis_df = pd.read_sql('SELECT * FROM analysis', connection)
      ratios_df = pd.read_sql('SELECT * FROM financial_ratios', connection)
   finally:
      if owns_connection:
         connection.close()

   parsed_df, failures_df = parse_analysis_table(analysis_df)
   comparison_df = cross_validate_against_ratio_engine(parsed_df, ratios_df)

   parsed_path = Path(PARSED_PATH)
   parsed_path.parent.mkdir(parents=True, exist_ok=True)
   parsed_df.to_csv(parsed_path, index=False)
   failures_df.to_csv(Path(FAILURES_PATH), index=False)

   print(f'Wrote {parsed_path} ({len(parsed_df)} parsed values)')
   print(f'Wrote {FAILURES_PATH} ({len(failures_df)} unparseable values)')
   print()
   print(
      f'COVERAGE: {parsed_df["company_id"].nunique()} of 92 companies. '
      'The supplied analysis table only carries these companies.'
   )

   if not comparison_df.empty:
      flagged = comparison_df[comparison_df['needs_review']]
      print()
      print(
         f'Cross-validation against the ratio engine: '
         f'{len(comparison_df)} comparisons, {len(flagged)} above the '
         f'{DIVERGENCE_TOLERANCE_PCT} point tolerance.'
      )
      print(comparison_df.to_string(index=False))

   return parsed_df, failures_df, comparison_df


def main():
   export_parsed_analysis()


if __name__ == '__main__':
   main()
