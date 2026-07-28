'''
Daily reports compilation for the N100 Financial Intelligence Platform.

Sprint 6 handover deliverable. Collects the project's day-level and
sprint-level records into a single PDF for submission.

Sources, in order of precedence:
   1. The Day N project logs kept as .docx in the instructions folder
   2. The six sprint retrospectives in docs/
   3. A coverage map stating which days are recorded at which level

COVERAGE HONESTY
   Day-level logs exist for Days 4 to 12 only. Days 1 to 3 and 13 to 45
   were recorded as stand-ups submitted through the internship portal and
   as sprint retrospectives, not as daily log files. This document says so
   on its first page rather than presenting sprint records as if they were
   daily ones.

Run with:
   python -m src.reports.daily_reports
'''

import html
import re
import zipfile
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
   PageBreak,
   Paragraph,
   SimpleDocTemplate,
   Spacer,
   Table,
   TableStyle
)

OUTPUT_PATH = 'docs/daily_reports.pdf'

# The daily logs live outside the repository, alongside the sprint guides.
LOG_DIRECTORIES = [
   Path('../../PJT2/instructions_and_doc'),
   Path('E:/iim/SIP/AMO/SIP_outside_assignment/BlueStock/PJT2/'
        'instructions_and_doc')
]

RETROSPECTIVE_DIR = Path('docs')

NAVY = colors.HexColor('#1F3864')
AMBER = colors.HexColor('#BF8F00')
LIGHT_GREY = colors.HexColor('#F2F2F2')
MID_GREY = colors.HexColor('#BFBFBF')

PAGE_WIDTH, PAGE_HEIGHT = A4
CONTENT_WIDTH = PAGE_WIDTH - 32 * mm

# Sprint boundaries, used for the coverage map.
SPRINTS = [
   ('Sprint 1', 'Days 1-7', 'Data Foundation'),
   ('Sprint 2', 'Days 8-14', 'Financial Ratio Engine'),
   ('Sprint 3', 'Days 15-21', 'Screener & Peer Comparison'),
   ('Sprint 4', 'Days 22-28', 'Dashboard & Valuation'),
   ('Sprint 5', 'Days 29-35', 'Intelligence, NLP & PDF Reports'),
   ('Sprint 6', 'Days 36-45', 'API Server, Clustering & Final QA')
]

STYLES = {
   'cover_title': ParagraphStyle(
      'cover_title', fontName='Helvetica-Bold', fontSize=25,
      textColor=NAVY, leading=30, alignment=TA_CENTER
   ),
   'cover_sub': ParagraphStyle(
      'cover_sub', fontName='Helvetica', fontSize=12,
      textColor=colors.HexColor('#595959'), leading=17, alignment=TA_CENTER
   ),
   'chapter': ParagraphStyle(
      'chapter', fontName='Helvetica-Bold', fontSize=15,
      textColor=NAVY, leading=19, spaceAfter=4
   ),
   'entry': ParagraphStyle(
      'entry', fontName='Helvetica-Bold', fontSize=12,
      textColor=NAVY, leading=16, spaceBefore=6, spaceAfter=4
   ),
   'heading': ParagraphStyle(
      'heading', fontName='Helvetica-Bold', fontSize=10,
      textColor=NAVY, leading=13, spaceBefore=6, spaceAfter=3
   ),
   'body': ParagraphStyle(
      'body', fontName='Helvetica', fontSize=9, leading=12.5, spaceAfter=4
   ),
   'bullet': ParagraphStyle(
      'bullet', fontName='Helvetica', fontSize=9, leading=12.2,
      leftIndent=10, spaceAfter=1.5
   ),
   'sub_bullet': ParagraphStyle(
      'sub_bullet', fontName='Helvetica', fontSize=8.5, leading=11.5,
      leftIndent=22, spaceAfter=1.5
   ),
   'cell': ParagraphStyle(
      'cell', fontName='Helvetica', fontSize=8.5, leading=11
   ),
   'cell_head': ParagraphStyle(
      'cell_head', fontName='Helvetica-Bold', fontSize=8.5,
      textColor=colors.white, leading=11
   ),
   'caption': ParagraphStyle(
      'caption', fontName='Helvetica-Oblique', fontSize=8,
      textColor=colors.HexColor('#7F7F7F'), leading=11, spaceAfter=4
   )
}

PARAGRAPH_BREAK = re.compile(r'</w:p>')
TAG = re.compile(r'<[^>]+>')
DAY_NUMBER = re.compile(r'Day(\d+)', re.IGNORECASE)


def _find_log_directory():
   for candidate in LOG_DIRECTORIES:
      if candidate.exists():
         return candidate

   return None


def extract_docx_text(path):
   '''Plain text from a .docx, one line per Word paragraph.'''
   with zipfile.ZipFile(path) as archive:
      xml = archive.read('word/document.xml').decode('utf-8', 'ignore')

   xml = PARAGRAPH_BREAK.sub('\n', xml)
   xml = re.sub(r'<w:tab[^>]*/>', '  ', xml)
   xml = re.sub(r'<w:br[^>]*/>', '\n', xml)
   text = html.unescape(TAG.sub('', xml))

   lines = []
   for line in text.split('\n'):
      stripped = line.strip()
      if stripped:
         lines.append(stripped)

   return lines


def collect_daily_logs():
   '''Day-level logs found on disk, ordered by day number.'''
   directory = _find_log_directory()
   if directory is None:
      return []

   entries = []

   for path in directory.glob('*.docx'):
      if 'Log' not in path.name:
         continue

      match = DAY_NUMBER.search(path.name)
      day = int(match.group(1)) if match else None

      if day is None:
         # Sprint2_Day12_Part1_Chat_Transfer_Log has the day mid-name.
         fallback = re.search(r'Day(\d+)', path.stem, re.IGNORECASE)
         day = int(fallback.group(1)) if fallback else 999

      entries.append({
         'day': day,
         'filename': path.name,
         'lines': extract_docx_text(path)
      })

   return sorted(entries, key=lambda item: item['day'])


def collect_retrospectives():
   '''Sprint retrospectives from docs/, ordered by sprint number.'''
   entries = []

   for path in sorted(RETROSPECTIVE_DIR.glob('*retro*.md')):
      match = re.search(r'(\d)', path.stem)
      sprint = int(match.group(1)) if match else 99

      entries.append({
         'sprint': sprint,
         'filename': path.name,
         'lines': path.read_text(encoding='utf-8').split('\n')
      })

   return sorted(entries, key=lambda item: item['sprint'])


def _escape(text):
   return (
      text.replace('&', '&amp;')
      .replace('<', '&lt;')
      .replace('>', '&gt;')
   )


def _render_plain_lines(lines):
   '''Turn extracted log lines into flowables.'''
   flowables = []

   for line in lines:
      safe = _escape(line)

      if line.startswith(('- ', '• ', '* ')):
         flowables.append(
            Paragraph(f'&bull;&nbsp; {safe[2:].strip()}', STYLES['bullet'])
         )
      elif line.startswith(('  - ', '   - ')):
         flowables.append(
            Paragraph(
               f'&ndash;&nbsp; {safe.strip()[2:].strip()}',
               STYLES['sub_bullet']
            )
         )
      elif line.endswith(':') and len(line) < 60:
         flowables.append(Paragraph(f'<b>{safe}</b>', STYLES['heading']))
      else:
         flowables.append(Paragraph(safe, STYLES['body']))

   return flowables


def _render_markdown(lines):
   '''Minimal markdown rendering: headings, bullets, tables as text.'''
   flowables = []

   for line in lines:
      stripped = line.strip()

      if not stripped:
         continue
      if stripped.startswith('---'):
         continue

      safe = _escape(stripped)

      if stripped.startswith('# '):
         continue  # the document title is supplied by the caller
      if stripped.startswith('## '):
         flowables.append(Paragraph(safe[3:], STYLES['entry']))
      elif stripped.startswith('# '):
         flowables.append(Paragraph(safe[2:], STYLES['entry']))
      elif stripped.startswith('#'):
         flowables.append(
            Paragraph(safe.lstrip('#').strip(), STYLES['heading'])
         )
      elif stripped.startswith('|'):
         cells = [c.strip() for c in stripped.strip('|').split('|')]
         if all(set(c) <= set('-: ') for c in cells):
            continue
         flowables.append(
            Paragraph(
               '&bull;&nbsp; ' + ' &nbsp;|&nbsp; '.join(
                  _escape(c) for c in cells if c
               ),
               STYLES['bullet']
            )
         )
      elif stripped.startswith(('- ', '* ')):
         flowables.append(
            Paragraph(f'&bull;&nbsp; {safe[2:]}', STYLES['bullet'])
         )
      elif re.match(r'^\d+\.\s', stripped):
         flowables.append(Paragraph(f'&bull;&nbsp; {safe}', STYLES['bullet']))
      elif stripped.startswith('```'):
         continue
      else:
         flowables.append(Paragraph(safe, STYLES['body']))

   return flowables


def _table(headers, rows, widths=None):
   head = [Paragraph(h, STYLES['cell_head']) for h in headers]
   body = [
      [Paragraph(str(cell), STYLES['cell']) for cell in row] for row in rows
   ]

   if widths is None:
      widths = [CONTENT_WIDTH / len(headers)] * len(headers)

   table = Table([head] + body, colWidths=widths, repeatRows=1)
   table.setStyle(TableStyle([
      ('BACKGROUND', (0, 0), (-1, 0), NAVY),
      ('VALIGN', (0, 0), (-1, -1), 'TOP'),
      ('GRID', (0, 0), (-1, -1), 0.4, MID_GREY),
      ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
      ('TOPPADDING', (0, 0), (-1, -1), 4),
      ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
      ('LEFTPADDING', (0, 0), (-1, -1), 5),
      ('RIGHTPADDING', (0, 0), (-1, -1), 5)
   ]))

   return table


def _callout(title, text, colour):
   table = Table(
      [[Paragraph(f'<b>{title}</b><br/>{text}', STYLES['cell'])]],
      colWidths=[CONTENT_WIDTH]
   )
   table.setStyle(TableStyle([
      ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FBFBFB')),
      ('BOX', (0, 0), (-1, -1), 0.6, colour),
      ('LINEBEFORE', (0, 0), (0, -1), 3, colour),
      ('TOPPADDING', (0, 0), (-1, -1), 6),
      ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
      ('LEFTPADDING', (0, 0), (-1, -1), 8),
      ('RIGHTPADDING', (0, 0), (-1, -1), 8)
   ]))

   return table


def _cover(daily_count, retro_count):
   return [
      Spacer(1, 55 * mm),
      Paragraph('N100 Financial Intelligence Platform', STYLES['cover_title']),
      Spacer(1, 4 * mm),
      Paragraph('Daily Reports', STYLES['cover_title']),
      Spacer(1, 10 * mm),
      Paragraph(
         'Project progress record, 45-day internship build',
         STYLES['cover_sub']
      ),
      Spacer(1, 18 * mm),
      Paragraph(
         f'{daily_count} day-level logs &nbsp;|&nbsp; '
         f'{retro_count} sprint retrospectives',
         STYLES['cover_sub']
      ),
      Spacer(1, 22 * mm),
      Paragraph(
         f'Compiled {date.today().isoformat()}<br/>'
         'Raj Sarania, Data Analyst<br/>'
         'Summer Internship Programme, Bluestock Fintech',
         STYLES['cover_sub']
      )
   ]


def _coverage_section(daily_entries):
   recorded_days = sorted({entry['day'] for entry in daily_entries})

   rows = []
   for name, span, focus in SPRINTS:
      start, end = [int(n) for n in re.findall(r'\d+', span)]
      in_span = [d for d in recorded_days if start <= d <= end]

      if in_span:
         level = f'Day-level logs for Days {min(in_span)} to {max(in_span)}'
      else:
         level = 'Sprint-level retrospective'

      rows.append([name, span, focus, level])

   return [
      Paragraph('Coverage map', STYLES['chapter']),
      Paragraph(
         'What level of record exists for each part of the project.',
         STYLES['caption']
      ),
      _callout(
         'Read this first',
         'This project was recorded at two levels of granularity. '
         f'Day-level log files exist for {len(recorded_days)} days: '
         f'{", ".join(str(d) for d in recorded_days)}. '
         'The remaining days were recorded as stand-ups submitted through '
         'the internship portal and consolidated into the six sprint '
         'retrospectives reproduced in Part 2 of this document. '
         'No day-level entry has been reconstructed after the fact: where '
         'a daily log does not exist, this document says so rather than '
         'presenting a sprint record as a daily one.',
         AMBER
      ),
      Spacer(1, 5 * mm),
      _table(
         ['Sprint', 'Days', 'Focus', 'Record level'],
         rows,
         widths=[20 * mm, 20 * mm, 52 * mm, CONTENT_WIDTH - 92 * mm]
      ),
      Spacer(1, 5 * mm),
      Paragraph('Document structure', STYLES['heading']),
      Paragraph(
         '<b>Part 1</b> reproduces every day-level project log, in day '
         'order, as written at the time.<br/>'
         '<b>Part 2</b> reproduces the six sprint retrospectives, which '
         'carry the day-by-day detail for the remainder of the project '
         'including the decisions taken, defects found and technical debt '
         'recorded.',
         STYLES['body']
      )
   ]


def build_document(output_path=OUTPUT_PATH):
   '''Render the daily reports PDF and return its path and counts.'''
   daily_entries = collect_daily_logs()
   retrospectives = collect_retrospectives()

   destination = Path(output_path)
   destination.parent.mkdir(parents=True, exist_ok=True)

   document = SimpleDocTemplate(
      str(destination),
      pagesize=A4,
      leftMargin=16 * mm,
      rightMargin=16 * mm,
      topMargin=15 * mm,
      bottomMargin=15 * mm,
      title='N100 Daily Reports',
      author='N100 Financial Intelligence Platform'
   )

   story = list(_cover(len(daily_entries), len(retrospectives)))

   story.append(PageBreak())
   story.extend(_coverage_section(daily_entries))

   # Part 1: the day-level logs.
   story.append(PageBreak())
   story.append(Paragraph('Part 1 - Day-level project logs',
                          STYLES['chapter']))
   story.append(Paragraph(
      'Reproduced as written at the time, in day order.',
      STYLES['caption']
   ))

   for index, entry in enumerate(daily_entries):
      if index:
         story.append(PageBreak())
      story.append(Paragraph(
         f'Day {entry["day"]} project log', STYLES['entry']
      ))
      story.append(Paragraph(
         f'Source: {entry["filename"]}', STYLES['caption']
      ))
      story.extend(_render_plain_lines(entry['lines']))

   # Part 2: the sprint retrospectives.
   story.append(PageBreak())
   story.append(Paragraph('Part 2 - Sprint retrospectives',
                          STYLES['chapter']))
   story.append(Paragraph(
      'The consolidated record for the days without an individual log.',
      STYLES['caption']
   ))

   for entry in retrospectives:
      story.append(PageBreak())
      story.append(Paragraph(
         f'Sprint {entry["sprint"]} retrospective', STYLES['entry']
      ))
      story.append(Paragraph(
         f'Source: docs/{entry["filename"]}', STYLES['caption']
      ))
      story.extend(_render_markdown(entry['lines']))

   document.build(story)

   return destination, len(daily_entries), len(retrospectives)


def main():
   destination, daily_count, retro_count = build_document()
   pages = len(
      re.findall(rb'/Type\s*/Page[^s]', destination.read_bytes())
   )

   print(f'Wrote {destination}')
   print(f'  day-level logs        : {daily_count}')
   print(f'  sprint retrospectives : {retro_count}')
   print(f'  pages                 : {pages}')
   print(f'  size                  : '
         f'{destination.stat().st_size / 1024:,.1f} KB')

   if daily_count == 0:
      print('  WARNING: no daily logs found. Check the log directory path.')


if __name__ == '__main__':
   main()
