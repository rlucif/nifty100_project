from pathlib import Path
import pandas as pd

from src.nlp.features import (
   build_company_features,
   consecutive_direction,
   load_history,
   sustained_above,
   trailing_streak
)

DB_PATH = 'data/nifty100.db'
OUTPUT_PATH = 'output/pros_cons_generated.csv'

CONFIDENCE_FLOOR = 60.0
CONFIDENCE_CEILING = 100.0

TYPE_PRO = 'pro'
TYPE_CON = 'con'


def _scaled_confidence(value, threshold, strong, higher_is_stronger=True):
   # Map threshold -> 60 and strong -> 100, clipped to both ends.
   if value is None or pd.isna(value):
      return None

   span = abs(strong - threshold)
   if span == 0:
      return CONFIDENCE_FLOOR

   if higher_is_stronger:
      progress = (value - threshold) / span
   else:
      progress = (threshold - value) / span

   progress = max(0.0, min(1.0, progress))

   return round(
      CONFIDENCE_FLOOR + progress * (CONFIDENCE_CEILING - CONFIDENCE_FLOOR),
      1
   )


def _streak_confidence(streak, required, strong):
   if streak < required:
      return None

   return _scaled_confidence(float(streak), float(required), float(strong))


# Pro rules
def _pro_rules(f):
   results = []

   # Rule 1: ROE above 20% sustained for 3 or more years.
   if sustained_above(f['roe_series'], 20, periods=3):
      results.append((
         'PRO-01',
         'Consistently high return on equity above 20% demonstrates '
         'exceptional capital efficiency',
         _scaled_confidence(f['roe'], 20, 40)
      ))

   # Rule 2: free cash flow positive for 5 or more consecutive years.
   fcf_streak = trailing_streak(f['fcf_series'], lambda value: value > 0)
   if fcf_streak >= 5:
      results.append((
         'PRO-02',
         'Strong free cash flow generation over 5 years signals healthy '
         'business fundamentals',
         _streak_confidence(fcf_streak, 5, 10)
      ))

   # Rule 3: debt free in the latest year.
   if f['debt_to_equity'] is not None and f['debt_to_equity'] == 0:
      results.append((
         'PRO-03',
         'Debt-free balance sheet provides financial flexibility and '
         'eliminates interest burden',
         CONFIDENCE_CEILING
      ))

   # Rule 4: revenue CAGR above 15% over 5 years.
   if f['revenue_cagr_5yr'] is not None and f['revenue_cagr_5yr'] > 15:
      results.append((
         'PRO-04',
         'Revenue growing at above 15% CAGR over 5 years reflects strong '
         'business momentum',
         _scaled_confidence(f['revenue_cagr_5yr'], 15, 30)
      ))

   # Rule 5: operating margin above 25% in the latest year.
   if f['opm'] is not None and f['opm'] > 25:
      results.append((
         'PRO-05',
         'Operating profit margin above 25% indicates strong pricing '
         'power and cost discipline',
         _scaled_confidence(f['opm'], 25, 50)
      ))

   # Rule 6: PAT CAGR above 20% over 5 years.
   if f['pat_cagr_5yr'] is not None and f['pat_cagr_5yr'] > 20:
      results.append((
         'PRO-06',
         'Net profit compounding at above 20% over 5 years creates '
         'significant shareholder value',
         _scaled_confidence(f['pat_cagr_5yr'], 20, 40)
      ))

   # Rule 7: interest coverage above 10, or no debt at all.
   coverage = f['interest_coverage']
   if coverage is None or coverage > 10:
      confidence = (
         CONFIDENCE_CEILING if coverage is None
         else _scaled_confidence(coverage, 10, 40)
      )
      results.append((
         'PRO-07',
         'Very high interest coverage ratio reflects negligible '
         'financial stress from debt servicing',
         confidence
      ))

   # Rule 8: dividend yield above 2% with positive free cash flow.
   if (f['dividend_yield_pct'] is not None
         and f['dividend_yield_pct'] > 2
         and f['free_cash_flow'] is not None
         and f['free_cash_flow'] > 0):
      results.append((
         'PRO-08',
         'Consistent dividend yield above 2% backed by positive free '
         'cash flow',
         _scaled_confidence(f['dividend_yield_pct'], 2, 5)
      ))

   # Rule 9: EPS CAGR above 15% over 5 years.
   if f['eps_cagr_5yr'] is not None and f['eps_cagr_5yr'] > 15:
      results.append((
         'PRO-09',
         'Earnings per share growing above 15% CAGR indicates strong '
         'earnings quality and compounding',
         _scaled_confidence(f['eps_cagr_5yr'], 15, 35)
      ))

   # Rule 10: ROE improving for 3 consecutive years.
   if consecutive_direction(f['roe_series'], rising=True, periods=3):
      results.append((
         'PRO-10',
         'Return on equity improving for 3 consecutive years shows '
         'strengthening business quality',
         85.0
      ))

   # Rule 11: profits growing faster than revenue, operating leverage.
   if (f['revenue_cagr_5yr'] is not None
         and f['pat_cagr_5yr'] is not None
         and f['pat_cagr_5yr'] > f['revenue_cagr_5yr']):
      gap = f['pat_cagr_5yr'] - f['revenue_cagr_5yr']
      results.append((
         'PRO-11',
         'Revenue growing slower than profits shows improving operating '
         'leverage and scale benefits',
         _scaled_confidence(gap, 0, 15)
      ))

   # Rule 12: asset base growing while debt declines.
   assets_growing = consecutive_direction(
      f['assets_series'], rising=True, periods=2
   )
   debt_declining = consecutive_direction(
      f['borrowings_series'], rising=False, periods=2
   )
   if assets_growing and debt_declining:
      results.append((
         'PRO-12',
         'Growing asset base funded by internal accruals reflects '
         'self-sustaining growth',
         88.0
      ))

   return results


# Con rules
def _con_rules(f):
   results = []
   is_financial = f['broad_sector'] == 'Financials'

   # Rule 1: leverage above 2.0 for a non-financial company.
   if (not is_financial
         and f['debt_to_equity'] is not None
         and f['debt_to_equity'] > 2.0):
      results.append((
         'CON-01',
         f'Debt-to-equity ratio of {f["debt_to_equity"]:.2f} is elevated '
         'for a non-financial company and warrants monitoring',
         _scaled_confidence(f['debt_to_equity'], 2.0, 6.0)
      ))

   # Rule 2: free cash flow negative for 3 consecutive years.
   negative_fcf_streak = trailing_streak(
      f['fcf_series'], lambda value: value < 0
   )
   if negative_fcf_streak >= 3:
      results.append((
         'CON-02',
         'Free cash flow negative for 3 consecutive years raises concern '
         'about cash generation quality',
         _streak_confidence(negative_fcf_streak, 3, 7)
      ))

   # Rule 3: operating margin declining for 3 consecutive years.
   if consecutive_direction(f['opm_series'], rising=False, periods=3):
      results.append((
         'CON-03',
         'Operating margins declining for 3 consecutive years suggest '
         'pricing or cost pressure',
         85.0
      ))

   # Rule 4: a loss in the latest year.
   if f['net_profit'] is not None and f['net_profit'] < 0:
      results.append((
         'CON-04',
         'Company reported a net loss in the most recent financial year',
         CONFIDENCE_CEILING
      ))

   # Rule 5: revenue declining for 2 or more years.
   if consecutive_direction(f['sales_series'], rising=False, periods=2):
      results.append((
         'CON-05',
         'Revenue contraction over 2 consecutive years indicates demand '
         'weakness or market share loss',
         88.0
      ))

   # Rule 6: interest coverage below 1.5.
   if f['interest_coverage'] is not None and f['interest_coverage'] < 1.5:
      results.append((
         'CON-06',
         'Interest coverage ratio below 1.5x indicates the company is at '
         'risk of not meeting its debt obligations',
         _scaled_confidence(
            f['interest_coverage'], 1.5, 0.0, higher_is_stronger=False
         )
      ))

   # Rule 7: dividend payout above 100%.
   if f['dividend_payout_pct'] is not None and f['dividend_payout_pct'] > 100:
      results.append((
         'CON-07',
         'Dividend payout ratio above 100% means the company is paying '
         'dividends from reserves, which is unsustainable',
         _scaled_confidence(f['dividend_payout_pct'], 100, 200)
      ))

   # Rule 8: leverage rising for 3 consecutive years.
   if consecutive_direction(f['de_series'], rising=True, periods=3):
      results.append((
         'CON-08',
         'Rising debt-to-equity ratio over 3 years suggests increasing '
         'financial leverage risk',
         85.0
      ))

   # Rule 9: EPS declining for 3 consecutive years.
   if consecutive_direction(f['eps_series'], rising=False, periods=3):
      results.append((
         'CON-09',
         'Earnings per share declining for 3 consecutive years reflects '
         'deteriorating profitability',
         85.0
      ))

   # Rule 10: return on capital employed below 10%.
   if f['roce'] is not None and f['roce'] < 10:
      results.append((
         'CON-10',
         'Return on capital employed below 10% suggests the business is '
         'not generating sufficient returns on invested capital',
         _scaled_confidence(f['roce'], 10, 0, higher_is_stronger=False)
      ))

   # Rule 11: net debt above three times EBITDA.
   if (f['net_debt'] is not None
         and f['ebitda'] is not None
         and f['ebitda'] > 0
         and f['net_debt'] > 3 * f['ebitda']):
      multiple = f['net_debt'] / f['ebitda']
      results.append((
         'CON-11',
         f'Net debt at {multiple:.1f} times EBITDA is a high leverage '
         'ratio and limits financial flexibility',
         _scaled_confidence(multiple, 3, 8)
      ))

   # Rule 12: revenue CAGR below 5% over 5 years.
   if f['revenue_cagr_5yr'] is not None and f['revenue_cagr_5yr'] < 5:
      results.append((
         'CON-12',
         'Revenue growing at below 5% over 5 years lags inflation and '
         'suggests limited business momentum',
         _scaled_confidence(
            f['revenue_cagr_5yr'], 5, -5, higher_is_stronger=False
         )
      ))

   return results


RELATIVE_CONFIDENCE_FLOOR = 62.0
RELATIVE_CONFIDENCE_CEILING = 78.0

# Metric key -> (label, higher_is_better)
RELATIVE_METRICS = {
   'roe': ('return on equity', True),
   'roce': ('return on capital employed', True),
   'opm': ('operating margin', True),
   'npm': ('net profit margin', True),
   'revenue_cagr_5yr': ('5 year revenue growth', True),
   'debt_to_equity': ('debt to equity', False)
}


def _sector_percentiles(features):
   # company_id -> metric -> percentile rank within its sector.
   frame = pd.DataFrame([
      {
         'company_id': company_id,
         'broad_sector': company['broad_sector'] or 'Unclassified',
         **{
            metric: company[metric] for metric in RELATIVE_METRICS
         }
      }
      for company_id, company in features.items()
   ])

   percentiles = {}

   def rank_group(group):
      for metric, (_label, higher_is_better) in RELATIVE_METRICS.items():
         values = pd.to_numeric(group[metric], errors='coerce')
         ranks = values.rank(pct=True, na_option='keep') * 100

         if not higher_is_better:
            ranks = 100 - ranks

         for company_id, rank in zip(group['company_id'], ranks):
            if pd.isna(rank):
               continue
            percentiles.setdefault(company_id, {})[metric] = float(rank)

   rank_group(frame)

   for _sector, group in frame.groupby('broad_sector'):
      if len(group) < 3:
         continue

      rank_group(group)

   return percentiles


def _relative_pro(company_features, metric_ranks):
   if not metric_ranks:
      return None

   metric, rank = max(metric_ranks.items(), key=lambda item: item[1])
   label, _higher = RELATIVE_METRICS[metric]
   sector = company_features['broad_sector'] or 'the index'

   confidence = RELATIVE_CONFIDENCE_FLOOR + (rank / 100) * (
      RELATIVE_CONFIDENCE_CEILING - RELATIVE_CONFIDENCE_FLOOR
   )

   return (
      'PRO-13',
      f'Ranks in the {rank:.0f}th percentile of {sector} on {label}, '
      'its strongest position relative to sector peers',
      round(confidence, 1)
   )


def _relative_con(company_features, metric_ranks):
   if not metric_ranks:
      return None

   metric, rank = min(metric_ranks.items(), key=lambda item: item[1])
   label, _higher = RELATIVE_METRICS[metric]
   sector = company_features['broad_sector'] or 'the index'

   confidence = RELATIVE_CONFIDENCE_FLOOR + (1 - rank / 100) * (
      RELATIVE_CONFIDENCE_CEILING - RELATIVE_CONFIDENCE_FLOOR
   )

   return (
      'CON-13',
      f'No absolute red flag, but ranks in only the {rank:.0f}th '
      f'percentile of {sector} on {label}',
      round(confidence, 1)
   )


def generate_pros_and_cons(features):
   records = []
   percentiles = _sector_percentiles(features)

   for company_id, company_features in features.items():
      emitted = {TYPE_PRO: 0, TYPE_CON: 0}

      for entry_type, rules in (
         (TYPE_PRO, _pro_rules(company_features)),
         (TYPE_CON, _con_rules(company_features))
      ):
         for rule_id, text, confidence in rules:
            if confidence is None or confidence <= CONFIDENCE_FLOOR:
               continue

            emitted[entry_type] += 1
            records.append({
               'company_id': company_id,
               'type': entry_type,
               'rule_id': rule_id,
               'text': text,
               'confidence_pct': round(float(confidence), 1)
            })

      metric_ranks = percentiles.get(company_id, {})

      if emitted[TYPE_PRO] == 0:
         fallback = _relative_pro(company_features, metric_ranks)
         if fallback:
            records.append({
               'company_id': company_id,
               'type': TYPE_PRO,
               'rule_id': fallback[0],
               'text': fallback[1],
               'confidence_pct': fallback[2]
            })

      if emitted[TYPE_CON] == 0:
         fallback = _relative_con(company_features, metric_ranks)
         if fallback:
            records.append({
               'company_id': company_id,
               'type': TYPE_CON,
               'rule_id': fallback[0],
               'text': fallback[1],
               'confidence_pct': fallback[2]
            })

   return pd.DataFrame(
      records,
      columns=['company_id', 'type', 'rule_id', 'text', 'confidence_pct']
   ).sort_values(['company_id', 'type', 'confidence_pct'],
                 ascending=[True, True, False])


def coverage_report(generated_df, features):
   rows = []

   for company_id in features:
      company_rows = generated_df[generated_df['company_id'] == company_id]
      rows.append({
         'company_id': company_id,
         'pros': int((company_rows['type'] == TYPE_PRO).sum()),
         'cons': int((company_rows['type'] == TYPE_CON).sum())
      })

   return pd.DataFrame(rows)


def export_pros_and_cons(connection=None):
   history = load_history(connection)
   features = build_company_features(history)

   generated_df = generate_pros_and_cons(features)

   output_path = Path(OUTPUT_PATH)
   output_path.parent.mkdir(parents=True, exist_ok=True)
   generated_df.to_csv(output_path, index=False)

   coverage_df = coverage_report(generated_df, features)

   print(f'Wrote {output_path} ({len(generated_df)} statements)')
   print(f'  pros: {(generated_df["type"] == TYPE_PRO).sum()}')
   print(f'  cons: {(generated_df["type"] == TYPE_CON).sum()}')
   print(f'  companies covered: {generated_df["company_id"].nunique()}')
   print()

   missing_pros = coverage_df[coverage_df['pros'] == 0]
   missing_cons = coverage_df[coverage_df['cons'] == 0]

   print('EXIT CRITERION - at least 1 pro and 1 con per company')
   print(f'  companies with no pro : {len(missing_pros)}')
   print(f'  companies with no con : {len(missing_cons)}')

   if not missing_pros.empty:
      print(f'    {sorted(missing_pros["company_id"])}')
   if not missing_cons.empty:
      print(f'    {sorted(missing_cons["company_id"])}')

   return generated_df, coverage_df


def main():
   export_pros_and_cons()


if __name__ == '__main__':
   main()
