import pandas as pd
import streamlit as st

# Consistent palette across every screen and chart.
PRIMARY_COLOUR = '#1F3864'
ACCENT_COLOUR = '#C00000'
POSITIVE_COLOUR = '#2E7D32'

SIMULATED_CAPTION = (
   'P/E, P/B, EV/EBITDA, dividend yield and market cap are **SIMULATED** '
   'datasets supplied with the project. Treat them as illustrative.'
)

NOT_AVAILABLE = 'N/A'


def format_metric(value, suffix='', decimals=2):
   if value is None or pd.isna(value):
      return NOT_AVAILABLE

   try:
      return f'{float(value):,.{decimals}f}{suffix}'
   except (TypeError, ValueError):
      return NOT_AVAILABLE


def kpi_row(metrics, columns_per_row=6):
   columns = st.columns(min(len(metrics), columns_per_row))

   for column, metric in zip(columns, metrics):
      label, value = metric[0], metric[1]
      help_text = metric[2] if len(metric) > 2 else None

      column.metric(label, value, help=help_text)


def simulated_note():
   st.caption(SIMULATED_CAPTION)


def page_header(title, subtitle=None):
   st.title(title)

   if subtitle:
      st.caption(subtitle)


def empty_state(message):
   st.info(message)


def company_selector(companies_df, label='Search company name or ticker', key=None):
   options = [
      f'{row.company_name} ({row.company_id})'
      for row in companies_df.itertuples()
   ]

   if not options:
      return None

   selection = st.selectbox(label, options, key=key, index=0)

   if not selection:
      return None

   return selection.rsplit('(', 1)[-1].rstrip(')')


def dataframe_download_button(dataframe, filename, label='Download CSV'):
   csv_bytes = dataframe.to_csv(index=False).encode('utf-8')

   return st.download_button(
      label=label,
      data=csv_bytes,
      file_name=filename,
      mime='text/csv'
   )
