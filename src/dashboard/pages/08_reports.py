import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
   sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st  # noqa: E402
from src.dashboard.utils.db import get_companies, get_documents  # noqa: E402
from src.dashboard.utils.ui import (  # noqa: E402
   ACCENT_COLOUR,
   company_selector,
   page_header
)

st.set_page_config(page_title='Annual Reports | Nifty 100', layout='wide')
REQUEST_TIMEOUT_SECONDS = 6

UNAVAILABLE_BADGE = (
   f'<span style="background-color:{ACCENT_COLOUR};color:#FFFFFF;'
   'padding:2px 8px;border-radius:4px;font-size:0.8em;">'
   'Report unavailable</span>'
)


def is_usable_url(url):
   if not isinstance(url, str):
      return False

   return url.strip().lower().startswith(('http://', 'https://'))


@st.cache_data(ttl=3600, show_spinner=False)
def check_url(url):
   try:
      import requests
   except ImportError:
      return None

   try:
      response = requests.head(
         url,
         timeout=REQUEST_TIMEOUT_SECONDS,
         allow_redirects=True
      )

      # Some BSE endpoints reject HEAD but serve GET.
      if response.status_code >= 400:
         response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT_SECONDS,
            stream=True,
            allow_redirects=True
         )
         response.close()

      return response.status_code < 400
   except Exception:
      return None


def render_report_row(year, url, verified_status):
   year_column, link_column = st.columns([1, 5])
   year_column.markdown(f'**{year}**')
   if not is_usable_url(url):
      link_column.markdown(UNAVAILABLE_BADGE, unsafe_allow_html=True)
      return

   if verified_status is False:
      link_column.markdown(
         f'{UNAVAILABLE_BADGE} '
         f'<span style="font-size:0.85em;">{url}</span>',
         unsafe_allow_html=True
      )
      return

   suffix = ''
   if verified_status is True:
      suffix = ' &nbsp;<span style="color:#2E7D32;">&#10004; link OK</span>'
   elif verified_status is None:
      suffix = ''

   link_column.markdown(
      f'[Annual Report {year} (PDF)]({url}){suffix}',
      unsafe_allow_html=True
   )


def main():
   page_header(
      'Annual Reports',
      'Published annual reports filed with BSE.'
   )

   companies_df = get_companies()
   ticker = company_selector(companies_df, key='reports_search')

   if not ticker:
      st.info('Select a company to see its filed reports.')
      return

   documents_df = get_documents(ticker)

   if documents_df.empty:
      st.warning(
         f'No annual reports are recorded for {ticker} in the supplied '
         'documents dataset.'
      )
      return

   documents_df = documents_df.copy()
   documents_df['Year'] = documents_df['Year'].astype(str)
   documents_df = documents_df.sort_values('Year', ascending=False)
   usable = documents_df['Annual_Report'].map(is_usable_url)
   summary_columns = st.columns(3)
   summary_columns[0].metric('Reports listed', len(documents_df))
   summary_columns[1].metric('With a link', int(usable.sum()))
   summary_columns[2].metric('Missing a link', int((~usable).sum()))

   verify = st.checkbox(
      'Verify links against bseindia.com',
      value=False,
      help='Sends one request per report. Adds a few seconds.'
   )

   statuses = {}
   if verify:
      progress = st.progress(0.0, text='Checking links...')
      rows = list(documents_df.itertuples())

      for index, row in enumerate(rows, start=1):
         url = row.Annual_Report
         statuses[row.Year] = (
            check_url(url) if is_usable_url(url) else False
         )
         progress.progress(index / len(rows), text=f'Checked {index} of {len(rows)}')

      progress.empty()

      unreachable = sum(1 for value in statuses.values() if value is False)
      unknown = sum(1 for value in statuses.values() if value is None)

      if unknown:
         st.caption(
            f'{unknown} link(s) could not be checked, most likely because '
            'this machine has no outbound network access. They are shown '
            'as normal links.'
         )
      st.caption(f'{unreachable} link(s) returned an error.')

   st.divider()

   for row in documents_df.itertuples():
      render_report_row(
         row.Year,
         row.Annual_Report,
         statuses.get(row.Year)
      )

   st.divider()
   with st.expander('Raw document records'):
      st.dataframe(
         documents_df[['Year', 'Annual_Report']],
         hide_index=True,
         width='stretch'
      )


main()
