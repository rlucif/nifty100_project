import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
   sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402
from plotly.subplots import make_subplots  # noqa: E402

from src.analytics.periods import (  # noqa: E402
   add_period_columns,
   deduplicate_company_years
)
from src.analytics.ratios import calculate_roce  # noqa: E402
from src.dashboard.utils.db import (  # noqa: E402
   get_bs,
   get_companies,
   get_pl,
   get_pros_and_cons,
   get_universe
)
from src.dashboard.utils.ui import (  # noqa: E402
   ACCENT_COLOUR,
   POSITIVE_COLOUR,
   PRIMARY_COLOUR,
   company_selector,
   format_metric,
   kpi_row,
   page_header
)

st.set_page_config(page_title='Company Profile | Nifty 100', layout='wide')

HISTORY_YEARS = 10


def build_history(ticker):
   # Ten most recent full financial years of statement data, with ROCE recomputed because Sprint 2 never persisted it.
   profit_df = deduplicate_company_years(get_pl(ticker))
   balance_df = deduplicate_company_years(get_bs(ticker))

   if profit_df.empty:
      return pd.DataFrame()

   history = profit_df.merge(balance_df, on=['company_id', 'year'], how='left')
   history = add_period_columns(history)
   history = history[history['period_sort_key'] > 0]
   history = history.sort_values('period_sort_key').tail(HISTORY_YEARS)

   if history.empty:
      return history

   history['return_on_equity_pct'] = [
      (net_profit / (equity + reserves) * 100)
      if pd.notna(net_profit) and pd.notna(equity) and pd.notna(reserves)
      and (equity + reserves) > 0
      else None
      for net_profit, equity, reserves in zip(
         history['net_profit'],
         history['equity_capital'],
         history['reserves']
      )
   ]

   # calculate_roce returns None if any input is missing, which is the normal case for banks: they report no operating profit.
   history['return_on_capital_employed_pct'] = [
      calculate_roce(
         operating_profit, other_income, equity, reserves, borrowings
      )
      for operating_profit, other_income, equity, reserves, borrowings in zip(
         history['operating_profit'],
         history['other_income'],
         history['equity_capital'],
         history['reserves'],
         history['borrowings']
      )
   ]

   return history


def render_company_card(company, universe_row):
   st.subheader(company['company_name'])

   detail_columns = st.columns(4)
   detail_columns[0].markdown(
      f'**Sector**  \n{company.get("broad_sector") or "Unclassified"}'
   )
   detail_columns[1].markdown(
      f'**Sub-sector**  \n{company.get("sub_sector") or "N/A"}'
   )
   detail_columns[2].markdown(f'**NSE ticker**  \n{company["company_id"]}')
   detail_columns[3].markdown(
      f'**Latest period**  \n'
      f'{universe_row["year"] if universe_row is not None else "N/A"}'
   )

   about = company.get('about_company')
   if isinstance(about, str) and about.strip():
      with st.expander('About the company', expanded=False):
         st.write(about)


def render_kpis(universe_row):
   if universe_row is None:
      st.warning('No computed ratios are available for this company.')
      return

   kpi_row([
      ('ROE', format_metric(universe_row['return_on_equity_pct'], '%')),
      ('ROCE', format_metric(
         universe_row['return_on_capital_employed_pct'], '%'
      )),
      ('Net profit margin', format_metric(
         universe_row['net_profit_margin_pct'], '%'
      )),
      ('Debt / Equity', format_metric(universe_row['debt_to_equity'])),
      ('Revenue CAGR 5y', format_metric(
         universe_row['revenue_cagr_5yr'], '%'
      )),
      ('Free cash flow', format_metric(
         universe_row['free_cash_flow_cr'], ' Cr'
      ))
   ])


def render_revenue_profit_chart(history):
   figure = go.Figure()

   figure.add_bar(
      x=history['year'],
      y=history['sales'],
      name='Revenue',
      marker_color=PRIMARY_COLOUR
   )
   figure.add_bar(
      x=history['year'],
      y=history['net_profit'],
      name='Net profit',
      marker_color=POSITIVE_COLOUR
   )

   figure.update_layout(
      barmode='group',
      height=380,
      margin={'t': 30, 'b': 10, 'l': 10, 'r': 10},
      yaxis_title='INR Crore',
      legend={'orientation': 'h', 'y': 1.12, 'x': 0}
   )

   st.plotly_chart(figure, width='stretch')


def render_returns_chart(history):
   figure = make_subplots(specs=[[{'secondary_y': True}]])

   figure.add_trace(
      go.Scatter(
         x=history['year'],
         y=history['return_on_equity_pct'],
         name='ROE %',
         mode='lines+markers',
         line={'color': PRIMARY_COLOUR, 'width': 2.5}
      ),
      secondary_y=False
   )
   figure.add_trace(
      go.Scatter(
         x=history['year'],
         y=history['return_on_capital_employed_pct'],
         name='ROCE %',
         mode='lines+markers',
         line={'color': ACCENT_COLOUR, 'width': 2.5, 'dash': 'dash'}
      ),
      secondary_y=True
   )

   figure.update_yaxes(title_text='ROE %', secondary_y=False)
   figure.update_yaxes(title_text='ROCE %', secondary_y=True)
   figure.update_layout(
      height=380,
      margin={'t': 30, 'b': 10, 'l': 10, 'r': 10},
      legend={'orientation': 'h', 'y': 1.12, 'x': 0}
   )

   st.plotly_chart(figure, width='stretch')


def render_pros_and_cons(ticker):
   records = get_pros_and_cons(ticker)

   if records.empty:
      st.info(
         'No analyst pros and cons were supplied for this company. '
         'The source dataset covers 16 of the 92 companies.'
      )
      return

   pros_column, cons_column = st.columns(2)

   def split_items(raw):
      if not isinstance(raw, str):
         return []

      return [item.strip() for item in raw.split('\n') if item.strip()]

   with pros_column:
      st.markdown('**Pros**')
      pros = split_items(records.iloc[0].get('pros'))
      if not pros:
         st.caption('None recorded.')
      for item in pros:
         st.markdown(
            f'<span style="color:{POSITIVE_COLOUR}">&#10004;</span> '
            f'{item}',
            unsafe_allow_html=True
         )

   with cons_column:
      st.markdown('**Cons**')
      cons = split_items(records.iloc[0].get('cons'))
      if not cons:
         st.caption('None recorded.')
      for item in cons:
         st.markdown(
            f'<span style="color:{ACCENT_COLOUR}">&#10008;</span> {item}',
            unsafe_allow_html=True
         )


def main():
   page_header(
      'Company Profile',
      'Search for a company by name or ticker.'
   )

   companies_df = get_companies()
   universe_df = get_universe()

   ticker = company_selector(companies_df, key='profile_search')

   if not ticker:
      st.info('Start typing a company name or ticker above.')
      return

   matches = companies_df[companies_df['company_id'] == ticker]

   if matches.empty:
      st.error('Ticker not found - please try another.')
      return

   company = matches.iloc[0].to_dict()

   universe_matches = universe_df[universe_df['company_id'] == ticker]
   universe_row = (
      universe_matches.iloc[0] if not universe_matches.empty else None
   )

   render_company_card(company, universe_row)
   st.divider()
   render_kpis(universe_row)
   st.divider()

   history = build_history(ticker)

   if history.empty:
      st.warning(
         'No financial statement history is available for this company.'
      )
      return

   if len(history) < HISTORY_YEARS:
      st.caption(
         f'Only {len(history)} years of data are available for this '
         'company. Charts show the full available history.'
      )

   left_column, right_column = st.columns(2)

   with left_column:
      st.subheader('Revenue and net profit')
      render_revenue_profit_chart(history)

   with right_column:
      st.subheader('Returns over time')
      render_returns_chart(history)

   st.divider()
   st.subheader('Analyst pros and cons')
   render_pros_and_cons(ticker)


main()
