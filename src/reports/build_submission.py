'''
Submission bundle builder for the N100 Financial Intelligence Platform.

The internship submission form has six slots: three source code zips
(frontend, backend, RestAPI), a database zip, and two PDFs. This module
assembles exactly that, with every zip under the 10 MB form limit.

Segmentation reasoning
   The form is shaped for a conventional web application. This project is
   a Python analytics platform, so the mapping is:

      Frontend  the Streamlit dashboard, plus the radar chart PNGs it
                visualises
      Backend   the ETL, analytics, screener, NLP and report engines,
                plus their generated workbooks and PDFs
      RestAPI   the FastAPI application and its contract
      Database  the schema, the populated database and the audit trail

   The form has no slot for the 23 tracked deliverables, so each is
   attached to the segment that produces or displays it. Placing all of
   reports/ in one zip would come to 13.7 MB and fail the limit, which is
   why the tearsheets and the radar charts sit in different segments.

Every zip carries a MANIFEST.txt explaining what is inside and where the
other segments are, so a reviewer opening one zip is never left guessing.

Run with:
   python -m src.reports.build_submission
'''

import zipfile
from datetime import date
from pathlib import Path

SUBMISSION_DIR = 'submission'

SIZE_LIMIT_MB = 10.0

# Directories and suffixes never included.
EXCLUDE_PARTS = {
   '__pycache__', '.pytest_cache', '.ruff_cache', '.venv', '.git',
   'final_deliverables', 'submission'
}
EXCLUDE_SUFFIXES = {'.pyc', '.pyo'}

# slot name -> (zip filename, description, list of paths)
SEGMENTS = {
   'frontend': (
      '1_source_code_frontend.zip',
      'Streamlit dashboard: entry point, 8 screens, cached data loader, '
      'plus the 92 radar chart PNGs the peer views are built on.',
      [
         'src/dashboard',
         'src/__init__.py',
         'reports/radar_charts',
         'README.md',
         'requirements.txt'
      ]
   ),
   'backend': (
      '2_source_code_backend.zip',
      'Analytics engine: ETL, ratio engine, screener, NLP rule engine, '
      'clustering, statistics and report generators, with the generated '
      'workbooks, company tearsheets, sector reports and portfolio PDF.',
      [
         'src/etl',
         'src/analytics',
         'src/screener',
         'src/nlp',
         'src/reports',
         'src/__init__.py',
         'config',
         'tests',
         'notebooks',
         'Makefile',
         'README.md',
         'requirements.txt',
         'output/screener_output.xlsx',
         'output/peer_comparison.xlsx',
         'output/valuation_summary.xlsx',
         'output/cashflow_intelligence.xlsx',
         'output/capital_allocation.csv',
         'output/cluster_labels.csv',
         'output/cluster_profiles.csv',
         'output/pros_cons_generated.csv',
         'output/analysis_parsed.csv',
         'output/parse_failures.csv',
         'output/distress_alerts.csv',
         'output/pattern_changes.csv',
         'output/portfolio_stats.csv',
         'output/outlier_report.csv',
         'output/valuation_flags.csv',
         'output/skipped_tearsheets.csv',
         'output/acceptance_gates.csv',
         'output/ratio_edge_cases.log',
         'output/perf_notes.md',
         'reports/tearsheets',
         'reports/sector',
         'reports/portfolio',
         'reports/elbow_plot.png',
         'reports/correlation_heatmap.png',
         'docs'
      ]
   ),
   'restapi': (
      '3_source_code_restapi.zip',
      'FastAPI application: 20 endpoints across 7 routers, cached data '
      'access, OpenAPI 3.1 specification and the full test report.',
      [
         'src/api',
         'src/__init__.py',
         'tests/api',
         'docs/openapi.json',
         'reports/pytest_report.html',
         'README.md',
         'requirements.txt'
      ]
   ),
   'database': (
      '4_database_sql.zip',
      'Database layer: DDL schema, the populated SQLite database, the 12 '
      'source Excel workbooks so the database can be rebuilt from '
      'scratch, exploratory queries, index definitions and the load and '
      'validation audit trail.',
      [
         'src/etl/schema.sql',
         'src/etl/sqlite_loader.py',
         'src/etl/create_indexes.py',
         'src/etl/validator.py',
         'src/etl/schemas.py',
         'src/etl/run_validation.py',
         'data/nifty100.db',
         # The source workbooks are gitignored in the repository but must
         # ship here: without them `make load` cannot run and a reviewer
         # cannot verify the ETL layer end to end. Verified by a
         # clean-room extraction test.
         'data/raw',
         'data/supporting',
         'notebooks/exploratory_queries.sql',
         'output/load_audit.csv',
         'output/validation_failures.csv'
      ]
   )
}

# The two PDF slots.
PDF_SLOTS = {
   'technical_documentation': (
      '5_technical_documentation.pdf',
      'docs/technical_documentation.pdf'
   ),
   'daily_reports': (
      '6_daily_reports.pdf',
      'docs/daily_reports.pdf'
   )
}


def _included(path):
   if any(part in EXCLUDE_PARTS for part in path.parts):
      return False
   if path.suffix in EXCLUDE_SUFFIXES:
      return False

   return True


def _files_for(source):
   source = Path(source)

   if not source.exists():
      return []
   if source.is_file():
      return [source] if _included(source) else []

   return [
      path for path in sorted(source.rglob('*'))
      if path.is_file() and _included(path)
   ]


def _manifest(slot, description, paths, file_count, size_mb):
   other = [
      f'  {name:24} {filename}'
      for name, (filename, _d, _p) in SEGMENTS.items()
      if name != slot
   ]

   return '\n'.join([
      'N100 FINANCIAL INTELLIGENCE PLATFORM',
      f'Submission segment: {slot.upper()}',
      f'Built {date.today().isoformat()}',
      '=' * 68,
      '',
      'WHAT IS IN THIS ZIP',
      description,
      '',
      f'  files : {file_count}',
      f'  size  : {size_mb:.2f} MB',
      '',
      'CONTENTS',
      *[f'  {path}' for path in paths],
      '',
      '=' * 68,
      'THE OTHER SUBMISSION SEGMENTS',
      '',
      'This project was submitted in four zips plus two PDFs, because the',
      'form provides separate slots. The full project is the union of all',
      'six uploads.',
      '',
      *other,
      f'  {"technical documentation":24} '
      f'{PDF_SLOTS["technical_documentation"][0]}',
      f'  {"daily reports":24} {PDF_SLOTS["daily_reports"][0]}',
      '',
      '=' * 68,
      'HOW TO RUN THE PROJECT',
      '',
      '  pip install -r requirements.txt',
      '  python -m src.etl.sqlite_loader      # load Excel to SQLite',
      '  python -m src.etl.ratio_engine       # compute KPIs',
      '  python -m src.screener.run_screener  # screener and peer ranks',
      '  streamlit run src/dashboard/app.py   # dashboard on :8501',
      '  uvicorn src.api.main:app --port 8000 # API on :8000, /docs',
      '  python -m pytest -q                  # 308 tests',
      '',
      'A Makefile wraps all of the above; see `make help`. Full',
      'instructions are in README.md and docs/analyst_guide.pdf.',
      '',
      '=' * 68,
      'IMPORTANT DATA NOTE',
      '',
      'The market_cap and stock_prices datasets supplied with this project',
      'are SIMULATED. Every P/E, P/B, EV/EBITDA, dividend yield and market',
      'cap figure derives from them and is illustrative only. All source',
      'data defects found during the build are documented in',
      'docs/technical_documentation.pdf section 7.',
      ''
   ])


def build(output_dir=SUBMISSION_DIR):
   '''Build the four zips and copy the two PDFs. Returns a report.'''
   destination = Path(output_dir)
   destination.mkdir(parents=True, exist_ok=True)

   results = []

   for slot, (filename, description, paths) in SEGMENTS.items():
      archive_path = destination / filename

      collected = []
      missing = []
      for source in paths:
         files = _files_for(source)
         if not files:
            missing.append(source)
         collected.extend(files)

      # De-duplicate while keeping order: README and requirements appear
      # in more than one segment by design.
      seen = set()
      unique = []
      for path in collected:
         key = path.as_posix()
         if key not in seen:
            seen.add(key)
            unique.append(path)

      with zipfile.ZipFile(
         archive_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9
      ) as archive:
         for path in unique:
            archive.writestr(
               f'{archive_path.stem}/{path.as_posix()}',
               path.read_bytes()
            )

         size_mb = sum(
            info.compress_size for info in archive.infolist()
         ) / 1024 / 1024

         archive.writestr(
            f'{archive_path.stem}/MANIFEST.txt',
            _manifest(slot, description, paths, len(unique), size_mb)
         )

      final_mb = archive_path.stat().st_size / 1024 / 1024

      results.append({
         'slot': slot,
         'file': filename,
         'files': len(unique),
         'size_mb': round(final_mb, 2),
         'within_limit': final_mb < SIZE_LIMIT_MB,
         'missing': missing
      })

   # The PDFs are copied rather than zipped: the form accepts .pdf.
   for slot, (filename, source) in PDF_SLOTS.items():
      source_path = Path(source)
      target = destination / filename

      if source_path.exists():
         target.write_bytes(source_path.read_bytes())
         size_mb = target.stat().st_size / 1024 / 1024
         results.append({
            'slot': slot,
            'file': filename,
            'files': 1,
            'size_mb': round(size_mb, 2),
            'within_limit': size_mb < SIZE_LIMIT_MB,
            'missing': []
         })
      else:
         results.append({
            'slot': slot,
            'file': filename,
            'files': 0,
            'size_mb': 0.0,
            'within_limit': False,
            'missing': [source]
         })

   _write_upload_guide(destination, results)

   return results


def _write_upload_guide(destination, results):
   lines = [
      '# N100 Submission Bundle',
      '',
      f'Built {date.today().isoformat()}.',
      '',
      'Upload these six files to the corresponding slots on the form.',
      '',
      '| Form slot | File | Size | Files |',
      '| --- | --- | --- | --- |',
      f'| Source Code (Frontend) | `{results[0]["file"]}` | '
      f'{results[0]["size_mb"]} MB | {results[0]["files"]} |',
      f'| Source Code (Backend) | `{results[1]["file"]}` | '
      f'{results[1]["size_mb"]} MB | {results[1]["files"]} |',
      f'| Source Code (RestAPI) | `{results[2]["file"]}` | '
      f'{results[2]["size_mb"]} MB | {results[2]["files"]} |',
      f'| Database SQL File | `{results[3]["file"]}` | '
      f'{results[3]["size_mb"]} MB | {results[3]["files"]} |',
      f'| Technical Documentation | `{results[4]["file"]}` | '
      f'{results[4]["size_mb"]} MB | PDF |',
      f'| Daily Reports | `{results[5]["file"]}` | '
      f'{results[5]["size_mb"]} MB | PDF |',
      '',
      'Every file is under the 10 MB form limit, so nothing needs to be',
      'sent separately.',
      '',
      '## Notes for the reviewer',
      '',
      '- The form is shaped for a web application; this is a Python',
      '  analytics platform. The Streamlit dashboard is the frontend, the',
      '  ETL and analytics engine is the backend, and FastAPI is the API.',
      '- The form has no slot for the 23 generated deliverables, so each',
      '  is attached to the segment that produces or displays it. Every',
      '  zip contains a MANIFEST.txt naming the other segments.',
      '- Valuation figures come from a simulated dataset and are',
      '  illustrative only.',
      '',
      'Regenerate this bundle with:',
      '',
      '```bash',
      'python -m src.reports.build_submission',
      '```'
   ]

   (destination / 'UPLOAD_GUIDE.md').write_text(
      '\n'.join(lines) + '\n', encoding='utf-8'
   )


def main():
   results = build()

   print('SUBMISSION BUNDLE')
   print('=' * 70)
   print(f'{"slot":26}{"size":>9}{"files":>8}   limit')
   for row in results:
      verdict = 'OK' if row['within_limit'] else 'OVER LIMIT'
      print(
         f'{row["slot"]:26}{row["size_mb"]:8.2f} MB{row["files"]:8}   '
         f'{verdict}'
      )

   over = [row for row in results if not row['within_limit']]
   missing = [row for row in results if row['missing']]

   print()
   if over:
      print('FILES OVER THE 10 MB LIMIT:')
      for row in over:
         print(f'  {row["file"]} at {row["size_mb"]} MB')
   else:
      print('All six uploads are within the 10 MB form limit.')

   if missing:
      print()
      print('MISSING SOURCES (not included in a zip):')
      for row in missing:
         for path in row['missing']:
            print(f'  {row["slot"]:14} {path}')

   print()
   print(f'Bundle written to {Path(SUBMISSION_DIR).resolve()}')
   print('See submission/UPLOAD_GUIDE.md for the slot mapping.')


if __name__ == '__main__':
   main()
