'''
SQLite loader for the N100 Financial Intelligence Platform.

Creates the database schema and loads validated core datasets
into the SQLite data warehouse.
'''

import sqlite3
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
   connection.commit()

def load_data(connection):
   # Load all core datasets into SQLite
   datasets = load_all_core_files()
   total_rows = 0

   for table_name, dataframe in datasets.items():
      print(f'Loading {table_name}...')
      dataframe.to_sql(
         table_name,
         connection,
         if_exists='append',
         index=False
      )
      rows = len(dataframe)
      total_rows += rows
      print(f'✓ Inserted {rows} rows')

   connection.commit()
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