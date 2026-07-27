import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
   sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from src.dashboard.utils.db import get_universe  # noqa: E402
from src.dashboard.utils.ui import (  # noqa: E402
   dataframe_download_button,
   page_header,
   simulated_note
)
from src.screener.engine import ScreenerEngine  # noqa: E402

st.set_page_config(page_title='Screener | Nifty 100', layout='wide')

# (state key, label, column, operator, min, max, default, step)
SLIDER_SPECS = [
   ('roe_min', 'ROE minimum %', 'return_on_equity_pct', '>=',
    0.0, 60.0, 0.0, 1.0),
   ('de_max', 'D/E maximum', 'debt_to_equity', '<=',
    0.0, 10.0, 10.0, 0.1),
   ('fcf_min', 'Free cash flow minimum (Cr)', 'free_cash_flow_cr', '>=',
    -50000.0, 50000.0, -50000.0, 1000.0),
   ('rev_cagr_min', 'Revenue CAGR 5y minimum %', 'revenue_cagr_5yr', '>=',
    -10.0, 40.0, -10.0, 1.0),
   ('pat_cagr_min', 'PAT CAGR 5y minimum %', 'pat_cagr_5yr', '>=',
    -10.0, 60.0, -10.0, 1.0),
   ('opm_min', 'OPM minimum %', 'operating_profit_margin_pct', '>=',
    0.0, 60.0, 0.0, 1.0),
   ('pe_max', 'P/E maximum', 'pe_ratio', '<=',
    0.0, 100.0, 100.0, 1.0),
   ('pb_max', 'P/B maximum', 'pb_ratio', '<=',
    0.0, 20.0, 20.0, 0.5),
   ('dy_min', 'Dividend yield minimum %', 'dividend_yield_pct', '>=',
    0.0, 6.0, 0.0, 0.1),
   ('icr_min', 'Interest coverage minimum', 'interest_coverage', '>=',
    0.0, 50.0, 0.0, 1.0)
]

# Preset name mapped to the slider values it fills in.
PRESET_BUTTONS = [
   ('quality_compounder', 'Quality', {
      'roe_min': 15.0, 'de_max': 1.0, 'fcf_min': 0.0, 'rev_cagr_min': 10.0
   }),
   ('value_pick', 'Value', {
      'pe_max': 20.0, 'pb_max': 3.0, 'de_max': 2.0, 'dy_min': 1.0
   }),
   ('growth_accelerator', 'Growth', {
      'pat_cagr_min': 20.0, 'rev_cagr_min': 15.0, 'de_max': 2.0
   }),
   ('dividend_champion', 'Dividend', {
      'dy_min': 2.0, 'fcf_min': 0.0
   }),
   ('debt_free_blue_chip', 'Debt-Free', {
      'de_max': 0.05, 'roe_min': 12.0
   }),
   ('turnaround_watch', 'Turnaround', {
      'fcf_min': 0.0, 'rev_cagr_min': 10.0
   })
]

RESULT_COLUMNS = [
   'company_id',
   'company_name',
   'broad_sector',
   'composite_quality_score',
   'return_on_equity_pct',
   'debt_to_equity',
   'free_cash_flow_cr',
   'revenue_cagr_5yr',
   'pat_cagr_5yr',
   'operating_profit_margin_pct',
   'pe_ratio',
   'pb_ratio',
   'dividend_yield_pct',
   'interest_coverage'
]

COLUMN_LABELS = {
   'company_id': 'Ticker',
   'company_name': 'Company',
   'broad_sector': 'Sector',
   'composite_quality_score': 'Score',
   'return_on_equity_pct': 'ROE %',
   'debt_to_equity': 'D/E',
   'free_cash_flow_cr': 'FCF (Cr)',
   'revenue_cagr_5yr': 'Rev CAGR 5y %',
   'pat_cagr_5yr': 'PAT CAGR 5y %',
   'operating_profit_margin_pct': 'OPM %',
   'pe_ratio': 'P/E',
   'pb_ratio': 'P/B',
   'dividend_yield_pct': 'Div Yield %',
   'interest_coverage': 'ICR'
}


def initialise_state():
   for key, _label, _column, _operator, _low, _high, default, _step in \
         SLIDER_SPECS:
      st.session_state.setdefault(key, default)


def apply_preset(values):
   # Reset every slider to its neutral default, then apply the preset so a leftover value from a previous preset cannot leak through.
   for key, _label, _column, _operator, _low, _high, default, _step in \
         SLIDER_SPECS:
      st.session_state[key] = default

   for key, value in values.items():
      st.session_state[key] = value


def render_preset_buttons():
   st.sidebar.markdown('**Presets**')

   first_row = st.sidebar.columns(3)
   second_row = st.sidebar.columns(3)
   buttons = list(first_row) + list(second_row)

   for column, (preset_key, label, values) in zip(buttons, PRESET_BUTTONS):
      if column.button(label, key=f'preset_{preset_key}',
                       width='stretch'):
         apply_preset(values)
         st.rerun()

   if st.sidebar.button('Reset all', width='stretch'):
      apply_preset({})
      st.rerun()


def render_sliders():
   st.sidebar.markdown('**Filters**')
   active_filters = {}

   for key, label, column, operator, low, high, default, step in \
         SLIDER_SPECS:
      # No value= argument: with key= set, Streamlit reads the current value from session_state, which is what the preset buttons write.
      value = st.sidebar.slider(
         label,
         min_value=low,
         max_value=high,
         step=step,
         key=key
      )

      # A slider parked at its neutral end is not a filter.
      if operator == '>=' and value <= low:
         continue
      if operator == '<=' and value >= high:
         continue

      threshold_key = 'min' if operator == '>=' else 'max'
      active_filters[column] = {
         'operator': operator,
         'threshold': {threshold_key: value}
      }

   return active_filters


def main():
   page_header(
      'Screener',
      'Move the sliders or pick a preset. Results update immediately.'
   )

   initialise_state()

   universe_df = get_universe()
   engine = ScreenerEngine()
   engine.load_config()

   render_preset_buttons()
   active_filters = render_sliders()

   try:
      results_df = engine.apply_filters(universe_df, active_filters)
   except KeyError as error:
      st.error(f'A filtered column is missing from the data: {error}')
      return

   results_df = results_df.sort_values(
      'composite_quality_score',
      ascending=False
   )

   if active_filters:
      st.markdown(
         f'### {len(results_df)} companies match your filters'
      )
   else:
      st.markdown(
         f'### Showing all {len(results_df)} companies - no filters active'
      )

   applied = ', '.join(
      COLUMN_LABELS.get(column, column) for column in active_filters
   )
   st.caption(f'Active filters: {applied}' if applied else 'Active filters: none')

   if results_df.empty:
      st.warning(
         'No company meets every filter. Loosen a slider to widen the '
         'search.'
      )
      return

   display_df = results_df[RESULT_COLUMNS].rename(columns=COLUMN_LABELS)

   for column in display_df.columns:
      if pd.api.types.is_numeric_dtype(display_df[column]):
         display_df[column] = display_df[column].round(2)

   st.dataframe(display_df, hide_index=True, width='stretch')

   dataframe_download_button(
      display_df,
      'screener_results.csv',
      label=f'Download {len(display_df)} results as CSV'
   )

   st.divider()
   st.caption(
      'Banks, NBFCs and insurers are exempt from the D/E ceiling because '
      'high leverage is structurally normal for them. Companies with no '
      'interest expense are treated as having infinite interest coverage.'
   )
   with st.expander('Why a preset here can differ from the Excel export'):
      st.markdown(
         'The preset buttons fill in the ten sliders on this screen, but '
         'three preset rules cannot be expressed as a slider:\n\n'
         '- **Debt-Free Blue Chip** screens on `D/E == 0` exactly and on '
         'revenue above 5,000 Cr. The slider approximates this with '
         '`D/E <= 0.05`, so it returns more companies.\n'
         '- **Dividend Champion** also caps the dividend payout ratio '
         'at 80%.\n'
         '- **Turnaround Watch** also requires debt to equity to be '
         'falling year on year.\n\n'
         'Run `make screener` for `output/screener_output.xlsx`, which '
         'applies every preset rule in full.'
      )
   simulated_note()


main()
