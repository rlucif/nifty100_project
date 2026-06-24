import pytest
from src.etl.loader import normalize_ticker, normalize_year


@pytest.mark.parametrize(
   'input_value, expected',[
      ('infy', 'INFY'),
      ('tcs', 'TCS'),
      ('  tcs  ', 'TCS'),
      ('HiNdUnIlVr', 'HINDUNILVR'),
      ('reliance', 'RELIANCE'),
      ('SBIN', 'SBIN'),
      (' axisbank ', 'AXISBANK'),
      ('itc', 'ITC'),
      ('nestleind', 'NESTLEIND'),
      ('maruti', 'MARUTI'),
      ('bajajfinserv', 'BAJAJFINSERV'),
      ('asianpaints', 'ASIANPAINTS'),
      ('ultracemco', 'ULTRACEMCO'),
      ('wipro', 'WIPRO'),
      ('techm', 'TECHM'),
      ('hcltech', 'HCLTECH'),
      ('sunpharma', 'SUNPHARMA'),
      ('tatamotors', 'TATAMOTORS'),
      ('', ''),
      (None, None),
   ]
)
def test_normalize_ticker(input_value, expected):
   assert normalize_ticker(input_value) == expected


@pytest.mark.parametrize(
   'input_value, expected',[
      ('Mar-23', '2023-03'),
      ('Mar-24', '2024-03'),
      ('Mar-25', '2025-03'),
      ('Mar-22', '2022-03'),
      ('Mar-21', '2021-03'),
      ('Mar-20', '2020-03'),
      ('Mar-19', '2019-03'),
      ('Mar-18', '2018-03'),
      ('Mar-17', '2017-03'),
      ('Mar-16', '2016-03'),
      ('Dec-23', '2023-12'),
      ('Dec-22', '2022-12'),
      ('Dec-21', '2021-12'),
      ('Dec-20', '2020-12'),
      ('Dec-19', '2019-12'),
      ('Dec-18', '2018-12'),
      ('ABC-23', 'ABC-23'),
      ('2023', '2023'),
      ('', ''),
      (None, None),
   ]
)
def test_normalize_year(input_value, expected):
   assert normalize_year(input_value) == expected