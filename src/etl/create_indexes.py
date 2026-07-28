import sqlite3
import time
from pathlib import Path

DB_PATH = 'data/nifty100.db'

# Table mapped to the columns to index. A two column index on
# (company_id, year) also serves lookups on company_id alone, so a
# separate single column index would be redundant.
INDEX_TARGETS = {
   'profitandloss': ['company_id', 'year'],
   'balancesheet': ['company_id', 'year'],
   'cashflow': ['company_id', 'year'],
   'financial_ratios': ['company_id', 'year'],
   'market_cap': ['company_id', 'year'],
   'stock_prices': ['company_id', 'year'],
   'documents': ['company_id'],
   'sectors': ['company_id'],
   'peer_groups': ['company_id'],
   'peer_percentiles': ['company_id'],
   'analysis': ['company_id'],
   'prosandcons': ['company_id']
}


def get_connection():
   return sqlite3.connect(DB_PATH)


def existing_tables(connection):
   rows = connection.execute(
      "SELECT name FROM sqlite_master WHERE type = 'table'"
   ).fetchall()

   return {row[0] for row in rows}


def existing_indexes(connection):
   rows = connection.execute(
      "SELECT name FROM sqlite_master WHERE type = 'index'"
   ).fetchall()

   return {row[0] for row in rows}


def create_indexes(connection):
   tables = existing_tables(connection)
   before = existing_indexes(connection)

   created = []
   skipped = []

   for table, columns in INDEX_TARGETS.items():
      if table not in tables:
         skipped.append((table, 'table not present'))
         continue

      available = {
         row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')
      }
      usable = [column for column in columns if column in available]

      if not usable:
         skipped.append((table, 'no indexable columns'))
         continue

      index_name = f'idx_{table}_{"_".join(usable)}'
      column_list = ', '.join(f'"{column}"' for column in usable)

      connection.execute(
         f'CREATE INDEX IF NOT EXISTS {index_name} '
         f'ON "{table}" ({column_list})'
      )

      if index_name not in before:
         created.append(index_name)

   connection.commit()
   connection.execute('ANALYZE')
   connection.commit()

   return created, skipped


def benchmark_query(connection, sql, params=(), repeats=50):
   # Median elapsed milliseconds over a number of runs, or None if the
   # query cannot run yet.
   #
   # This target may be invoked on a freshly loaded database, before the
   # screener has built peer_percentiles. A benchmark is diagnostic
   # output, so a missing table must not stop the indexes being created.
   timings = []

   for _ in range(repeats):
      started = time.perf_counter()
      try:
         connection.execute(sql, params).fetchall()
      except sqlite3.OperationalError:
         return None
      timings.append((time.perf_counter() - started) * 1000)

   timings.sort()

   return timings[len(timings) // 2]


def main():
   if not Path(DB_PATH).exists():
      print(f'{DB_PATH} not found. Run `make load` first.')
      return

   connection = get_connection()

   try:
      benchmarks = {
         'financial_ratios by company': (
            'SELECT * FROM financial_ratios WHERE company_id = ?', ('TCS',)
         ),
         'profitandloss by company+year': (
            'SELECT * FROM profitandloss WHERE company_id = ? AND year = ?',
            ('TCS', 'Mar 2024')
         ),
         'peer_percentiles by company': (
            'SELECT * FROM peer_percentiles WHERE company_id = ?', ('TCS',)
         )
      }

      before = {
         label: benchmark_query(connection, sql, params)
         for label, (sql, params) in benchmarks.items()
      }

      created, skipped = create_indexes(connection)

      after = {
         label: benchmark_query(connection, sql, params)
         for label, (sql, params) in benchmarks.items()
      }

      print(f'Created {len(created)} index(es):')
      for name in created:
         print(f'  {name}')
      if not created:
         print('  (all indexes already present)')

      if skipped:
         print()
         print('Skipped:')
         for table, reason in skipped:
            print(f'  {table:20} {reason}')

      print()
      print(f'{"query":34}{"before":>10}{"after":>10}{"change":>10}')
      for label in benchmarks:
         if before[label] is None or after[label] is None:
            print(f'{label:34}{"table not built yet":>29}')
            continue

         change = (
            (after[label] - before[label]) / before[label] * 100
            if before[label] else 0
         )
         print(
            f'{label:34}{before[label]:9.3f}ms{after[label]:9.3f}ms'
            f'{change:+9.1f}%'
         )

      total_indexes = len([
         name for name in existing_indexes(connection)
         if name.startswith('idx_')
      ])
      print()
      print(f'Project indexes now present: {total_indexes}')

   finally:
      connection.close()


if __name__ == '__main__':
   main()
