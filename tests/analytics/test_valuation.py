import pandas as pd
import pytest

from src.analytics.valuation import (
   CAUTION_MULTIPLE,
   DISCOUNT_MULTIPLE,
   FLAG_CAUTION,
   FLAG_DISCOUNT,
   FLAG_FAIR,
   assign_flag,
   calculate_fcf_yield,
   calculate_median_pe_history
)


def test_fcf_yield_is_a_percentage_of_market_cap():
   assert calculate_fcf_yield(500.0, 10000.0) == 5.0


def test_fcf_yield_can_be_negative():
   # A company burning cash has a negative yield, which is meaningful.
   assert calculate_fcf_yield(-250.0, 10000.0) == -2.5


def test_fcf_yield_handles_missing_inputs():
   assert calculate_fcf_yield(None, 10000.0) is None
   assert calculate_fcf_yield(500.0, None) is None


def test_fcf_yield_rejects_zero_market_cap():
   assert calculate_fcf_yield(500.0, 0) is None


def test_flag_is_caution_above_the_caution_multiple():
   # Sector median 40, so Caution begins above 60.
   assert assign_flag(40 * CAUTION_MULTIPLE + 1, 40) == FLAG_CAUTION


def test_flag_is_discount_below_the_discount_multiple():
   # Sector median 40, so Discount begins below 28.
   assert assign_flag(40 * DISCOUNT_MULTIPLE - 1, 40) == FLAG_DISCOUNT


def test_flag_is_fair_between_the_thresholds():
   assert assign_flag(40, 40) == FLAG_FAIR


def test_flag_boundaries_are_not_flagged():
   # Exactly on a boundary is Fair, because both tests are strict.
   assert assign_flag(40 * CAUTION_MULTIPLE, 40) == FLAG_FAIR
   assert assign_flag(40 * DISCOUNT_MULTIPLE, 40) == FLAG_FAIR


@pytest.mark.parametrize(
   'pe_ratio, sector_median',
   [(None, 40), (40, None), (40, 0)]
)
def test_flag_is_none_when_comparison_is_impossible(pe_ratio, sector_median):
   assert assign_flag(pe_ratio, sector_median) is None


def test_median_pe_history_uses_the_recent_window():
   # Six years supplied, window of five: the earliest year is dropped, so the median is of 20, 30, 40, 50, 60.
   market_cap = pd.DataFrame({
      'company_id': ['TCS'] * 6,
      'year': [2019, 2020, 2021, 2022, 2023, 2024],
      'pe_ratio': [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]
   })

   result = calculate_median_pe_history(market_cap, window_years=5)
   assert result.loc[0, 'median_pe_5yr'] == 40.0


def test_median_pe_history_covers_every_company():
   market_cap = pd.DataFrame({
      'company_id': ['TCS', 'TCS', 'INFY'],
      'year': [2023, 2024, 2024],
      'pe_ratio': [20.0, 30.0, 25.0]
   })

   result = calculate_median_pe_history(market_cap)
   assert set(result['company_id']) == {'TCS', 'INFY'}
