import re
from pathlib import Path
import pytest

from src.analytics.cashflow_kpis import (
   calculate_deleveraging_flag,
   calculate_distress_flag
)

DB_PATH = Path('data/nifty100.db')

MINIMUM_TEARSHEET_KB = 30
EXPECTED_PAGES = 2


# Distress and deleveraging flags
def test_distress_flag_fires_on_negative_cfo_with_positive_cff():
   assert calculate_distress_flag(-3713, 2656) is True


def test_distress_flag_ignores_healthy_operating_cash_flow():
   assert calculate_distress_flag(5000, 2000) is False


def test_distress_flag_ignores_negative_cfo_without_financing_inflow():
   assert calculate_distress_flag(-3713, -500) is False


def test_distress_flag_is_none_safe():
   assert calculate_distress_flag(None, 100) is False
   assert calculate_distress_flag(-100, None) is False
   assert calculate_distress_flag(float('nan'), 100) is False


def test_deleveraging_flag_requires_borrowings_to_actually_fall():
   assert calculate_deleveraging_flag(-500, 900, 1000) is True
   assert calculate_deleveraging_flag(-500, 1100, 1000) is False


def test_deleveraging_flag_requires_financing_outflow():
   # Borrowings fell but financing was an inflow: not deleveraging.
   assert calculate_deleveraging_flag(500, 900, 1000) is False


def test_deleveraging_flag_is_none_safe():
   assert calculate_deleveraging_flag(-500, None, 1000) is False
   assert calculate_deleveraging_flag(None, 900, 1000) is False


# PDF generation
def _count_pages(path):
   data = Path(path).read_bytes()

   return len(re.findall(rb'/Type\s*/Page[^s]', data))


@pytest.fixture(scope='module')
def generated_tearsheet(tmp_path_factory):
   if not DB_PATH.exists():
      pytest.skip('data/nifty100.db is not present')

   from src.reports.tearsheet import generate_tearsheets

   output_dir = tmp_path_factory.mktemp('tearsheets')
   generated_df, _skipped_df = generate_tearsheets(
      ['TCS'], output_dir=str(output_dir)
   )

   if generated_df.empty:
      pytest.skip('TCS has no financial history in this database')

   return Path(generated_df.iloc[0]['path'])


def test_tearsheet_is_created(generated_tearsheet):
   assert generated_tearsheet.exists()


def test_tearsheet_meets_the_size_floor(generated_tearsheet):
   size_kb = generated_tearsheet.stat().st_size / 1024

   assert size_kb >= MINIMUM_TEARSHEET_KB


def test_tearsheet_is_exactly_two_pages(generated_tearsheet):
   # A third page would mean content overflowed its frame.
   assert _count_pages(generated_tearsheet) == EXPECTED_PAGES


def test_tearsheet_skips_a_company_with_too_little_history():
   if not DB_PATH.exists():
      pytest.skip('data/nifty100.db is not present')

   from src.reports.tearsheet import generate_tearsheets

   # JIOFIN carries 2 years of data, below the 3 year floor.
   generated_df, skipped_df = generate_tearsheets(
      ['JIOFIN'], output_dir='reports/tearsheets'
   )

   assert generated_df.empty
   assert len(skipped_df) == 1
   assert skipped_df.iloc[0]['company_id'] == 'JIOFIN'
