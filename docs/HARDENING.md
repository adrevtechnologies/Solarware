# Production Hardening Baseline

Last updated: 2026-04-20

## Monitoring and Observability

- API request logs must include route, status_code, duration_ms, and cache_hit where applicable.
- Area mass scans log start/end with tile_count, result_count, and elapsed seconds.
- Search API logs include exact-address footprint match outcomes for auditability.
- Errors are logged with stack traces and request context IDs where available.

## Performance Targets

- Search endpoint p95 latency target: <= 2.5s for cached lookups.
- Search endpoint p95 latency target: <= 8.0s for uncached live lookups.
- Area mass scan p95 latency target: <= 45s for default tile/radius settings.
- Cache hit ratio target for repeat scans: >= 60% within 7 days.

## Reliability Controls

- Geocode results are cached to disk (7-day TTL).
- Static map image URLs are cached to disk (7-day TTL).
- Places responses are cached in-memory during process lifetime.
- Area mass result sets are cached to disk and reused for export.
- Exact-address mode does not return point-centered fallback records when no mapped roof footprint exists.

## Operational Checklist

- Validate env vars for frontend and backend key separation before deploy.
- Validate production build in CI prior to release promotion.
- Review logs for cache hit ratios and slow requests after each release.
- Verify at least one area scan and one exact-address scan in production smoke tests.
