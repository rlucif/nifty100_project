import pandas as pd

# First Validation Function
def check_required_columns(df, required_columns):
   missing = [col for col in required_columns if col not in df.columns]
   if missing:
      return [{
         'field': ','.join(missing),
         'issue': 'Missing required columns',
         'severity': 'CRITICAL'
      }]
   
   return []

# Duplicate Column Validator
def check_duplicate_columns(df):
   duplicates = df.columns[df.columns.duplicated()].tolist()
   if duplicates:
      return [{
         'field': ','.join(duplicates),
         'issue': 'Duplicate column names',
         'severity': 'CRITICAL'
      }]

   return []

# Empty Row Validator
def check_empty_rows(df):
   empty_rows = df[df.isna().all(axis=1)]

   return [
      {
         'field': 'row',
         'issue': f'Empty row at index {idx}',
         'severity': 'WARNING'
      }
      for idx in empty_rows.index
   ]

# Duplicate records check
def check_duplicate_records(df):
   if "id" not in df.columns:
      return []

   duplicates = df.duplicated(
      subset=[c for c in df.columns if c != "id"],
      keep=False
   )

   failures = []

   for _, row in df[duplicates].iterrows():
      failures.append({
         "company_id": row.get("company_id"),
         "year": row.get("year"),
         "field": "record",
         "issue": "Duplicate record",
         "severity": "CRITICAL"
      })

   return failures

# Null company_id check
def check_null_company_id(df):
   if 'company_id' not in df.columns:
      return []

   failures = []
   null_rows = df[df['company_id'].isna()]

   for idx in null_rows.index:
      failures.append({
         'field': 'company_id',
         'issue': f'Null company_id at row {idx}',
         'severity': 'CRITICAL'
      })
   return failures

# Null Year check
def check_null_year(df):
   if 'year' not in df.columns:
      return []

   failures = []
   null_rows = df[df['year'].isna()]

   for idx in null_rows.index:
      failures.append({
         'field': 'year',
         'issue': f'Null year at row {idx}',
         'severity': 'CRITICAL'
      })
   return failures

# Uppercase Ticker validation
def check_company_id_uppercase(df):
   if 'company_id' not in df.columns:
      return []

   failures = []

   for idx, value in df['company_id'].items():
      if pd.notna(value):
         if value != str(value).upper():
               failures.append({
                  'field': 'company_id',
                  'issue': f'Ticker not uppercase at row {idx}',
                  'severity': 'WARNING'
               })
   return failures

# unexpected columns
def check_unexpected_columns(df, required_columns):
   extra = [col for col in df.columns if col not in required_columns]
   if extra:
      return [{
         "field": ",".join(extra),
         "issue": "Unexpected columns found",
         "severity": "WARNING"
      }]

   return []

# Main Validation Function
def validate_dataframe(df, required_columns):
   failures = []
   failures.extend(check_required_columns(df, required_columns))
   failures.extend(check_duplicate_columns(df))
   failures.extend(check_empty_rows(df))
   failures.extend(check_duplicate_records(df))
   failures.extend(check_null_company_id(df))
   failures.extend(check_null_year(df))
   failures.extend(check_company_id_uppercase(df))
   failures.extend(check_unexpected_columns(df, required_columns))

   return failures

#CSV Export Function
def save_failures(failures, output_file):
   pd.DataFrame(failures).to_csv(output_file, index=False)