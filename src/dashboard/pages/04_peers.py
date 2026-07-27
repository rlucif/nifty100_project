import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
   sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from src.analytics.peer import PEER_METRICS  # noqa: E402
from src.dashboard.utils.db import (  # noqa: E402
   get_peer_percentiles,
   get_peers,
   get_universe
)
from src.dashboard.utils.ui import (  # noqa: E402
   ACCENT_COLOUR,
   PRIMARY_COLOUR,
   page_header
)

st.set_page_config(page_title='Peer Comparison | Nifty 100', layout='wide')

# The eight axes shown on the radar.
RADAR_METRICS = [
   'return_on_equity_pct',
   'return_on_capital_employed_pct',
   'net_profit_margin_pct',
   'debt_to_equity',
   'free_cash_flow_cr',
   'pat_cagr_5yr',
   'revenue_cagr_5yr',
   'asset_turnover'
]

METRIC_LABELS = {
   'return_on_equity_pct': 'ROE',
   'return_on_capital_employed_pct': 'ROCE',
   'net_profit_margin_pct': 'NPM',
   'debt_to_equity': 'D/E (inv)',
   'free_cash_flow_cr': 'FCF',
   'pat_cagr_5yr': 'PAT CAGR 5y',
   'revenue_cagr_5yr': 'Rev CAGR 5y',
   'eps_cagr_5yr': 'EPS CAGR 5y',
   'interest_coverage': 'ICR',
   'asset_turnover': 'Asset Turnover'
}

BENCHMARK_HIGHLIGHT = 'background-color: #FFD966; font-weight: bold;'


def percentile_lookup(percentiles_df):
   # company_id -> metric -> percentile rank
   if percentiles_df.empty:
      return {}

   lookup = {}
   for row in percentiles_df.itertuples():
      lookup.setdefault(row.company_id, {})[row.metric] = row.percentile_rank

   return lookup


def render_radar(company_id, lookup, group_members):
   # The radar is drawn on percentile ranks, not raw values, because the raw units are not comparable to each other. D/E is already inverted by the peer engine, so further from the centre is better on every axis.
   company_ranks = lookup.get(company_id, {})

   if not company_ranks:
      st.info('This company has no peer percentile ranks.')
      return

   labels = [METRIC_LABELS.get(metric, metric) for metric in RADAR_METRICS]
   company_values = [
      company_ranks.get(metric) for metric in RADAR_METRICS
   ]

   peer_values = []
   for metric in RADAR_METRICS:
      ranks = [
         lookup.get(member, {}).get(metric)
         for member in group_members
         if lookup.get(member, {}).get(metric) is not None
      ]
      peer_values.append(sum(ranks) / len(ranks) if ranks else None)

   figure = go.Figure()

   figure.add_trace(go.Scatterpolar(
      r=company_values + company_values[:1],
      theta=labels + labels[:1],
      fill='toself',
      name=company_id,
      line={'color': PRIMARY_COLOUR, 'width': 2.5}
   ))
   figure.add_trace(go.Scatterpolar(
      r=peer_values + peer_values[:1],
      theta=labels + labels[:1],
      name='Peer group average',
      line={'color': ACCENT_COLOUR, 'width': 2, 'dash': 'dash'}
   ))

   figure.update_layout(
      polar={'radialaxis': {'visible': True, 'range': [0, 100]}},
      height=460,
      margin={'t': 40, 'b': 40, 'l': 40, 'r': 40},
      legend={'orientation': 'h', 'y': -0.08, 'x': 0}
   )

   st.plotly_chart(figure, width='stretch')
   st.caption(
      'Axes are percentile ranks within the peer group, 0 to 100. '
      'Debt to equity is inverted so less debt scores higher.'
   )


def render_kpi_table(group_df, benchmark_company):
   display_columns = ['company_id', 'company_name'] + PEER_METRICS

   table = group_df[display_columns].copy()
   table = table.rename(columns={
      'company_id': 'Ticker',
      'company_name': 'Company',
      **METRIC_LABELS
   })

   for column in table.columns:
      if pd.api.types.is_numeric_dtype(table[column]):
         table[column] = table[column].round(2)

   def highlight_benchmark(row):
      if row['Ticker'] == benchmark_company:
         return [BENCHMARK_HIGHLIGHT] * len(row)

      return [''] * len(row)

   st.dataframe(
      table.style.apply(highlight_benchmark, axis=1),
      hide_index=True,
      width='stretch'
   )

   if benchmark_company:
      st.caption(
         f'The highlighted row is the peer group benchmark '
         f'({benchmark_company}).'
      )
   else:
      st.caption(
         'This peer group has no benchmark row because its designated '
         'benchmark company has no computed financials.'
      )


def main():
   page_header(
      'Peer Comparison',
      'Rank a company against the companies it actually competes with.'
   )

   peer_groups_df = get_peers()
   universe_df = get_universe()

   group_names = sorted(peer_groups_df['peer_group_name'].dropna().unique())

   if not group_names:
      st.error('No peer groups are defined in the database.')
      return

   selected_group = st.selectbox('Peer group', group_names)

   members_df = peer_groups_df[
      peer_groups_df['peer_group_name'] == selected_group
   ]

   group_df = universe_df[
      universe_df['company_id'].isin(members_df['company_id'])
   ]

   if group_df.empty:
      st.warning('No companies in this peer group have computed financials.')
      return

   # is_benchmark arrives from Excel as the string '1'.
   benchmark_flag = pd.to_numeric(
      members_df['is_benchmark'],
      errors='coerce'
   )
   benchmark_rows = members_df[benchmark_flag == 1]
   benchmark_company = (
      benchmark_rows['company_id'].iloc[0]
      if not benchmark_rows.empty else None
   )

   missing = set(members_df['company_id']) - set(group_df['company_id'])
   if missing:
      st.caption(
         f'{", ".join(sorted(missing))} belongs to this group but has no '
         'computed financials and is excluded.'
      )

   percentiles_df = get_peer_percentiles(selected_group)
   lookup = percentile_lookup(percentiles_df)
   left_column, right_column = st.columns([1, 1])

   with left_column:
      st.subheader('Radar')

      company_options = sorted(group_df['company_id'])
      default_index = (
         company_options.index(benchmark_company)
         if benchmark_company in company_options else 0
      )
      selected_company = st.selectbox(
         'Company',
         company_options,
         index=default_index
      )

      render_radar(
         selected_company,
         lookup,
         list(group_df['company_id'])
      )

   with right_column:
      st.subheader(f'{selected_group} at a glance')
      st.metric('Companies in group', len(group_df))

      if not percentiles_df.empty:
         st.metric(
            'Metrics ranked',
            percentiles_df['metric'].nunique()
         )

   st.divider()
   st.subheader('Side-by-side comparison')
   render_kpi_table(group_df, benchmark_company)


main()
