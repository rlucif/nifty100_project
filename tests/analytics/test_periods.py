import pandas as pd
from src.analytics.periods import (
   deduplicate_company_years,
   fiscal_year,
   is_full_year,
   latest_rows,
   parse_period,
   period_sort_key
)


def test_parses_a_clean_period():
   assert parse_period('Mar 2024') == (3, 2024)


def test_parses_a_december_period():
   assert parse_period('Dec 2023') == (12, 2023)


def test_rejects_ttm():
   assert parse_period('TTM') == (None, None)
   assert period_sort_key('TTM') == -1


def test_tolerates_trailing_noise():
   # 'Mar 2023 15' appears in profitandloss.xlsx.
   assert parse_period('Mar 2023 15') == (3, 2023)


def test_part_year_labels_are_not_full_years():
   assert is_full_year('Mar 2024') is True
   assert is_full_year('Mar 2016 9m') is False
   assert is_full_year('TTM') is False


def test_sort_key_orders_periods_chronologically():
   labels = ['Mar 2024', 'Dec 2023', 'Sep 2024', 'Mar 2023']
   ordered = sorted(labels, key=period_sort_key)

   assert ordered == ['Mar 2023', 'Dec 2023', 'Mar 2024', 'Sep 2024']


def test_fiscal_year_is_the_closing_calendar_year():
   assert fiscal_year('Mar 2024') == 2024
   assert fiscal_year('Dec 2024') == 2024
   assert fiscal_year('TTM') is None


def test_latest_rows_picks_the_most_recent_period():
   frame = pd.DataFrame({
      'company_id': ['TCS', 'TCS', 'INFY'],
      'year': ['Mar 2023', 'Mar 2024', 'Mar 2024'],
      'value': [1, 2, 3]
   })

   result = latest_rows(frame)

   assert len(result) == 2
   assert result.loc[
      result['company_id'] == 'TCS', 'year'
   ].iloc[0] == 'Mar 2024'


def test_latest_rows_ignores_unparseable_periods():
   frame = pd.DataFrame({
      'company_id': ['TCS', 'TCS'],
      'year': ['Mar 2024', 'TTM'],
      'value': [1, 2]
   })

   result = latest_rows(frame)

   assert len(result) == 1
   assert result['year'].iloc[0] == 'Mar 2024'


def test_deduplicate_collapses_repeated_company_years():
   # The Sprint 2 join fan out repeats company-year rows.
   frame = pd.DataFrame({
      'company_id': ['PNB', 'PNB', 'PNB'],
      'year': ['Mar 2024', 'Mar 2024', 'Mar 2023'],
      'value': [1, 1, 2]
   })

   result = deduplicate_company_years(frame)

   assert len(result) == 2
