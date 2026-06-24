import pandas as pd
from src.etl.validator import (
    check_required_columns,
    check_null_company_id,
    check_null_year,
    check_company_id_uppercase
)


def test_required_columns():
   df = pd.DataFrame({'company_id': ['ABC']})
   failures = check_required_columns(df, ['company_id', 'year'])
   assert len(failures) == 1

# Null Company ID
def test_null_company_id():
   df = pd.DataFrame({'company_id': [None]})
   failures = check_null_company_id(df)
   assert len(failures) == 1

# Null year
def test_null_year():
   df = pd.DataFrame({'year': [None]})
   failures = check_null_year(df)
   assert len(failures) == 1

# lowercase Ticker
def test_company_id_uppercase():
   df = pd.DataFrame({'company_id': ['tcs']})
   failures = check_company_id_uppercase(df)
   assert len(failures) == 1