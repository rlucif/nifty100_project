'''
Run with:
   streamlit run src/dashboard/app.py
The app then serves on http://localhost:8501
'''

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
   sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st  # noqa: E402

from src.dashboard.utils.db import (  # noqa: E402
   database_is_available,
   get_companies,
   get_universe
)
from src.dashboard.utils.ui import simulated_note  # noqa: E402

st.set_page_config(
   page_title='Nifty 100 Analytics',
   page_icon='https://bluestock.in/static/assets/logo/dp.jpg',
   layout='wide',
   initial_sidebar_state='expanded'
)

SCREENS = [
   ('Home', 'Index level summary, sector mix and the top ranked companies'),
   ('Company Profile', 'One company in detail with ten years of history'),
   ('Screener', 'Filter the index on ten metrics or run a preset'),
   ('Peer Comparison', 'Rank a company against its peer group'),
   ('Trend Analysis', 'Track up to three metrics over ten years'),
   ('Sector Analysis', 'Compare revenue, returns and scale within a sector'),
   ('Capital Allocation', 'How each company deploys its cash flow'),
   ('Annual Reports', 'Links to published annual reports')
]


def main():
   st.title('Nifty 100 Financial Intelligence Platform')
   st.caption(
      'Fundamental analytics for the Nifty 100 constituents present in '
      'the supplied datasets.'
   )

   if not database_is_available():
      st.error(
         'data/nifty100.db was not found. Run `make load` and '
         '`make ratios` before starting the dashboard.'
      )
      st.stop()

   companies_df = get_companies()
   universe_df = get_universe()
   summary_columns = st.columns(4)
   summary_columns[0].metric('Companies', f'{len(universe_df)}')
   summary_columns[1].metric(
      'Sectors',
      f'{companies_df["broad_sector"].nunique()}'
   )
   summary_columns[2].metric(
      'Latest period',
      max(universe_df['year'], key=str)
   )
   summary_columns[3].metric('Screens', f'{len(SCREENS)}')

   st.divider()
   st.subheader('Screens')
   st.write(
      'Pick a screen from the sidebar. Each one reads the same cached '
      'database layer, so switching between them is instant.'
   )

   left_column, right_column = st.columns(2)

   for index, (name, description) in enumerate(SCREENS):
      target = left_column if index % 2 == 0 else right_column
      target.markdown(f'**{index + 1}. {name}**  \n{description}')

   st.divider()
   simulated_note()


main()
