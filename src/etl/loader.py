import pandas as pd
from pathlib import Path


def normalize_ticker(ticker):
   if pd.isna(ticker):
      return None
   return str(ticker).strip().upper()


def normalize_year(year):
   if pd.isna(year):
      return None
   year = str(year).strip()
   month_map = {
      'MAR': '03',
      'DEC': '12'
   }

   try:
      month, yy = year.split('-')
      month = month.upper()
      if month not in month_map:
         return year

      full_year = 2000 + int(yy)
      return f'{full_year}-{month_map[month]}'
   
   except Exception:
      return year


def load_excel(file_path):
   # Load a single excel file using project standard
   return pd.read_excel(file_path, header=1)


def load_all_core_files(raw_dir='data/raw'):
   # Load all 7 core datasets
   raw_dir = Path(raw_dir)
   datasets = {}

   for file in raw_dir.glob('*.xlsx'):
      datasets[file.stem] = load_excel(file)

   return datasets