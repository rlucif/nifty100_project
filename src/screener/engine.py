'''
This engine serves as the foundation for:
- Preset Screeners
- Custom Screeners
- Health Score
- Peer Comparison

Business rules implemented here rather than in the config file:

1. Financials D/E exemption
   Banks, NBFCs and insurers carry structurally high leverage, so an
   upper-bound D/E filter ("<" or "<=") does not reject them. An
   equality filter such as the Debt-Free Blue Chip D/E == 0 test is
   still applied, because a bank with D/E of 8 is genuinely not
   debt free.

2. Debt Free interest coverage
   interest_coverage is null when interest expense is zero. Such a
   company is Debt Free and is treated as ICR = infinity, so it passes
   any ICR minimum threshold.

3. Missing values
   For every other metric a missing value fails the filter.
'''

import operator
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

# Metrics where a lower reading is the better outcome.
LOWER_IS_BETTER = {'debt_to_equity', 'pe_ratio', 'pb_ratio'}

# Upper-bound operators that trigger the Financials D/E exemption.
UPPER_BOUND_OPERATORS = {'<', '<='}


class ScreenerEngine:
   # Generic financial screener engine
   OPERATOR_MAP = {
      '>': operator.gt,
      '>=': operator.ge,
      '<': operator.lt,
      '<=': operator.le,
      '==': operator.eq,
      '!=': operator.ne,
   }

   def __init__(self, config_path=None):
      # Initialize screener engine
      if config_path is None:
         project_root = Path(__file__).resolve().parents[2]
         config_path = project_root / 'config' / 'screener_config.yaml'

      self.config_path = Path(config_path)
      self.config = {}

   # Configuration
   def load_config(self):
      # Load screener configuration
      with self.config_path.open('r', encoding='utf-8') as file:
         self.config = yaml.safe_load(file)

      return self.config

   def _ensure_config(self):
      if not self.config:
         self.load_config()

      return self.config

   def validate_config(self):
      # Validate screener configuration
      if not self.config:
         raise ValueError('Configuration has not been loaded.')

      if 'filters' not in self.config:
         raise ValueError("Missing 'filters' section in configuration.")

      for column, filter_config in self.config['filters'].items():
         for required_key in ('enabled', 'operator', 'threshold'):
            if required_key not in filter_config:
               raise ValueError(f"{column}: missing '{required_key}'")

         self._validate_filter(column, filter_config)

      for preset_name, preset in self.config.get('presets', {}).items():
         for column, filter_config in preset.get('filters', {}).items():
            if 'operator' not in filter_config:
               raise ValueError(
                  f"{preset_name}.{column}: missing 'operator'"
               )
            if 'threshold' not in filter_config:
               raise ValueError(
                  f"{preset_name}.{column}: missing 'threshold'"
               )

            self._validate_filter(
               f'{preset_name}.{column}',
               filter_config
            )

      return True

   def _validate_filter(self, column, filter_config):
      operator_name = filter_config['operator']

      if (operator_name not in self.OPERATOR_MAP
            and operator_name != 'between'):
         raise ValueError(f"{column}: unsupported operator '{operator_name}'")

      threshold = filter_config['threshold']

      if not threshold:
         raise ValueError(f'{column}: empty threshold')

      if 'min' not in threshold and 'max' not in threshold:
         raise ValueError(
            f"{column}: threshold must contain 'min' or 'max'"
         )

      if operator_name == 'between':
         if 'min' not in threshold or 'max' not in threshold:
            raise ValueError(
               f"{column}: 'between' needs both 'min' and 'max'"
            )

   # Filtering
   def _build_mask(self, dataframe, column, filter_config):
      # Boolean mask for one metric, including the business rules.
      operator_name = filter_config['operator']
      threshold = filter_config['threshold']

      if operator_name == 'between':
         mask = dataframe[column].between(
            threshold['min'],
            threshold['max'],
            inclusive='both'
         )
      else:
         value = threshold.get('min', threshold.get('max'))
         operation = self.OPERATOR_MAP[operator_name]
         mask = operation(dataframe[column], value)

      mask = mask.fillna(False).astype(bool)

      # Rule 2
      if column == 'interest_coverage':
         mask = mask | dataframe[column].isna()

      # Rule 1: Financials are exempt from upper-bound D/E screening.
      if (column == 'debt_to_equity'
            and operator_name in UPPER_BOUND_OPERATORS
            and 'broad_sector' in dataframe.columns):
         mask = mask | (dataframe['broad_sector'] == 'Financials')

      return mask

   def apply_filters(self, dataframe, filters=None):
      self._ensure_config()
      self.validate_config()

      if filters is None:
         filters = {
            column: filter_config
            for column, filter_config in self.config['filters'].items()
            if filter_config['enabled']
         }

      filtered_df = dataframe.copy()

      for column, filter_config in filters.items():
         if column not in filtered_df.columns:
            raise KeyError(f"Column '{column}' not found.")

         mask = self._build_mask(filtered_df, column, filter_config)
         filtered_df = filtered_df[mask]

      return filtered_df

   def run_preset(self, preset_name, dataframe):
      # Execute a predefined screener preset.
      self._ensure_config()
      self.validate_config()

      presets = self.config.get('presets', {})

      if preset_name not in presets:
         raise ValueError(f"Unknown preset '{preset_name}'.")

      preset_filters = presets[preset_name].get('filters', {})

      result_df = self.apply_filters(dataframe, preset_filters)

      if 'composite_quality_score' in result_df.columns:
         result_df = result_df.sort_values(
            'composite_quality_score',
            ascending=False
         )

      return result_df

   def preset_names(self):
      self._ensure_config()

      return list(self.config.get('presets', {}).keys())

   def preset_label(self, preset_name):
      self._ensure_config()

      return self.config['presets'][preset_name].get('label', preset_name)

   def run_all_presets(self, dataframe):
      return {
         preset_name: self.run_preset(preset_name, dataframe)
         for preset_name in self.preset_names()
      }

   # Composite quality score (Sprint 3 Day 17)
   def _score_series(self, series, lower_percentile, upper_percentile,
                     higher_is_better=True):
      # Winsorise at P10/P90 then scale to 0-100.
      numeric = pd.to_numeric(series, errors='coerce')
      valid = numeric.dropna()

      if valid.empty:
         return pd.Series(50.0, index=series.index)

      lower_bound = np.percentile(valid, lower_percentile)
      upper_bound = np.percentile(valid, upper_percentile)

      if upper_bound == lower_bound:
         scores = pd.Series(50.0, index=series.index)
         return scores.where(numeric.notna(), 50.0)

      capped = numeric.clip(lower_bound, upper_bound)
      scaled = (capped - lower_bound) / (upper_bound - lower_bound) * 100

      if not higher_is_better:
         scaled = 100 - scaled

      return scaled.fillna(50.0)

   def calculate_composite_score(self, dataframe, sector_relative=False):
      # Composite quality score on a 0-100 scale.
      self._ensure_config()

      score_config = self.config['composite_score']
      lower_percentile = score_config['winsorise_lower_percentile']
      upper_percentile = score_config['winsorise_upper_percentile']

      weights = {}
      for component_weights in score_config['weights'].values():
         weights.update(component_weights)

      working_df = dataframe.copy()

      coverage = pd.to_numeric(
         working_df['interest_coverage'],
         errors='coerce'
      )
      working_df['interest_coverage_score'] = coverage.fillna(coverage.max())
      working_df['debt_to_equity_score'] = pd.to_numeric(
         working_df['debt_to_equity'],
         errors='coerce'
      )

      if sector_relative:
         groups = working_df.groupby('broad_sector', dropna=False)
      else:
         groups = [(None, working_df)]

      total_score = pd.Series(0.0, index=working_df.index)

      for _group_name, group_df in groups:
         group_score = pd.Series(0.0, index=group_df.index)

         for metric, weight in weights.items():
            higher_is_better = metric not in LOWER_IS_BETTER
            if metric == 'debt_to_equity_score':
               higher_is_better = False

            metric_score = self._score_series(
               group_df[metric],
               lower_percentile,
               upper_percentile,
               higher_is_better
            )

            group_score = group_score + metric_score * (weight / 100)

         total_score.loc[group_df.index] = group_score

      return total_score.round(2)

   def add_composite_scores(self, dataframe):
      # Attach both the index-wide and the sector-relative score.
      result_df = dataframe.copy()

      result_df['composite_quality_score'] = self.calculate_composite_score(
         result_df
      )
      result_df['sector_relative_score'] = self.calculate_composite_score(
         result_df,
         sector_relative=True
      )

      return result_df.sort_values(
         'composite_quality_score',
         ascending=False
      )
