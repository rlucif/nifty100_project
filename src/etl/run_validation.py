from pathlib import Path
import pandas as pd
from validator import validate_dataframe, save_failures
from schemas import EXPECTED_SCHEMAS


DATA_DIR = Path('data/raw')
FILES = [
   'companies.xlsx',
   'balancesheet.xlsx',
   'cashflow.xlsx',
   'profitandloss.xlsx',
   'analysis.xlsx',
   'documents.xlsx',
   'prosandcons.xlsx',
]

all_failures = []

# Validation logic
for file_name in FILES:
   file_path = DATA_DIR / file_name
   print(f'Validating {file_name}')

   df = pd.read_excel(file_path, header=1)

   failures = validate_dataframe(
      df,
      required_columns = EXPECTED_SCHEMAS[file_name]
   )
   for failure in failures:
      failure['source_file'] = file_name

   all_failures.extend(failures)

# Export Report
save_failures(all_failures, 'validation_failures.csv')
print(
   f'Validation complete '
   f'{len(all_failures)} issues found'
)