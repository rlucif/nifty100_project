'''Portfolio-level statistics endpoints for the N100 API.'''

from fastapi import APIRouter

from src.api.dependencies import frame_to_records, read_output_csv
from src.analytics.statistics import build_portfolio_stats, load_kpi_frame

router = APIRouter(tags=['portfolio'])


@router.get('/portfolio/stats')
def get_portfolio_stats():
   '''P10 through P90, mean and std for the 10 core KPIs.'''
   # Prefer the generated file so the API matches what was published. Fall back to computing it if the batch has not been run yet.
   stats = read_output_csv('portfolio_stats.csv')
   source = 'output/portfolio_stats.csv'

   if stats.empty:
      _path, stats = build_portfolio_stats(load_kpi_frame())
      source = 'computed on demand'

   return {
      'count': len(stats),
      'source': source,
      'stats': frame_to_records(stats)
   }


@router.get('/portfolio/clusters')
def get_clusters():
   '''Company archetype assignments from KMeans clustering.'''
   labels = read_output_csv('cluster_labels.csv')
   profiles = read_output_csv('cluster_profiles.csv')

   summary = []
   if not labels.empty:
      grouped = labels.groupby(['cluster_id', 'cluster_name']).agg(
         companies=('company_id', 'count'),
         mean_distance=('distance_from_centroid', 'mean')
      ).round(4).reset_index()
      summary = frame_to_records(grouped)

   return {
      'count': len(labels),
      'clusters': summary,
      'profiles': frame_to_records(profiles),
      'assignments': frame_to_records(labels)
   }


@router.get('/portfolio/outliers')
def get_outliers():
   '''Companies whose metrics sit more than 3 standard deviations from
   their sector mean.'''
   outliers = read_output_csv('outlier_report.csv')

   return {
      'count': len(outliers),
      'outliers': frame_to_records(outliers)
   }
