import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
   sys.path.insert(0, str(PROJECT_ROOT))

import plotly.express as px  # noqa: E402
import streamlit as st  # noqa: E402
from src.dashboard.utils.db import get_universe  # noqa: E402
from src.dashboard.utils.ui import (  # noqa: E402
   format_metric,
   kpi_row,
   page_header,
   simulated_note
)

st.set_page_config(page_title='Sector Analysis | Nifty 100', layout='wide')
ALL_SECTORS = 'All sectors'

MEDIAN_METRICS = {
   'return_on_equity_pct': 'ROE %',
   'return_on_capital_employed_pct': 'ROCE %',
   'net_profit_margin_pct': 'NPM %',
   'operating_profit_margin_pct': 'OPM %',
   'debt_to_equity': 'D/E',
   'revenue_cagr_5yr': 'Rev CAGR 5y %',
   'composite_quality_score': 'Composite score'
}


def render_bubble_chart(frame):
   plot_frame = frame.dropna(subset=['sales', 'return_on_equity_pct']).copy()

   if plot_frame.empty:
      st.info('No company in this selection has both revenue and ROE.')
      return

   # Market cap drives bubble size, so rows without it would vanish. Give them the smallest visible bubble instead of dropping them.
   plot_frame['bubble_size'] = plot_frame['market_cap_crore'].fillna(
      plot_frame['market_cap_crore'].min()
   )
   plot_frame['sub_sector'] = plot_frame['sub_sector'].fillna('Unclassified')

   figure = px.scatter(
      plot_frame,
      x='sales',
      y='return_on_equity_pct',
      size='bubble_size',
      color='sub_sector',
      hover_name='company_name',
      hover_data={
         'company_id': True,
         'sales': ':,.0f',
         'return_on_equity_pct': ':.2f',
         'market_cap_crore': ':,.0f',
         'bubble_size': False,
         'sub_sector': True
      },
      size_max=55,
      labels={
         'sales': 'Revenue (INR Crore)',
         'return_on_equity_pct': 'ROE %',
         'sub_sector': 'Sub-sector',
         'market_cap_crore': 'Market cap (Cr)'
      }
   )

   figure.update_layout(
      height=560,
      margin={'t': 30, 'b': 40, 'l': 40, 'r': 20},
      legend={'title': 'Sub-sector'}
   )

   st.plotly_chart(figure, width='stretch')
   st.caption(
      'Bubble size is market capitalisation, a SIMULATED metric. '
      'Companies without a market cap are drawn at the smallest size.'
   )


def render_sector_medians(universe_df, selected_sector):
   medians = (
      universe_df.groupby(universe_df['broad_sector'].fillna('Unclassified'))
      [list(MEDIAN_METRICS.keys())]
      .median()
      .round(2)
   )

   metric_column = st.selectbox(
      'Median metric',
      list(MEDIAN_METRICS.keys()),
      format_func=lambda key: MEDIAN_METRICS[key]
   )

   chart_frame = (
      medians[metric_column]
      .sort_values(ascending=False)
      .rename_axis('Sector')
      .reset_index(name=MEDIAN_METRICS[metric_column])
   )

   colours = [
      '#C00000' if sector == selected_sector else '#1F3864'
      for sector in chart_frame['Sector']
   ]

   figure = px.bar(
      chart_frame,
      x='Sector',
      y=MEDIAN_METRICS[metric_column]
   )
   figure.update_traces(marker_color=colours)
   figure.update_layout(
      height=380,
      margin={'t': 20, 'b': 80, 'l': 40, 'r': 20},
      xaxis={'tickangle': -35}
   )

   st.plotly_chart(figure, width='stretch')

   if selected_sector != ALL_SECTORS:
      st.caption(f'{selected_sector} is highlighted in red.')


def main():
   page_header(
      'Sector Analysis',
      'Compare scale, returns and valuation within and across sectors.'
   )

   universe_df = get_universe()

   sectors = sorted(
      universe_df['broad_sector'].fillna('Unclassified').unique()
   )
   selected_sector = st.selectbox(
      'Sector',
      [ALL_SECTORS] + sectors
   )

   if selected_sector == ALL_SECTORS:
      frame = universe_df.copy()
   else:
      frame = universe_df[
         universe_df['broad_sector'].fillna('Unclassified')
         == selected_sector
      ]

   kpi_row([
      ('Companies', f'{len(frame)}'),
      ('Median ROE', format_metric(
         frame['return_on_equity_pct'].median(), '%'
      )),
      ('Median D/E', format_metric(frame['debt_to_equity'].median())),
      ('Median P/E', format_metric(frame['pe_ratio'].median())),
      ('Median Rev CAGR 5y', format_metric(
         frame['revenue_cagr_5yr'].median(), '%'
      )),
      ('Total revenue', format_metric(frame['sales'].sum(), ' Cr', 0))
   ])

   st.divider()
   st.subheader('Revenue against returns')
   render_bubble_chart(frame)

   st.divider()
   st.subheader('Sector medians')
   render_sector_medians(universe_df, selected_sector)

   simulated_note()


main()
