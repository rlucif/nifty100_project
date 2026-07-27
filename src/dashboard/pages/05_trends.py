import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
   sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from src.analytics.periods import (  # noqa: E402
   add_period_columns,
   deduplicate_company_years
)
from src.dashboard.utils.db import (  # noqa: E402
   get_companies,
   get_cf,
   get_pl,
   get_ratios
)
from src.dashboard.utils.ui import (  # noqa: E402
   company_selector,
   page_header
)

st.set_page_config(page_title='Trend Analysis | Nifty 100', layout='wide')

HISTORY_YEARS = 10
MAX_METRICS = 3

LINE_COLOURS = ['#1F3864', '#C00000', '#2E7D32']

# Metric label mapped to (source, column).
TREND_METRICS = {
   'Revenue (Cr)': ('pl', 'sales'),
   'Net profit (Cr)': ('pl', 'net_profit'),
   'Operating profit (Cr)': ('pl', 'operating_profit'),
   'EPS': ('pl', 'eps'),
   'ROE %': ('ratios', 'return_on_equity_pct'),
   'Net profit margin %': ('ratios', 'net_profit_margin_pct'),
   'Operating margin %': ('ratios', 'operating_profit_margin_pct'),
   'Debt / Equity': ('ratios', 'debt_to_equity'),
   'Free cash flow (Cr)': ('ratios', 'free_cash_flow_cr'),
   'Asset turnover': ('ratios', 'asset_turnover'),
   'Cash from operations (Cr)': ('cf', 'operating_activity')
}


def build_trend_frame(ticker):
   # One row per period with every selectable metric attached.
   profit_df = deduplicate_company_years(get_pl(ticker))
   ratios_df = deduplicate_company_years(get_ratios(ticker))
   cashflow_df = deduplicate_company_years(get_cf(ticker))

   if profit_df.empty and ratios_df.empty:
      return pd.DataFrame()

   base = profit_df if not profit_df.empty else ratios_df
   frame = base[['company_id', 'year']].copy()

   for source_df, columns in (
      (profit_df, ['sales', 'net_profit', 'operating_profit', 'eps']),
      (ratios_df, [
         'return_on_equity_pct',
         'net_profit_margin_pct',
         'operating_profit_margin_pct',
         'debt_to_equity',
         'free_cash_flow_cr',
         'asset_turnover'
      ]),
      (cashflow_df, ['operating_activity'])
   ):
      if source_df.empty:
         continue

      available = [c for c in columns if c in source_df.columns]
      frame = frame.merge(
         source_df[['company_id', 'year'] + available],
         on=['company_id', 'year'],
         how='left'
      )

   frame = add_period_columns(frame)
   frame = frame[frame['period_sort_key'] > 0]
   return frame.sort_values('period_sort_key').tail(HISTORY_YEARS)


def annotate_year_on_year(values):
   # Percentage change against the previous period, blank for the first point and wherever the base is zero or missing.
   annotations = []

   for index, value in enumerate(values):
      if index == 0 or pd.isna(value):
         annotations.append('')
         continue

      previous = values[index - 1]
      if pd.isna(previous) or previous == 0:
         annotations.append('')
         continue

      change = (value - previous) / abs(previous) * 100
      annotations.append(f'{change:+.1f}%')

   return annotations


def render_trend_chart(frame, selected_metrics):
   figure = go.Figure()

   for position, label in enumerate(selected_metrics):
      _source, column = TREND_METRICS[label]

      if column not in frame.columns:
         continue

      values = list(frame[column])
      annotations = annotate_year_on_year(values)

      figure.add_trace(go.Scatter(
         x=list(frame['year']),
         y=values,
         name=label,
         mode='lines+markers+text',
         text=annotations,
         textposition='top center',
         textfont={'size': 9},
         line={
            'color': LINE_COLOURS[position % len(LINE_COLOURS)],
            'width': 2.5
         },
         yaxis='y' if position == 0 else f'y{position + 1}'
      ))

   layout = {
      'height': 520,
      'margin': {'t': 40, 'b': 40, 'l': 60, 'r': 60},
      'legend': {'orientation': 'h', 'y': 1.1, 'x': 0},
      'hovermode': 'x unified',
      'xaxis': {'title': 'Period'}
   }

   for position, label in enumerate(selected_metrics):
      axis_key = 'yaxis' if position == 0 else f'yaxis{position + 1}'
      axis = {'title': label}

      if position > 0:
         axis.update({
            'overlaying': 'y',
            'side': 'right' if position == 1 else 'left',
            'showgrid': False,
            'position': 1.0 if position == 1 else 0.0
         })

      layout[axis_key] = axis

   figure.update_layout(**layout)
   st.plotly_chart(figure, width='stretch')


def main():
   page_header(
      'Trend Analysis',
      'Overlay up to three metrics across ten years. '
      'Each point is annotated with its year on year change.'
   )

   companies_df = get_companies()
   ticker = company_selector(companies_df, key='trends_search')

   if not ticker:
      st.info('Select a company to begin.')
      return

   selected_metrics = st.multiselect(
      f'Metrics (up to {MAX_METRICS})',
      list(TREND_METRICS.keys()),
      default=['Revenue (Cr)', 'Net profit (Cr)'],
      max_selections=MAX_METRICS
   )

   if not selected_metrics:
      st.info('Pick at least one metric.')
      return

   frame = build_trend_frame(ticker)

   if frame.empty:
      st.warning('No history is available for this company.')
      return

   if len(frame) < HISTORY_YEARS:
      st.caption(
         f'{len(frame)} years of data available for {ticker}. '
         'The chart shows the full available history.'
      )

   render_trend_chart(frame, selected_metrics)

   with st.expander('Underlying data'):
      columns = ['year'] + [
         TREND_METRICS[label][1]
         for label in selected_metrics
         if TREND_METRICS[label][1] in frame.columns
      ]
      st.dataframe(
         frame[columns].round(2),
         hide_index=True,
         width='stretch'
      )


main()
