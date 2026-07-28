'''Peer group endpoints for the N100 API.'''

import pandas as pd
from fastapi import APIRouter, HTTPException
from src.api.dependencies import query

router = APIRouter(tags=['peers'])


@router.get('/peers')
def list_peer_groups():
   '''List every peer group with its member count and benchmark.'''
   groups = query(
      'SELECT peer_group_name, company_id, is_benchmark FROM peer_groups'
   )

   records = []
   for group_name, members in groups.groupby('peer_group_name'):
      benchmark_flag = pd.to_numeric(
         members['is_benchmark'], errors='coerce'
      )
      benchmark_rows = members[benchmark_flag == 1]

      records.append({
         'peer_group_name': group_name,
         'member_count': len(members),
         'benchmark_company': (
            benchmark_rows['company_id'].iloc[0]
            if not benchmark_rows.empty else None
         )
      })

   records.sort(key=lambda item: item['peer_group_name'])
   return {'count': len(records), 'peer_groups': records}


@router.get('/peers/{group_name}')
def get_peer_group(group_name: str):
   '''All companies in a peer group with a percentile rank per metric.'''
   available = query(
      'SELECT DISTINCT peer_group_name FROM peer_groups'
   )['peer_group_name'].tolist()

   matches = [
      name for name in available
      if name.lower() == group_name.strip().lower()
   ]

   if not matches:
      raise HTTPException(
         status_code=404,
         detail=(
            f'Unknown peer group {group_name}. '
            f'Available: {", ".join(sorted(available))}'
         )
      )

   resolved = matches[0]

   members = query(
      'SELECT company_id, is_benchmark FROM peer_groups '
      'WHERE peer_group_name = ?',
      (resolved,)
   )
   percentiles = query(
      'SELECT * FROM peer_percentiles WHERE peer_group_name = ?',
      (resolved,)
   )

   benchmark_flag = pd.to_numeric(members['is_benchmark'], errors='coerce')
   benchmark_rows = members[benchmark_flag == 1]
   benchmark_id = (
      benchmark_rows['company_id'].iloc[0]
      if not benchmark_rows.empty else None
   )

   companies = []
   for company_id in sorted(members['company_id']):
      company_rows = percentiles[percentiles['company_id'] == company_id]

      metrics = {
         row.metric: {
            'value': None if pd.isna(row.value) else round(row.value, 4),
            'percentile_rank': (
               None if pd.isna(row.percentile_rank)
               else round(row.percentile_rank, 2)
            )
         }
         for row in company_rows.itertuples()
      }

      companies.append({
         'company_id': company_id,
         'is_benchmark': company_id == benchmark_id,
         'has_rankings': bool(metrics),
         'metrics': metrics
      })

   return {
      'peer_group_name': resolved,
      'member_count': len(members),
      'benchmark_company': benchmark_id,
      'metrics_ranked': int(percentiles['metric'].nunique()),
      'companies': companies
   }
