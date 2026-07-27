'''
Screener engine unit tests.

Covers the two business rules that are implemented in code rather than
in config, the composite score, and the config validation contract.
'''

import pandas as pd
import pytest

from src.screener.engine import ScreenerEngine


@pytest.fixture
def engine():
   instance = ScreenerEngine()
   instance.load_config()

   return instance


@pytest.fixture
def sample_universe():
   # Two Financials and three non-Financials with contrasting leverage.
   return pd.DataFrame({
      'company_id': ['HDFCBANK', 'SBIN', 'TCS', 'RELIANCE', 'ADANIGREEN'],
      'broad_sector': [
         'Financials',
         'Financials',
         'Information Technology',
         'Energy',
         'Energy'
      ],
      'return_on_equity_pct': [16.0, 14.0, 50.0, 9.0, 12.8],
      'debt_to_equity': [8.2, 9.1, 0.09, 0.44, 6.6],
      'interest_coverage': [1.2, 1.1, None, 8.0, 1.4],
      'free_cash_flow_cr': [100.0, -50.0, 4000.0, 2000.0, -900.0],
      'net_profit_margin_pct': [20.0, 12.0, 19.0, 8.0, 11.0],
      'return_on_capital_employed_pct': [7.0, 6.0, 60.0, 12.0, 9.0],
      'revenue_cagr_5yr': [12.0, 9.0, 8.0, 14.0, 35.0],
      'pat_cagr_5yr': [15.0, 8.0, 10.0, 11.0, None],
      'fcf_cagr_5yr': [5.0, None, 9.0, 4.0, None],
      'cfo_to_pat_ratio': [1.2, 0.9, 1.1, 1.3, 0.4],
      'fcf_positive_flag': [1, 0, 1, 1, 0]
   })


def test_config_loads_and_validates(engine):
   assert engine.validate_config() is True


def test_all_six_presets_are_defined(engine):
   assert len(engine.preset_names()) == 6


def test_invalid_operator_is_rejected(engine):
   engine.config['filters']['return_on_equity_pct']['operator'] = '=~'

   with pytest.raises(ValueError, match='unsupported operator'):
      engine.validate_config()


def test_empty_threshold_is_rejected(engine):
   # This must be caught for every filter, not only the last one.
   engine.config['filters']['return_on_equity_pct']['threshold'] = {}

   with pytest.raises(ValueError, match='empty threshold'):
      engine.validate_config()


def test_unknown_preset_raises(engine, sample_universe):
   with pytest.raises(ValueError, match='Unknown preset'):
      engine.run_preset('not_a_preset', sample_universe)


def test_financials_are_exempt_from_upper_bound_debt_filter(
   engine,
   sample_universe
):
   # Rule 1: banks carry structurally high leverage, so a D/E ceiling
   # must not reject them.
   filters = {
      'debt_to_equity': {'operator': '<', 'threshold': {'max': 1.0}}
   }

   result = engine.apply_filters(sample_universe, filters)

   assert set(result['company_id']) == {'HDFCBANK', 'SBIN', 'TCS', 'RELIANCE'}
   assert 'ADANIGREEN' not in set(result['company_id'])


def test_financials_are_not_exempt_from_equality_debt_filter(
   engine,
   sample_universe
):
   # A bank with D/E of 8.2 is not debt free, so the Debt-Free Blue Chip
   # equality test still applies to it.
   filters = {
      'debt_to_equity': {'operator': '==', 'threshold': {'max': 0}}
   }

   result = engine.apply_filters(sample_universe, filters)

   assert result.empty


def test_debt_free_company_passes_interest_coverage_minimum(
   engine,
   sample_universe
):
   # Rule 2: TCS has no interest expense so its ICR is null, which
   # represents infinite coverage and must pass any minimum.
   filters = {
      'interest_coverage': {'operator': '>=', 'threshold': {'min': 5.0}}
   }

   result = engine.apply_filters(sample_universe, filters)

   assert 'TCS' in set(result['company_id'])
   assert 'RELIANCE' in set(result['company_id'])
   assert 'HDFCBANK' not in set(result['company_id'])


def test_missing_value_fails_an_ordinary_filter(engine, sample_universe):
   # pat_cagr_5yr is null for ADANIGREEN, which must not pass.
   filters = {
      'pat_cagr_5yr': {'operator': '>', 'threshold': {'min': 5.0}}
   }

   result = engine.apply_filters(sample_universe, filters)

   assert 'ADANIGREEN' not in set(result['company_id'])


def test_missing_column_raises_keyerror(engine, sample_universe):
   filters = {
      'not_a_column': {'operator': '>', 'threshold': {'min': 1}}
   }

   with pytest.raises(KeyError):
      engine.apply_filters(sample_universe, filters)


def test_composite_score_is_bounded(engine, sample_universe):
   scores = engine.calculate_composite_score(sample_universe)

   assert scores.between(0, 100).all()


def test_composite_score_rewards_the_stronger_company(
   engine,
   sample_universe
):
   scored = engine.add_composite_scores(sample_universe)
   ranked = scored.set_index('company_id')['composite_quality_score']

   # TCS: high ROE, high ROCE, no debt, strong cash.
   # ADANIGREEN: heavy debt, negative free cash flow.
   assert ranked['TCS'] > ranked['ADANIGREEN']


def test_add_composite_scores_sorts_descending(engine, sample_universe):
   scored = engine.add_composite_scores(sample_universe)
   scores = scored['composite_quality_score'].tolist()

   assert scores == sorted(scores, reverse=True)


def test_sector_relative_score_is_produced(engine, sample_universe):
   scored = engine.add_composite_scores(sample_universe)

   assert 'sector_relative_score' in scored.columns
   assert scored['sector_relative_score'].between(0, 100).all()
