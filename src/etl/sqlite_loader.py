'''
SQLite loader for the N100 Financial Intelligence Platform.

Creates the database schema and loads validated core datasets
into the SQLite data warehouse.
'''

import sqlite3
import pandas as pd
import time
from pathlib import Path
from src.etl.loader import load_all_core_files

def get_connection(db_path='data/nifty100.db'):
   # create and return a sqlite database connection
   db_path = Path(db_path)
   db_path.parent.mkdir(parents=True, exist_ok=True)

   return sqlite3.connect(db_path)

def create_schema(connection, schema_path='src/etl/schema.sql'):
   # create database table from sql schema file
   schema_path = Path(schema_path)
   with open(schema_path, 'r', encoding='utf-8') as file:
      sql_script = file.read()

   connection.executescript(sql_script)
   connection.execute("PRAGMA foreign_keys = ON;")
   connection.commit()

def load_supporting_files():
   # Load all supplementary datasets
   base_path = Path('data/supporting')

   return {
      'financial_ratios': pd.read_excel(base_path / 'financial_ratios.xlsx', header=0),
      'market_cap': pd.read_excel(base_path / 'market_cap.xlsx', header=0),
      'peer_groups': pd.read_excel(base_path / 'peer_groups.xlsx', header=0),
      'sectors': pd.read_excel(base_path / 'sectors.xlsx', header=0),
      'stock_prices': pd.read_excel(base_path / 'stock_prices.xlsx', header=0)
   }

def load_data(connection):
   # Load all datasets into SQLite and generate load audit.
   datasets = load_all_core_files()
   datasets.update(load_supporting_files())
   audit = []
   total_rows = 0

   for table_name, dataframe in datasets.items():
      start = time.time()
      print(f'Loading {table_name}...')

      dataframe.to_sql(
         table_name,
         connection,
         if_exists='append',
         index=False
      )

      runtime = round(time.time() - start, 3)
      rows = len(dataframe)
      total_rows += rows

      audit.append({
         'table': table_name,
         'rows_in': rows,
         'rows_out': rows,
         'rejected': 0,
         'runtime_s': runtime
      })
      print(f'✓ Inserted {rows} rows')
   connection.commit()

   pd.DataFrame(audit).to_csv(
      'reports/load_audit.csv',
      index=False
   )

   return len(datasets), total_rows

def main():
   # create the sqlite database and load all core datasets
   connection = get_connection()

   try:
      create_schema(connection)
      tables_loaded, total_rows = load_data(connection)
      print('\n===================================')
      print('Database created successfully')
      print(f'Tables loaded : {tables_loaded}')
      print(f'Rows inserted : {total_rows}')
      print('Database      : data/nifty100.db')
      print('===================================')
   except Exception as e:
      print(f'Database loading failed: {e}')
      raise
   finally:
      connection.close()

if __name__ == '__main__':
   main()