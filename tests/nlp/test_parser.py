import pandas as pd
from src.nlp.parser import (
   DIVERGENCE_TOLERANCE_PCT,
   cross_validate_against_ratio_engine,
   parse_analysis_table,
   parse_growth_text
)


def test_parses_a_standard_entry():
   assert parse_growth_text('10 Years: 21%') == (10, 21.0)


def test_tolerates_padded_whitespace():
   # The source pads values with spaces: '5 Years:       22%'.
   assert parse_growth_text('5 Years:       22%') == (5, 22.0)


def test_parses_a_singular_year():
   assert parse_growth_text('1 Year:        13%') == (1, 13.0)


def test_parses_a_decimal_value():
   assert parse_growth_text('3 Years: 26.5%') == (3, 26.5)


def test_rejects_ttm():
   # No leading digit, so the specified pattern must not match.
   assert parse_growth_text('TTM:            47%') == (None, None)


def test_rejects_last_year():
   assert parse_growth_text('Last Year:    17%') == (None, None)


def test_rejects_non_string_input():
   assert parse_growth_text(None) == (None, None)
   assert parse_growth_text(float('nan')) == (None, None)


def test_parse_table_splits_matches_from_failures():
   analysis = pd.DataFrame({
      'company_id': ['TCS'],
      'compounded_sales_growth': ['5 Years: 10%'],
      'compounded_profit_growth': ['TTM: 27%'],
      'stock_price_cagr': ['5 Years: 8%'],
      'roe': ['Last Year: 17%']
   })

   parsed, failures = parse_analysis_table(analysis)

   assert len(parsed) == 2
   assert len(failures) == 2
   assert set(parsed['metric_type']) == {'sales_growth', 'stock_price_cagr'}


def test_parsed_frame_has_the_specified_columns():
   analysis = pd.DataFrame({
      'company_id': ['TCS'],
      'compounded_sales_growth': ['5 Years: 10%'],
      'compounded_profit_growth': ['5 Years: 8%'],
      'stock_price_cagr': ['5 Years: 8%'],
      'roe': ['5 Years: 40%']
   })

   parsed, _failures = parse_analysis_table(analysis)

   assert list(parsed.columns) == [
      'company_id', 'metric_type', 'period_years', 'value_pct'
   ]


def test_cross_validation_flags_a_large_divergence():
   parsed = pd.DataFrame({
      'company_id': ['TCS'],
      'metric_type': ['sales_growth'],
      'period_years': [5],
      'value_pct': [30.0]
   })
   ratios = pd.DataFrame({
      'company_id': ['TCS'],
      'year': ['Mar 2024'],
      'revenue_cagr_5yr': [10.0],
      'pat_cagr_5yr': [10.0]
   })

   result = cross_validate_against_ratio_engine(parsed, ratios)

   assert len(result) == 1
   assert result.iloc[0]['divergence_pct'] == 20.0
   assert bool(result.iloc[0]['needs_review']) is True


def test_cross_validation_accepts_a_close_match():
   parsed = pd.DataFrame({
      'company_id': ['TCS'],
      'metric_type': ['sales_growth'],
      'period_years': [5],
      'value_pct': [10.0]
   })
   ratios = pd.DataFrame({
      'company_id': ['TCS'],
      'year': ['Mar 2024'],
      'revenue_cagr_5yr': [10.4],
      'pat_cagr_5yr': [10.0]
   })

   result = cross_validate_against_ratio_engine(parsed, ratios)

   assert result.iloc[0]['divergence_pct'] < DIVERGENCE_TOLERANCE_PCT
   assert bool(result.iloc[0]['needs_review']) is False


def test_cross_validation_ignores_non_five_year_windows():
   parsed = pd.DataFrame({
      'company_id': ['TCS'],
      'metric_type': ['sales_growth'],
      'period_years': [10],
      'value_pct': [30.0]
   })
   ratios = pd.DataFrame({
      'company_id': ['TCS'],
      'year': ['Mar 2024'],
      'revenue_cagr_5yr': [10.0],
      'pat_cagr_5yr': [10.0]
   })

   assert cross_validate_against_ratio_engine(parsed, ratios).empty
