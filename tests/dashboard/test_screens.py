import warnings
from pathlib import Path
import pytest

warnings.filterwarnings('ignore')

DB_PATH = Path('data/nifty100.db')
PAGES_DIR = Path('src/dashboard/pages')

SCREENS = [
   '01_home.py',
   '02_profile.py',
   '03_screener.py',
   '04_peers.py',
   '05_trends.py',
   '06_sectors.py',
   '07_capital.py',
   '08_reports.py'
]

# Companies that have previously exposed a rendering bug.
#   PNB        reports no operating profit, so ROCE is not computable
#   ADANIGREEN fewer than ten years of history
#   ITC        an ordinary company, as a control
REGRESSION_TICKERS = ['PNB', 'ADANIGREEN', 'ITC']
PAGE_LOAD_BUDGET_SECONDS = 3.0

pytest.importorskip('streamlit.testing.v1')


@pytest.fixture(scope='module')
def app_test():
   from streamlit.testing.v1 import AppTest

   return AppTest


def _require_database():
   if not DB_PATH.exists():
      pytest.skip('data/nifty100.db is not present')


@pytest.mark.parametrize('screen', SCREENS)
def test_screen_loads_without_error(app_test, screen):
   _require_database()

   result = app_test.from_file(str(PAGES_DIR / screen), default_timeout=180)
   result.run()

   assert not result.exception, (
      f'{screen} raised: '
      f'{result.exception[0].value if result.exception else ""}'
   )


def test_entry_point_loads(app_test):
   _require_database()

   result = app_test.from_file('src/dashboard/app.py', default_timeout=180)
   result.run()

   assert not result.exception


@pytest.mark.parametrize('ticker', REGRESSION_TICKERS)
def test_profile_renders_for_difficult_tickers(app_test, ticker):
   # PNB regression: calculate_roce used to raise TypeError because a bank reports no operating profit.
   _require_database()

   import sqlite3
   import pandas as pd

   connection = sqlite3.connect(DB_PATH)
   try:
      companies = pd.read_sql(
         'SELECT id, company_name FROM companies WHERE id = ?',
         connection,
         params=(ticker,)
      )
   finally:
      connection.close()

   if companies.empty:
      pytest.skip(f'{ticker} has no company master record')

   option = f'{companies.iloc[0]["company_name"]} ({ticker})'

   result = app_test.from_file(
      str(PAGES_DIR / '02_profile.py'),
      default_timeout=180
   )
   result.run()
   result.selectbox[0].set_value(option).run()

   assert not result.exception, (
      f'profile raised for {ticker}: '
      f'{result.exception[0].value if result.exception else ""}'
   )


def test_screener_survives_extreme_slider_values(app_test):
   _require_database()

   result = app_test.from_file(
      str(PAGES_DIR / '03_screener.py'),
      default_timeout=180
   )
   result.run()

   for slider in result.slider:
      slider.set_value(slider.max)

   result.run()

   assert not result.exception


def test_screener_presets_all_run(app_test):
   _require_database()

   from streamlit.testing.v1 import AppTest

   labels = [
      'Quality', 'Value', 'Growth', 'Dividend', 'Debt-Free', 'Turnaround'
   ]

   for label in labels:
      result = AppTest.from_file(
         str(PAGES_DIR / '03_screener.py'),
         default_timeout=180
      )
      result.run()

      buttons = [button for button in result.button if button.label == label]
      assert buttons, f'preset button {label} is missing'

      buttons[0].click().run()

      assert not result.exception, f'preset {label} raised'
