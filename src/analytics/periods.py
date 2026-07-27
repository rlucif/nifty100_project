'''
Period handling for the N100 Financial Intelligence Platform.

The supplied datasets label every financial year with a text period such as
'Mar 2024' or 'Dec 2023'. Companies do not share a common financial year end,
and the raw Excel files also contain irregular labels ('TTM',
'Mar 2023 15', 'Mar 2016 9m').

This module converts those labels into a sortable key and a fiscal year
integer so that CAGR windows, latest-year selection and the market_cap join
all agree on what "the latest year" means.
'''

import logging
import re

logger = logging.getLogger(__name__)

MONTH_NUMBERS = {
   'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
   'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
}

# 'Mar 2024' with optional trailing noise such as ' 15' or ' 9m'.
PERIOD_PATTERN = re.compile(
   r'^\s*([A-Za-z]{3})[a-z]*\s+(\d{4})\b',
   re.IGNORECASE
)


def parse_period(year_label):
   # Return (month, calendar_year) for a period label, or (None, None).
   if year_label is None:
      return None, None

   match = PERIOD_PATTERN.match(str(year_label))
   if not match:
      logger.debug('Unparseable period label: %s', year_label)
      return None, None

   month = MONTH_NUMBERS.get(match.group(1).lower())
   if month is None:
      return None, None

   return month, int(match.group(2))


def period_sort_key(year_label):
   # Sortable integer for a period label. Unparseable labels sort first.
   month, calendar_year = parse_period(year_label)
   if month is None:
      return -1

   return calendar_year * 100 + month


def fiscal_year(year_label):
   # Calendar year a financial period closes in, used to join the
   # market_cap table whose year column is a plain integer.
   # 'Mar 2024' and 'Dec 2024' both map to 2024.
   month, calendar_year = parse_period(year_label)
   if month is None:
      return None

   return calendar_year


def is_full_year(year_label):
   # Reject TTM and part-year labels such as 'Mar 2016 9m'.
   if year_label is None:
      return False

   text = str(year_label).strip()
   if not PERIOD_PATTERN.match(text):
      return False

   return not text.lower().endswith('m')


def add_period_columns(dataframe, year_column='year'):
   # Attach period_sort_key and fiscal_year columns to a dataframe.
   result = dataframe.copy()
   result['period_sort_key'] = result[year_column].map(period_sort_key)
   result['fiscal_year'] = result[year_column].map(fiscal_year)

   return result


def latest_rows(dataframe, year_column='year', group_column='company_id'):
   # One row per company: the most recent parseable period.
   # Source duplicates (identical company-year rows produced by the
   # Sprint 2 join fan-out) are collapsed to the first occurrence.
   working = add_period_columns(dataframe, year_column)
   working = working[working['period_sort_key'] > 0]

   working = working.sort_values(
      [group_column, 'period_sort_key'],
      ascending=[True, False]
   )

   return working.drop_duplicates(subset=[group_column], keep='first')


def deduplicate_company_years(
   dataframe,
   year_column='year',
   group_column='company_id'):
   # Collapse duplicate company-year rows to a single record.
   # Sprint 2 deliberately preserved source duplicates in financial_ratios;
   # analytics built on top of that table must not count a company twice.
   return dataframe.drop_duplicates(
      subset=[group_column, year_column],
      keep='first'
   )
