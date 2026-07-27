import re
from pathlib import Path
import pandas as pd

from src.reports.sector_report import generate_sector_reports
from src.reports.tearsheet import MINIMUM_YEARS, generate_tearsheets

SKIPPED_PATH = 'output/skipped_tearsheets.csv'
TEARSHEET_DIR = 'reports/tearsheets'

MINIMUM_TEARSHEET_KB = 30
EXPECTED_PAGES = 2


def count_pdf_pages(path):
   data = Path(path).read_bytes()

   return len(re.findall(rb'/Type\s*/Page[^s]', data))


def verify_tearsheets(generated_df):
   checks = []

   for row in generated_df.itertuples():
      path = Path(row.path)
      pages = count_pdf_pages(path)

      checks.append({
         'company_id': row.company_id,
         'size_kb': row.size_kb,
         'pages': pages,
         'size_ok': row.size_kb >= MINIMUM_TEARSHEET_KB,
         'pages_ok': pages == EXPECTED_PAGES
      })

   return pd.DataFrame(checks)


def main():
   print('=' * 62)
   print('SPRINT 5 DAY 34 - BATCH REPORT GENERATION')
   print('=' * 62)

   print('\n[1/3] Generating company tearsheets')
   generated_df, skipped_df = generate_tearsheets()
   print(f'      generated {len(generated_df)}, skipped {len(skipped_df)}')

   skipped_path = Path(SKIPPED_PATH)
   skipped_path.parent.mkdir(parents=True, exist_ok=True)

   if skipped_df.empty:
      pd.DataFrame(
         columns=['company_id', 'reason', 'years_of_data']
      ).to_csv(skipped_path, index=False)
   else:
      skipped_df.to_csv(skipped_path, index=False)
      print(f'      skipped tickers logged to {skipped_path}')
      print(skipped_df.to_string(index=False))

   print('\n[2/3] Generating sector reports')
   sectors_df = generate_sector_reports()
   print(f'      generated {len(sectors_df)} sector PDFs')

   print('\n[3/3] Verifying output')
   checks_df = verify_tearsheets(generated_df)

   undersized = checks_df[~checks_df['size_ok']]
   wrong_pages = checks_df[~checks_df['pages_ok']]

   print('\n' + '=' * 62)
   print('SPRINT 5 EXIT CRITERIA')
   print('=' * 62)

   tearsheet_count = len(list(Path(TEARSHEET_DIR).glob('*_tearsheet.pdf')))
   expected_count = len(generated_df)

   print(
      f'  [{"PASS" if tearsheet_count == expected_count else "REVIEW":>6}] '
      f'Tearsheets on disk        {tearsheet_count} of {expected_count}'
   )
   print(
      f'  [{"PASS" if undersized.empty else "REVIEW":>6}] '
      f'All at least {MINIMUM_TEARSHEET_KB} KB       '
      f'{len(checks_df) - len(undersized)} of {len(checks_df)}'
   )
   print(
      f'  [{"PASS" if wrong_pages.empty else "REVIEW":>6}] '
      f'All exactly {EXPECTED_PAGES} pages       '
      f'{len(checks_df) - len(wrong_pages)} of {len(checks_df)}'
   )
   print(
      f'  [{"  INFO":>6}] Skipped under {MINIMUM_YEARS} years  '
      f'{len(skipped_df)}'
   )
   print(f'  [{"  INFO":>6}] Sector PDFs              {len(sectors_df)}')

   if not undersized.empty:
      print('\n  Undersized tearsheets:')
      print(undersized.to_string(index=False))
   if not wrong_pages.empty:
      print('\n  Unexpected page counts:')
      print(wrong_pages.to_string(index=False))

   print()
   print(
      f'  Size range: {checks_df["size_kb"].min():.1f} KB to '
      f'{checks_df["size_kb"].max():.1f} KB, '
      f'median {checks_df["size_kb"].median():.1f} KB'
   )

   return generated_df, skipped_df, sectors_df, checks_df


if __name__ == '__main__':
   main()
