'''
Day 6 - Data Quality Review

Performs post-load verification of the SQLite database by checking:
1. Database connectivity
2. Table existence
3. Row count verification
'''

import sqlite3
from pathlib import Path


DB_PATH = Path('data/nifty100.db')

EXPECTED_TABLE_COUNTS = {
   'analysis': 20,
   'balancesheet': 1312,
   'cashflow': 1187,
   'companies': 92,
   'documents': 1585,
   'profitandloss': 1276,
   'prosandcons': 16,
   'financial_ratios': 1184,
   'market_cap': 552,
   'peer_groups': 56,
   'sectors': 92,
   'stock_prices': 5520,
}


def get_connection():
   return sqlite3.connect(DB_PATH)


def table_exists(cursor, table_name):
   cursor.execute(
      '''
      SELECT name
      FROM sqlite_master
      WHERE type='table'
      AND name=?
      ''',
      (table_name,),
   )
   return cursor.fetchone() is not None


def get_row_count(cursor, table_name):
   cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
   return cursor.fetchone()[0]


def main():
   print('=' * 60)
   print('N100 DATA QUALITY REVIEW')
   print('=' * 60)

   connection = get_connection()
   cursor = connection.cursor()
   passed = 0

   try:
      print('\nDatabase Connection')
      print('------------------------------')
      print('[PASS] Connected to SQLite database')
      print('\nTable Verification')
      print('------------------------------')

      for table, expected in EXPECTED_TABLE_COUNTS.items():
         if not table_exists(cursor, table):
               print(f'[FAIL] {table:<20} Table not found')
               continue

         actual = get_row_count(cursor, table)

         if actual == expected:
               print(
                  f'[PASS] {table:<20}'
                  f'Expected: {expected:<5}'
                  f'Actual: {actual:<5}'
               )
               passed += 1
         else:
               print(
                  f'[FAIL] {table:<20}'
                  f'Expected: {expected:<5}'
                  f'Actual: {actual:<5}'
               )

      print('\nSummary')
      print('------------------------------')
      print(f'Tables Verified : {passed}/{len(EXPECTED_TABLE_COUNTS)}')

      if passed == len(EXPECTED_TABLE_COUNTS):
         print('Overall Status  : PASS')
      else:
         print('Overall Status  : FAIL')

   finally:
      connection.close()
      print('\nSQLite connection closed.')


if __name__ == '__main__':
   main()