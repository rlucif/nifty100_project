# Checks that individual rules fire on the conditions they claim, that
# confidence stays inside its band, and that the relative fallback only
# appears when no absolute rule triggered

import pandas as pd
import pytest

from src.nlp.features import (
   consecutive_direction,
   sustained_above,
   trailing_streak
)
from src.nlp.pros_cons_generator import (
   CONFIDENCE_CEILING,
   CONFIDENCE_FLOOR,
   generate_pros_and_cons
)


def _base_features(**overrides):
   # A deliberately unremarkable company: trips no rule either way.
   features = {
      'company_id': 'TESTCO',
      'company_name': 'Test Company Ltd',
      'broad_sector': 'Industrials',
      'latest_year': 'Mar 2024',
      'years_of_data': 10,
      'roe': 12.0,
      'roce': 14.0,
      'opm': 15.0,
      'npm': 8.0,
      'debt_to_equity': 0.8,
      'interest_coverage': 5.0,
      'net_profit': 500.0,
      'dividend_payout_pct': 30.0,
      'dividend_yield_pct': 1.0,
      'free_cash_flow': 100.0,
      'net_debt': 200.0,
      'ebitda': 400.0,
      'revenue_cagr_5yr': 9.0,
      'pat_cagr_5yr': 8.0,
      'eps_cagr_5yr': 8.0,
      'roe_series': pd.Series([12.0] * 10),
      'opm_series': pd.Series([15.0] * 10),
      'eps_series': pd.Series([10.0] * 10),
      'sales_series': pd.Series([1000.0] * 10),
      'fcf_series': pd.Series([100.0] * 10),
      'de_series': pd.Series([0.8] * 10),
      'assets_series': pd.Series([5000.0] * 10),
      'borrowings_series': pd.Series([800.0] * 10)
   }
   features.update(overrides)

   return {features['company_id']: features}


def _rule_ids(frame, entry_type=None):
   subset = frame if entry_type is None else frame[frame['type'] == entry_type]

   return set(subset['rule_id'])


# Streak and trend helpers
def test_trailing_streak_counts_from_the_latest_year():
   assert trailing_streak(pd.Series([-1, 1, 1, 1]), lambda v: v > 0) == 3


def test_trailing_streak_breaks_on_a_missing_value():
   # 'five consecutive years' needs five known years.
   assert trailing_streak(pd.Series([1, None, 1, 1]), lambda v: v > 0) == 2


def test_consecutive_direction_requires_every_step():
   assert consecutive_direction(pd.Series([1, 2, 3, 4]), rising=True) is True
   assert consecutive_direction(pd.Series([1, 2, 2, 4]), rising=True) is False


def test_consecutive_direction_needs_enough_history():
   assert consecutive_direction(pd.Series([1, 2]), rising=True) is False


def test_sustained_above_checks_the_recent_window():
   assert sustained_above(pd.Series([1, 25, 26, 27]), 20, periods=3) is True
   assert sustained_above(pd.Series([25, 26, 19]), 20, periods=3) is False


# Pro rules
def test_high_sustained_roe_triggers_pro_01():
   features = _base_features(
      roe=32.0, roe_series=pd.Series([25.0, 28.0, 30.0, 32.0])
   )

   assert 'PRO-01' in _rule_ids(generate_pros_and_cons(features), 'pro')


def test_long_positive_fcf_streak_triggers_pro_02():
   features = _base_features(fcf_series=pd.Series([50.0] * 8))

   assert 'PRO-02' in _rule_ids(generate_pros_and_cons(features), 'pro')


def test_zero_debt_triggers_pro_03_at_full_confidence():
   features = _base_features(debt_to_equity=0.0)
   result = generate_pros_and_cons(features)

   pro_03 = result[result['rule_id'] == 'PRO-03']

   assert len(pro_03) == 1
   assert pro_03.iloc[0]['confidence_pct'] == CONFIDENCE_CEILING


def test_null_interest_coverage_is_treated_as_debt_free():
   # A null coverage ratio means zero interest expense.
   features = _base_features(interest_coverage=None)
   result = generate_pros_and_cons(features)

   pro_07 = result[result['rule_id'] == 'PRO-07']

   assert len(pro_07) == 1
   assert pro_07.iloc[0]['confidence_pct'] == CONFIDENCE_CEILING


def test_operating_leverage_triggers_pro_11():
   features = _base_features(revenue_cagr_5yr=10.0, pat_cagr_5yr=22.0)

   assert 'PRO-11' in _rule_ids(generate_pros_and_cons(features), 'pro')


# Con rules
def test_high_leverage_triggers_con_01_for_a_non_financial():
   features = _base_features(debt_to_equity=3.5)

   assert 'CON-01' in _rule_ids(generate_pros_and_cons(features), 'con')


def test_high_leverage_does_not_trigger_con_01_for_a_financial():
   features = _base_features(
      broad_sector='Financials', debt_to_equity=8.0
   )

   assert 'CON-01' not in _rule_ids(generate_pros_and_cons(features), 'con')


def test_net_loss_triggers_con_04_at_full_confidence():
   features = _base_features(net_profit=-250.0)
   result = generate_pros_and_cons(features)

   con_04 = result[result['rule_id'] == 'CON-04']

   assert len(con_04) == 1
   assert con_04.iloc[0]['confidence_pct'] == CONFIDENCE_CEILING


def test_weak_interest_coverage_triggers_con_06():
   features = _base_features(interest_coverage=1.1)

   assert 'CON-06' in _rule_ids(generate_pros_and_cons(features), 'con')


def test_payout_above_one_hundred_triggers_con_07():
   features = _base_features(dividend_payout_pct=140.0)

   assert 'CON-07' in _rule_ids(generate_pros_and_cons(features), 'con')


def test_net_debt_above_three_times_ebitda_triggers_con_11():
   features = _base_features(net_debt=2000.0, ebitda=400.0)

   assert 'CON-11' in _rule_ids(generate_pros_and_cons(features), 'con')


def test_declining_revenue_triggers_con_05():
   features = _base_features(
      sales_series=pd.Series([1200.0, 1100.0, 1000.0])
   )

   assert 'CON-05' in _rule_ids(generate_pros_and_cons(features), 'con')


# Confidence and fallback behaviour
def test_every_confidence_stays_inside_its_band():
   features = _base_features(
      roe=45.0,
      roe_series=pd.Series([25.0, 30.0, 40.0, 45.0]),
      debt_to_equity=0.0,
      net_profit=-100.0,
      revenue_cagr_5yr=35.0,
      pat_cagr_5yr=55.0
   )

   result = generate_pros_and_cons(features)

   assert result['confidence_pct'].between(
      CONFIDENCE_FLOOR, CONFIDENCE_CEILING
   ).all()


def test_confidence_rises_with_signal_strength():
   modest = generate_pros_and_cons(
      _base_features(revenue_cagr_5yr=16.0)
   )
   strong = generate_pros_and_cons(
      _base_features(revenue_cagr_5yr=29.0)
   )

   modest_score = modest[modest['rule_id'] == 'PRO-04'].iloc[0]
   strong_score = strong[strong['rule_id'] == 'PRO-04'].iloc[0]

   assert strong_score['confidence_pct'] > modest_score['confidence_pct']


def test_relative_fallback_fires_when_no_absolute_rule_does():
   # A single company cannot be ranked, so no fallback is possible and the frame is simply empty of that rule.
   features = _base_features()
   features['PEER1'] = dict(features['TESTCO'], company_id='PEER1', roe=20.0)
   features['PEER2'] = dict(features['TESTCO'], company_id='PEER2', roe=5.0)

   result = generate_pros_and_cons(features)
   testco = result[result['company_id'] == 'TESTCO']

   assert (testco['type'] == 'pro').sum() >= 1
   assert (testco['type'] == 'con').sum() >= 1


def test_relative_fallback_is_absent_when_absolute_rules_fire():
   features = _base_features(
      roe=32.0,
      roe_series=pd.Series([25.0, 28.0, 30.0, 32.0]),
      net_profit=-100.0
   )

   result = generate_pros_and_cons(features)

   assert 'PRO-13' not in _rule_ids(result, 'pro')
   assert 'CON-13' not in _rule_ids(result, 'con')


@pytest.mark.parametrize('entry_type', ['pro', 'con'])
def test_output_columns_match_the_specification(entry_type):
   result = generate_pros_and_cons(_base_features(net_profit=-1.0))

   assert list(result.columns) == [
      'company_id', 'type', 'rule_id', 'text', 'confidence_pct'
   ]
   assert entry_type in set(result['type']) or result.empty
