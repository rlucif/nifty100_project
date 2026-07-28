'''
FastAPI server for the N100 Financial Intelligence Platform.

Serves the 16 endpoints listed below under the /api/v1 prefix.
   health       GET  /health
   companies    GET  /companies
                GET  /companies/{ticker}
                GET  /companies/{ticker}/pl
                GET  /companies/{ticker}/bs
                GET  /companies/{ticker}/cashflow
                GET  /companies/{ticker}/ratios
                GET  /companies/{ticker}/tearsheet
                GET  /companies/{ticker}/peers/compare
                GET  /companies/{ticker}/documents
   screener     GET  /screener
   sectors      GET  /sectors
                GET  /sectors/{sector}/companies
   peers        GET  /peers/{group_name}
   valuation    GET  /market-cap/{ticker}
   portfolio    GET  /portfolio/stats

Three convenience endpoints are also exposed (/screener/presets, /peers
and /portfolio/clusters, /portfolio/outliers) because the dashboard and
the acceptance checks need them.

Run with:
   uvicorn src.api.main:app --port 8000

Interactive documentation is then at http://localhost:8000/docs
'''

import json
import logging
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.dependencies import API_VERSION, DB_PATH
from src.api.routers import (
   companies,
   health,
   peers,
   portfolio,
   screener,
   sectors,
   valuation
)

API_PREFIX = '/api/v1'
OPENAPI_EXPORT_PATH = 'docs/openapi.json'

logging.basicConfig(
   level=logging.INFO,
   format='%(asctime)s %(levelname)s %(message)s'
)
logger = logging.getLogger('n100.api')

app = FastAPI(
   title='N100 Financial Intelligence Platform API',
   description=(
      'Fundamental analytics for the Nifty 100 constituents present in '
      'the supplied datasets. Valuation metrics are simulated data.'
   ),
   version=API_VERSION,
   docs_url='/docs',
   redoc_url='/redoc'
)

# Internal use only
app.add_middleware(
   CORSMiddleware,
   allow_origins=['*'],
   allow_credentials=False,
   allow_methods=['*'],
   allow_headers=['*']
)


@app.middleware('http')
async def log_requests(request: Request, call_next):
   '''Log the method, path and elapsed time of every request.'''
   started = time.perf_counter()
   response = await call_next(request)
   elapsed_ms = (time.perf_counter() - started) * 1000

   logger.info(
      '%s %s -> %s in %.1f ms',
      request.method,
      request.url.path,
      response.status_code,
      elapsed_ms
   )
   response.headers['X-Response-Time-ms'] = f'{elapsed_ms:.1f}'

   return response


for router in (
   health.router,
   companies.router,
   screener.router,
   sectors.router,
   peers.router,
   valuation.router,
   portfolio.router
):
   app.include_router(router, prefix=API_PREFIX)


@app.get('/', tags=['root'])
def read_root():
   '''Service banner with pointers to the documentation.'''
   return {
      'service': 'N100 Financial Intelligence Platform API',
      'version': API_VERSION,
      'database': str(DB_PATH.name),
      'docs': '/docs',
      'health': f'{API_PREFIX}/health'
   }


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
   '''Return a JSON body rather than an HTML page on an unhandled error.'''
   logger.exception('Unhandled error on %s', request.url.path)

   return JSONResponse(
      status_code=500,
      content={'detail': 'Internal server error'}
   )


def export_openapi(output_path=OPENAPI_EXPORT_PATH):
   '''Write the OpenAPI 3 specification to docs/openapi.json.'''
   destination = Path(output_path)
   destination.parent.mkdir(parents=True, exist_ok=True)

   specification = app.openapi()
   destination.write_text(
      json.dumps(specification, indent=2),
      encoding='utf-8'
   )

   return destination, specification


def route_summary():
   '''List the registered API routes, for verification and docs.

   Read from the OpenAPI schema rather than app.routes: this FastAPI
   version represents an included router as a single wrapper object with
   no path of its own, so walking app.routes finds nothing.
   '''
   routes = []

   for path, operations in app.openapi().get('paths', {}).items():
      if not path.startswith(API_PREFIX):
         continue

      for method in operations:
         if method.upper() in {'HEAD', 'OPTIONS'}:
            continue
         routes.append((method.upper(), path))

   return sorted(routes, key=lambda item: (item[1], item[0]))


def main():
   destination, specification = export_openapi()
   routes = route_summary()

   print(f'Wrote {destination}')
   print(f'OpenAPI version: {specification.get("openapi")}')
   print(f'Registered {len(routes)} endpoints under {API_PREFIX}:')
   for method, path in routes:
      print(f'  {method:6} {path}')


if __name__ == '__main__':
   main()
