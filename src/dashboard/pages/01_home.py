import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
   sys.path.insert(0, str(PROJECT_ROOT))

import plotly.express as px  # noqa: E402
import streamlit as st  # noqa: E402

from src.dashboard.utils.db import get_universe, get_valuation  # noqa: E402
from src.dashboard.utils.ui import (  # noqa: E402
   format_metric,
   kpi_row,
   page_header,
   simulated_note
)

st.set_page_config(page_title='Home | Nifty 100', layout='wide')

AVAILABLE_YEARS = [2024, 2023, 2022, 2021, 2020, 2019]
DEBT_FREE_THRESHOLD = 0.05


def build_year_view(universe_df, valuation_df, selected_year):
   # The ratio columns are fixed at each company's latest financial year, but the valuation multiples exist for every year from 2019 to 2024.
   # Selecting a year re-points the valuation side of the view.
   year_valuation = valuation_df[valuation_df['year'] == selected_year]

   ratio_columns = [
      'company_id',
      'company_name',
      'broad_sector',
      'year',
      'return_on_equity_pct',
      'debt_to_equity',
      'revenue_cagr_5yr',
      'composite_quality_score'
   ]

   view = universe_df[ratio_columns].merge(
      year_valuation[[
         'company_id',
         'pe_ratio',
         'pb_ratio',
         'dividend_yield_pct',
         'market_cap_crore'
      ]],
      on='company_id',
      how='left'
   )

   return view


def main():
   page_header(
      'Index Overview',
      'Summary metrics across every company in the supplied datasets.'
   )

   universe_df = get_universe()
   valuation_df = get_valuation()

   selected_year = st.sidebar.selectbox(
      'Valuation year',
      AVAILABLE_YEARS,
      index=0,
      help='Changes the valuation multiples used by the tiles below.'
   )

   view = build_year_view(universe_df, valuation_df, selected_year)

   debt_free_count = int(
      (view['debt_to_equity'] < DEBT_FREE_THRESHOLD).sum()
   )

   median_roe = view['return_on_equity_pct'].median()

   kpi_row([
      ('Average ROE', format_metric(
         view['return_on_equity_pct'].mean(), '%'
      ), (
         'Mean ROE across the index. A handful of companies carry '
         'equity figures that are not on the same scale as their '
         'profits, which inflates this average. The median is '
         f'{format_metric(median_roe, "%")}. See '
         'output/ratio_edge_cases.log.'
      )),
      ('Median P/E', format_metric(view['pe_ratio'].median())),
      ('Median D/E', format_metric(view['debt_to_equity'].median())),
      ('Total companies', f'{len(view)}'),
      ('Median Revenue CAGR 5y', format_metric(
         view['revenue_cagr_5yr'].median(), '%'
      )),
      ('Debt-free companies', f'{debt_free_count}')
   ])

   st.caption(
      f'Valuation tiles reflect {selected_year}. '
      f'Debt free is defined as D/E below {DEBT_FREE_THRESHOLD}.'
   )

   st.divider()

   left_column, right_column = st.columns([1, 1])

   with left_column:
      st.subheader('Sector breakdown')

      sector_counts = (
         view['broad_sector']
         .fillna('Unclassified')
         .value_counts()
         .rename_axis('Sector')
         .reset_index(name='Companies')
      )

      donut = px.pie(
         sector_counts,
         names='Sector',
         values='Companies',
         hole=0.55
      )
      donut.update_traces(
         textposition='inside',
         textinfo='value+percent'
      )
      donut.update_layout(
         margin={'t': 10, 'b': 10, 'l': 10, 'r': 10},
         legend={'orientation': 'v', 'x': 1.0, 'y': 0.5}
      )

      st.plotly_chart(donut, width='stretch')
      st.caption(
         f'{sector_counts["Sector"].nunique()} sectors. Companies with no '
         'master record appear as Unclassified.'
      )

   with right_column:
      st.subheader('Top 5 by composite quality score')

      top_five = (
         view.sort_values('composite_quality_score', ascending=False)
         .head(5)[[
            'company_id',
            'company_name',
            'broad_sector',
            'composite_quality_score',
            'return_on_equity_pct',
            'debt_to_equity'
         ]]
         .rename(columns={
            'company_id': 'Ticker',
            'company_name': 'Company',
            'broad_sector': 'Sector',
            'composite_quality_score': 'Score',
            'return_on_equity_pct': 'ROE %',
            'debt_to_equity': 'D/E'
         })
      )

      st.dataframe(
         top_five.round(2),
         hide_index=True,
         width='stretch'
      )

      st.caption(
         'Composite score blends profitability, cash quality, growth and '
         'leverage, winsorised at the 10th and 90th percentile.'
      )

   st.divider()

   st.subheader('Sector medians')

   sector_medians = (
      view.groupby(view['broad_sector'].fillna('Unclassified'))
      .agg(
         Companies=('company_id', 'count'),
         Median_ROE=('return_on_equity_pct', 'median'),
         Median_DE=('debt_to_equity', 'median'),
         Median_PE=('pe_ratio', 'median'),
         Median_Score=('composite_quality_score', 'median')
      )
      .round(2)
      .reset_index()
      .rename(columns={
         'broad_sector': 'Sector',
         'Median_ROE': 'Median ROE %',
         'Median_DE': 'Median D/E',
         'Median_PE': 'Median P/E',
         'Median_Score': 'Median Score'
      })
      .sort_values('Companies', ascending=False)
   )

   st.dataframe(sector_medians, hide_index=True, width='stretch')
   simulated_note()


main()
