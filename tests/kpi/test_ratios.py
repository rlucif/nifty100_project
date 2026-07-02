import pytest
from src.analytics.ratios import (
   calculate_net_profit_margin,
   calculate_operating_profit_margin,
   calculate_roe,
   calculate_roce,
   calculate_debt_to_equity,
   calculate_high_leverage_flag,
   calculate_interest_coverage,
   calculate_icr_label,
   calculate_icr_warning_flag,
   calculate_net_debt,
   calculate_asset_turnover
)


@pytest.mark.parametrize(
'net_profit, sales, expected',[
      (20, 100, 20.0),
      (-10, 100, -10.0),
      (50, 0, None),
   ]
)
def test_calculate_net_profit_margin(net_profit, sales, expected):
   assert calculate_net_profit_margin(net_profit, sales) == expected


@pytest.mark.parametrize(
   'operating_profit, sales, source_opm, expected',[
      (25, 100, 25.0, 25.0),
      (30, 120, 25.0, 25.0),
      (50, 0, None, None),
   ]
)
def test_calculate_operating_profit_margin(operating_profit, sales, source_opm, expected):
   assert calculate_operating_profit_margin(
      operating_profit,
      sales,
      source_opm
   ) == expected


@pytest.mark.parametrize(
   'net_profit, equity_capital, reserves, expected',[
      (20, 50, 50, 20.0),
      (10, -20, 10, None),
      (10, 0, 0, None),
   ]
)
def test_calculate_roe(net_profit, equity_capital, reserves, expected):
   assert calculate_roe(
      net_profit,
      equity_capital,
      reserves
   ) == expected


@pytest.mark.parametrize(
   'operating_profit, other_income, equity_capital, reserves, borrowings, expected',[
      (80, 20, 50, 30, 20, 100.0),
      (60, 4, 20, 20, 24, 100.0),
      (10, 2, 0, 0, 0, None),
   ]
)
def test_calculate_roce(
   operating_profit,
   other_income,
   equity_capital,
   reserves,
   borrowings,
   expected
):
   assert calculate_roce(
      operating_profit,
      other_income,
      equity_capital,
      reserves,
      borrowings
   ) == expected


@pytest.mark.parametrize(
   'borrowings, equity_capital, reserves, expected',[
      (100, 50, 50, 1.0),
      (0, 50, 50, 0),
      (100, -50, 0, None),
   ]
)
def test_calculate_debt_to_equity(
   borrowings,
   equity_capital,
   reserves,
   expected
):
   assert calculate_debt_to_equity(
      borrowings,
      equity_capital,
      reserves
   ) == expected


@pytest.mark.parametrize(
   'debt_to_equity, sector, expected',[
      (6.2, 'Industrials', True),
      (6.2, 'Financials', False),
      (2.5, 'Industrials', False),
      (None, 'Industrials', False),
   ]
)
def test_calculate_high_leverage_flag(
   debt_to_equity,
   sector,
   expected
):
   assert calculate_high_leverage_flag(
      debt_to_equity,
      sector
   ) == expected


@pytest.mark.parametrize(
   'operating_profit, other_income, interest, expected',[
      (120, 30, 30, 5.0),
      (100, 0, 20, 5.0),
      (100, 10, 0, None),
   ]
)
def test_calculate_interest_coverage(
   operating_profit,
   other_income,
   interest,
   expected
):
   assert calculate_interest_coverage(
      operating_profit,
      other_income,
      interest
   ) == expected


@pytest.mark.parametrize(
   'interest_coverage, expected',[
      (None, 'Debt Free'),
      (4.8, None),
   ]
)
def test_calculate_icr_label(
   interest_coverage,
   expected
):
   assert calculate_icr_label(
      interest_coverage
   ) == expected


@pytest.mark.parametrize(
   'interest_coverage, expected',[
      (0.8, True),
      (1.4, True),
      (1.5, False),
      (3.2, False),
      (None, False),
   ]
)
def test_calculate_icr_warning_flag(
   interest_coverage,
   expected
):
   assert calculate_icr_warning_flag(
      interest_coverage
   ) == expected


@pytest.mark.parametrize(
   'borrowings, investments, expected',[
      (500, 150, 350),
      (200, 250, -50),
      (0, 100, -100),
   ]
)
def test_calculate_net_debt(
   borrowings,
   investments,
   expected
):
   assert calculate_net_debt(
      borrowings,
      investments
   ) == expected


@pytest.mark.parametrize(
   'sales, total_assets, expected',[
      (1000, 500, 2.0),
      (750, 300, 2.5),
      (1000, 0, None),
   ]
)
def test_calculate_asset_turnover(
   sales,
   total_assets,
   expected
):
   assert calculate_asset_turnover(
      sales,
      total_assets
   ) == expected