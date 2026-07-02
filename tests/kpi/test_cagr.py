import pytest

from src.analytics.cagr import (
   calculate_cagr,
   calculate_revenue_cagr,
   calculate_pat_cagr,
   calculate_eps_cagr
)


@pytest.mark.parametrize(
   'start_value, end_value, years, expected_value, expected_flag', [
      (100, 200, 3, 25.99210498948732, None),
      (100, -50, 3, None, 'DECLINE_TO_LOSS'),
      (-100, 50, 3, None, 'TURNAROUND'),
      (-100, -50, 3, None, 'BOTH_NEGATIVE'),
      (0, 50, 3, None, 'ZERO_BASE'),
      (100, 200, 0, None, None),
   ]
)
def test_calculate_cagr(
   start_value,
   end_value,
   years,
   expected_value,
   expected_flag
):
   value, flag = calculate_cagr(
      start_value,
      end_value,
      years
   )

   if expected_value is None:
      assert value is None
   else:
      assert value == pytest.approx(expected_value)

   assert flag == expected_flag


@pytest.mark.parametrize(
   'start_sales, end_sales, years', [
      (100, 200, 3),
      (200, 400, 5),
   ]
)
def test_calculate_revenue_cagr(
   start_sales,
   end_sales,
   years
):
   assert calculate_revenue_cagr(
      start_sales,
      end_sales,
      years
   ) == calculate_cagr(
      start_sales,
      end_sales,
      years
   )


@pytest.mark.parametrize(
   'start_pat, end_pat, years', [
      (100, 150, 3),
      (200, 500, 5),
   ]
)
def test_calculate_pat_cagr(
   start_pat,
   end_pat,
   years
):
   assert calculate_pat_cagr(
      start_pat,
      end_pat,
      years
   ) == calculate_cagr(
      start_pat,
      end_pat,
      years
   )


@pytest.mark.parametrize(
   'start_eps, end_eps, years', [
      (10, 20, 3),
      (15, 45, 5),
   ]
)
def test_calculate_eps_cagr(
   start_eps,
   end_eps,
   years
):
   assert calculate_eps_cagr(
      start_eps,
      end_eps,
      years
   ) == calculate_cagr(
      start_eps,
      end_eps,
      years
   )