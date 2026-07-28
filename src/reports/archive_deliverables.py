import shutil
from datetime import date
from pathlib import Path

import pandas as pd

from src.reports.acceptance import DELIVERABLES

ARCHIVE_DIR = 'output/final_deliverables'
MANIFEST_NAME = 'MANIFEST.csv'
README_NAME = 'README.md'


def _target_name(code, source):
   # Prefix with the deliverable id so the handover directory sorts in tracker order rather than alphabetically.
   return f'{code}_{source.name}'


def archive(output_dir=ARCHIVE_DIR):
   destination = Path(output_dir)

   # Start clean so a removed deliverable does not linger from a previous run.
   if destination.exists():
      shutil.rmtree(destination)
   destination.mkdir(parents=True, exist_ok=True)

   rows = []

   for code, sprint, name, location in DELIVERABLES:
      path_part = location.split(' ->')[0]
      source = Path(path_part)

      if not source.exists():
         rows.append({
            'id': code,
            'sprint': sprint,
            'deliverable': name,
            'source': path_part,
            'archived_as': None,
            'kind': 'missing',
            'files': 0,
            'size_kb': 0.0
         })
         continue

      target_name = _target_name(code, source)
      target = destination / target_name

      if source.is_dir():
         shutil.copytree(source, target)
         files = [item for item in target.rglob('*') if item.is_file()]
         kind = 'directory'
      else:
         shutil.copy2(source, target)
         files = [target]
         kind = 'file'

      rows.append({
         'id': code,
         'sprint': sprint,
         'deliverable': name,
         'source': path_part,
         'archived_as': target_name,
         'kind': kind,
         'files': len(files),
         'size_kb': round(
            sum(item.stat().st_size for item in files) / 1024, 1
         )
      })

   manifest = pd.DataFrame(rows)
   manifest.to_csv(destination / MANIFEST_NAME, index=False)

   _write_readme(destination, manifest)

   return destination, manifest


def _write_readme(destination, manifest):
   present = int(manifest['archived_as'].notna().sum())
   total_files = int(manifest['files'].sum())
   total_mb = manifest['size_kb'].sum() / 1024

   lines = [
      '# N100 Financial Intelligence Platform - Final Deliverables',
      '',
      f'Archived {date.today().isoformat()}.',
      '',
      f'- Deliverables: **{present} of {len(manifest)}**',
      f'- Files: **{total_files:,}**',
      f'- Total size: **{total_mb:,.1f} MB**',
      '',
      'Each entry is prefixed with its tracker id so this directory '
      'sorts in deliverable order.',
      '',
      '| ID | Sprint | Deliverable | Archived as | Files | Size (KB) |',
      '| --- | --- | --- | --- | --- | --- |'
   ]

   for row in manifest.itertuples():
      lines.append(
         f'| {row.id} | {row.sprint} | {row.deliverable} | '
         f'`{row.archived_as or "MISSING"}` | {row.files} | '
         f'{row.size_kb:,.1f} |'
      )

   lines += [
      '',
      '## Notes',
      '',
      '- `D-16_tearsheets` holds 91 PDFs, not 92. JIOFIN carries only 2 '
      'years of data against a 3 year floor and is logged in '
      '`output/skipped_tearsheets.csv`.',
      '- `D-17_sector` holds 11 PDFs: 10 real broad sectors plus an '
      'Unclassified bucket for the two tickers missing from the company '
      'master.',
      '- All valuation figures derive from a **simulated** dataset and '
      'are illustrative only.',
      '- Acceptance gate results are in `D-23_acceptance_checklist.pdf` '
      'and `output/acceptance_gates.csv`.',
      '',
      'Regenerate this directory with:',
      '',
      '```bash',
      'python -m src.reports.archive_deliverables',
      '```'
   ]

   (destination / README_NAME).write_text(
      '\n'.join(lines) + '\n', encoding='utf-8'
   )


def main():
   destination, manifest = archive()

   present = int(manifest['archived_as'].notna().sum())
   missing = manifest[manifest['archived_as'].isna()]

   print(f'Archived to {destination}')
   print(f'  deliverables : {present} of {len(manifest)}')
   print(f'  files        : {int(manifest["files"].sum()):,}')
   print(f'  size         : {manifest["size_kb"].sum() / 1024:,.1f} MB')
   print()

   print(manifest[[
      'id', 'deliverable', 'kind', 'files', 'size_kb'
   ]].to_string(index=False))

   if not missing.empty:
      print()
      print('MISSING:')
      for row in missing.itertuples():
         print(f'  {row.id}  {row.deliverable} ({row.source})')


if __name__ == '__main__':
   main()
