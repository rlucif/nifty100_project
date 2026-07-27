import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
   sys.path.insert(0, str(PROJECT_ROOT))

import plotly.express as px  # noqa: E402
import streamlit as st  # noqa: E402
from src.analytics.periods import latest_rows  # noqa: E402
from src.dashboard.utils.db import (  # noqa: E402
   get_capital_allocation,
   get_universe
)
from src.dashboard.utils.ui import page_header  # noqa: E402

st.set_page_config(page_title='Capital Allocation | Nifty 100', layout='wide')

PATTERN_MEANINGS = {
   'Reinvestor': 'Generates cash and ploughs it back into the business.',
   'Shareholder Returns':
      'Generates more cash than it books as profit and returns it.',
   'Liquidating Assets': 'Selling assets while repaying capital providers.',
   'Distress Signal':
      'Burning operating cash, selling assets and raising funding.',
   'Growth Funded by Debt':
      'Investing heavily while operations still consume cash.',
   'Cash Accumulator': 'Cash coming in from every activity.',
   'Pre-Revenue': 'Cash going out across every activity.',
   'Mixed': 'Generates cash, invests, and still raises funding.'
}

PATTERN_COLOURS = {
   'Reinvestor': '#1F3864',
   'Shareholder Returns': '#2E7D32',
   'Cash Accumulator': '#4472C4',
   'Growth Funded by Debt': '#ED7D31',
   'Mixed': '#7F7F7F',
   'Liquidating Assets': '#BF8F00',
   'Distress Signal': '#C00000',
   'Pre-Revenue': '#833C00'
}


def build_latest_patterns(universe_df):
   allocation_df = get_capital_allocation()

   if allocation_df.empty:
      return allocation_df

   latest = latest_rows(allocation_df)

   return latest.merge(
      universe_df[[
         'company_id',
         'company_name',
         'broad_sector',
         'free_cash_flow_cr',
         'composite_quality_score'
      ]],
      on='company_id',
      how='left'
   )


def main():
   page_header(
      'Capital Allocation Map',
      'How each company deploys the cash it generates.'
   )

   universe_df = get_universe()
   patterns_df = build_latest_patterns(universe_df)

   if patterns_df.empty:
      st.error(
         'output/capital_allocation.csv was not found. '
         'Run `make ratios` to generate it.'
      )
      return

   patterns_df['pattern_label'] = patterns_df['pattern_label'].fillna('Unknown Pattern')
   patterns_df['company_name'] = patterns_df['company_name'].fillna(patterns_df['company_id'])

   counts = (
      patterns_df['pattern_label']
      .value_counts()
      .rename_axis('Pattern')
      .reset_index(name='Companies')
   )

   st.subheader('Pattern distribution')

   treemap = px.treemap(
      patterns_df,
      path=['pattern_label', 'company_name'],
      values=None,
      color='pattern_label',
      color_discrete_map=PATTERN_COLOURS,
      hover_data={'company_id': True, 'broad_sector': True}
   )
   treemap.update_layout(
      height=560,
      margin={'t': 30, 'b': 10, 'l': 10, 'r': 10}
   )
   treemap.update_traces(root_color='#F2F2F2')

   st.plotly_chart(treemap, width='stretch')
   st.caption(
      'Each tile is a company sized equally within its pattern. '
      'Patterns come from the signs of operating, investing and '
      'financing cash flow in the latest year.'
   )

   st.divider()

   left_column, right_column = st.columns([1, 2])

   with left_column:
      st.subheader('Patterns')
      st.dataframe(counts, hide_index=True, width='stretch')

   with right_column:
      st.subheader('Companies in a pattern')

      selected_pattern = st.selectbox(
         'Pattern',
         counts['Pattern'].tolist()
      )

      st.info(
         PATTERN_MEANINGS.get(
            selected_pattern,
            'Sign combination not covered by the eight standard patterns.'
         )
      )

      members = patterns_df[
         patterns_df['pattern_label'] == selected_pattern
      ][[
         'company_id',
         'company_name',
         'broad_sector',
         'year',
         'cfo_sign',
         'cfi_sign',
         'cff_sign',
         'free_cash_flow_cr',
         'composite_quality_score'
      ]].rename(columns={
         'company_id': 'Ticker',
         'company_name': 'Company',
         'broad_sector': 'Sector',
         'year': 'Period',
         'cfo_sign': 'CFO',
         'cfi_sign': 'CFI',
         'cff_sign': 'CFF',
         'free_cash_flow_cr': 'FCF (Cr)',
         'composite_quality_score': 'Score'
      })

      st.dataframe(
         members.round(2),
         hide_index=True,
         width='stretch'
      )


main()
